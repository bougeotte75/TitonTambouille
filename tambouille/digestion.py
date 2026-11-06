"""
Digestion du journal : applique aux onglets des opérations écrites selon DIGESTION.md.

- Chaque entrée du journal a une clé « AAAA-MM-JJ HH:MM empreinte » ; une entrée
  modifiée à la main change d'empreinte et redevient « à digérer ».
- Avant chaque application, les fichiers des onglets sont copiés dans
  donnees/sauvegardes/<horodatage>/ : « annuler » les remet en place.
- L'historique (donnees/historique.json) garde, pour chaque digestion, la liste
  des modifications en français, affichée dans le Journal.
"""
from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime
from pathlib import Path

from . import config, journal

RE_ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
RE_DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MEMBRES_PAR_DEFAUT = ("A", "M", "B")
TYPES_LIEU = {"restaurant", "a_emporter", "cafe", "marche", "commerce"}
VIDES = {
    "recettes": {"recettes": []},
    "idees": {"idees": []},
    "lieux": {"lieux": []},
    "foyer": {"membres": [{"initiale": m, "gouts": []} for m in MEMBRES_PAR_DEFAUT]},
    "ardoise": {"repas_a_prevoir": {"soirs": True, "midis_week_end": True, "midis_semaine": False, "entrees": False},
                "contraintes": "", "jours": []},
}


class ErreurDigestion(ValueError):
    """Opération refusée : rien n'est appliqué."""


# --------------------------------------------------------------------------- fichiers

def _f(nom: str) -> Path:
    return config.DOSSIER_DONNEES / f"{nom}.json"


def _f_etat() -> Path:
    return config.DOSSIER_DONNEES / "digestion.json"


def _f_historique() -> Path:
    return config.DOSSIER_DONNEES / "historique.json"


def _lire(chemin: Path, defaut):
    if not chemin.exists():
        return json.loads(json.dumps(defaut))       # copie
    return json.loads(chemin.read_text(encoding="utf-8"))


def _ecrire(chemin: Path, donnees) -> None:
    chemin.parent.mkdir(parents=True, exist_ok=True)
    tmp = chemin.with_suffix(".tmp")
    tmp.write_text(json.dumps(donnees, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.replace(chemin)


def lire_onglet(nom: str) -> dict:
    return _lire(_f(nom), VIDES[nom])


# --------------------------------------------------------------------------- entrées à digérer

def cle(entree: journal.Entree) -> str:
    contenu = entree.texte + "|" + "|".join(p.fichier + p.legende for p in entree.photos) \
        + "|" + "|".join(l.url + l.titre for l in entree.liens)
    return f"{entree.jour} {entree.heure} {hashlib.sha1(contenu.encode('utf-8')).hexdigest()[:8]}"


def cles_digerees() -> set[str]:
    return set(_lire(_f_etat(), {"digerees": []})["digerees"])


def a_digerer() -> list[tuple[str, journal.Entree]]:
    faites = cles_digerees()
    return [(cle(e), e) for e in journal.lire() if cle(e) not in faites]


def contexte() -> dict:
    """Ce dont a besoin celui qui écrit les opérations : entrées en attente et état des onglets."""
    recettes = lire_onglet("recettes")["recettes"]
    idees = lire_onglet("idees")["idees"]
    lieux = lire_onglet("lieux")["lieux"]
    foyer = lire_onglet("foyer")
    return {
        "entrees": [{"origine": k, "jour": e.jour, "heure": e.heure, "texte": e.texte,
                     "photos": [{"fichier": p.fichier, "legende": p.legende} for p in e.photos],
                     "liens": [{"url": l.url, "titre": l.titre} for l in e.liens]} for k, e in a_digerer()],
        "recettes": [{"id": r["id"], "nom": r["nom"],
                      "ingredients": [i.get("texte", "") for i in r.get("ingredients", [])]} for r in recettes],
        "idees": [{"id": i["id"], "titre": i["titre"], "statut": i.get("statut")} for i in idees],
        "lieux": [{"id": l["id"], "nom": l["nom"], "type": l.get("type")} for l in lieux],
        "membres": [m["initiale"] for m in foyer["membres"]],
    }


# --------------------------------------------------------------------------- application

def _exiger(cond: bool, message: str) -> None:
    if not cond:
        raise ErreurDigestion(message)


def _id(op: dict) -> str:
    v = op.get("id", "")
    _exiger(isinstance(v, str) and bool(RE_ID.match(v)), f"Identifiant invalide : {v!r}")
    return v


def _date(op: dict, champ: str = "date") -> str:
    v = op.get(champ, "")
    _exiger(isinstance(v, str) and bool(RE_DATE.match(v)), f"Date invalide : {v!r}")
    return v


def _saison(v) -> dict:
    _exiger(isinstance(v, dict) and isinstance(v.get("mois"), list)
            and all(isinstance(m, int) and 1 <= m <= 12 for m in v["mois"]) and isinstance(v.get("texte"), str),
            "Saison invalide : il faut {\"mois\": [1..12], \"texte\": \"…\"}")
    return {"mois": sorted(set(v["mois"]), key=lambda m: v["mois"].index(m)), "texte": v["texte"]}


def _trouver(liste: list, ident: str, quoi: str) -> dict:
    for x in liste:
        if x["id"] == ident:
            return x
    raise ErreurDigestion(f"{quoi} inconnue : {ident} (créez-la d'abord)")


def _date_courte(iso: str) -> str:
    mois = ["janv.", "févr.", "mars", "avr.", "mai", "juin", "juil.", "août", "sept.", "oct.", "nov.", "déc."]
    a, m, j = (int(x) for x in iso.split("-"))
    return f"{j} {mois[m - 1]}"


class _Etat:
    def __init__(self):
        self.d = {nom: lire_onglet(nom) for nom in VIDES}
        self.touches: set[str] = set()

    @property
    def recettes(self):
        return self.d["recettes"]["recettes"]

    def membre(self, initiale: str) -> dict:
        for m in self.d["foyer"]["membres"]:
            if m["initiale"] == initiale:
                return m
        raise ErreurDigestion(f"Membre du foyer inconnu : {initiale!r}")


def _appliquer_une(e: _Etat, op: dict) -> str:
    """Applique une opération et renvoie sa description en français."""
    t = op.get("type")

    if t == "recette":
        ident = _id(op)
        r = next((x for x in e.recettes if x["id"] == ident), None)
        nouvelle = r is None
        if nouvelle:
            _exiger(bool(op.get("nom")), "Nouvelle recette sans nom.")
            r = {"id": ident, "nom": op["nom"], "categorie": "Plats", "fois": 0, "derniere": None,
                 "cuisinee": [], "foyer": {}, "source": None, "ingredients": [], "etapes": [],
                 "photos": [], "notes": []}
            e.recettes.append(r)
        for champ in ("nom", "categorie", "regime", "pour"):
            if champ in op:
                r[champ] = str(op[champ])
        if "cout" in op:
            _exiger(op["cout"] in (1, 2, 3), "Coût : 1, 2 ou 3.")
            r["cout"] = op["cout"]
        if "saison" in op:
            r["saison"] = _saison(op["saison"])
        e.touches.add("recettes")
        return f"Recette créée : {r['nom']}" if nouvelle else f"Recette mise à jour : {r['nom']}"

    if t == "recette_source":
        r = _trouver(e.recettes, _id(op), "Recette")
        src = op.get("source") or {}
        _exiger(isinstance(src, dict) and bool(src.get("titre")), "Source sans titre.")
        _exiger(isinstance(op.get("ingredients"), list) and all(isinstance(i, str) for i in op["ingredients"]),
                "Ingrédients : liste de textes.")
        r["source"] = {"titre": str(src["titre"]), "url": str(src.get("url", "")), "date": src.get("date")}
        r["ingredients"] = [{"texte": i} for i in op["ingredients"]]
        r["etapes"] = [str(x) for x in op.get("etapes", [])]
        if "pour" in op:
            r["pour"] = str(op["pour"])
        e.touches.add("recettes")
        return f"{r['nom']} : recette recopiée d'après {r['source']['titre']}"

    if t == "recette_correction":
        r = _trouver(e.recettes, _id(op), "Recette")
        mot = str(op.get("ingredient", "")).lower()
        _exiger(bool(mot), "Correction sans ingrédient.")
        ing = next((i for i in r["ingredients"] if mot in i["texte"].lower()
                    or mot in (i.get("correction") or {}).get("nouveau", "").lower()), None)
        _exiger(ing is not None, f"{r['nom']} : aucun ingrédient ne contient « {mot} ».")
        ancien, nouveau, date = str(op.get("ancien", "")), str(op.get("nouveau", "")), _date(op)
        _exiger(bool(ancien and nouveau), "Correction : « ancien » et « nouveau » sont requis.")
        texte = ing["texte"]
        if "correction" not in ing and texte.startswith(ancien):
            texte = texte[len(ancien):].lstrip()        # « 100 g de sucre » → ancien « 100 g », reste « de sucre »
        elif "correction" in ing:
            ancien = ing["correction"]["ancien"]         # on garde la valeur de la source
        ing["texte"] = texte
        ing["correction"] = {"ancien": ancien, "nouveau": nouveau, "date": date}
        e.touches.add("recettes")
        return f"{r['nom']} : {ancien} → {nouveau} {texte}"

    if t == "recette_cuisinee":
        r = _trouver(e.recettes, _id(op), "Recette")
        date = _date(op)
        r.setdefault("cuisinee", [])
        if date not in r["cuisinee"]:
            r["cuisinee"].append(date)
        r["fois"] = max(r.get("fois", 0), len(r["cuisinee"]))
        r["derniere"] = max(d for d in r["cuisinee"] + ([r["derniere"]] if r.get("derniere") else []))
        e.touches.add("recettes")
        return f"{r['nom']} : cuisiné le {_date_courte(date)}"

    if t == "recette_note":
        r = _trouver(e.recettes, _id(op), "Recette")
        _exiger(bool(op.get("texte")), "Note vide.")
        r["notes"].append({"date": _date(op), "contexte": str(op.get("contexte", "")), "texte": str(op["texte"]),
                           "origine": op.get("origine")})
        r["notes"].sort(key=lambda n: n["date"], reverse=True)
        e.touches.add("recettes")
        return f"{r['nom']} : note du {_date_courte(op['date'])}"

    if t == "recette_photo":
        r = _trouver(e.recettes, _id(op), "Recette")
        fichier = str(op.get("fichier", ""))
        _exiger(bool(journal.RE_PHOTO.match(f"![x]({fichier})")) and ".." not in fichier
                and (config.DOSSIER_DONNEES / fichier).is_file(), f"Photo introuvable : {fichier}")
        r["photos"].append({"fichier": fichier, "legende": str(op.get("legende", "")), "date": _date(op)})
        e.touches.add("recettes")
        return f"{r['nom']} : photo ajoutée"

    if t == "avis":
        m = e.membre(str(op.get("membre", "")))
        niveau = op.get("niveau")
        _exiger(niveau in (1, 2, 3), "Avis : niveau 1, 2 ou 3.")
        sujet = str(op.get("sujet", "")).strip()
        _exiger(bool(sujet), "Avis sans sujet.")
        date = _date(op)
        r = next((x for x in e.recettes if x["id"] == sujet), None)
        if r is not None:
            r.setdefault("foyer", {})[m["initiale"]] = niveau
            e.touches.add("recettes")
            return f"{r['nom']} : avis de {m['initiale']} ({niveau}/3)"
        m.setdefault("gouts", [])
        m["gouts"] = [g for g in m["gouts"] if g["aliment"].lower() != sujet.lower()]
        m["gouts"].append({"aliment": sujet, "niveau": niveau, "date": date, "note": str(op.get("note", "")),
                           "origine": op.get("origine")})
        e.touches.add("foyer")
        return f"Goûts de {m['initiale']} : {sujet} ({niveau}/3)"

    if t == "idee":
        ident = _id(op)
        idees = e.d["idees"]["idees"]
        i = next((x for x in idees if x["id"] == ident), None)
        nouvelle = i is None
        if nouvelle:
            _exiger(bool(op.get("titre")), "Nouvelle idée sans titre.")
            i = {"id": ident, "titre": op["titre"], "source": "", "date": _date(op), "note": "",
                 "type": "", "statut": "a_tester", "origine": op.get("origine")}
            idees.append(i)
        for champ in ("titre", "source", "note"):
            if champ in op:
                i[champ] = str(op[champ])
        if "type_idee" in op:
            i["type"] = str(op["type_idee"])
        if "date" in op:
            i["date"] = _date(op)
        if "saison" in op:
            i["saison"] = _saison(op["saison"])
        e.touches.add("idees")
        return f"Idée ajoutée : {i['titre']}" if nouvelle else f"Idée mise à jour : {i['titre']}"

    if t == "idee_testee":
        i = _trouver(e.d["idees"]["idees"], _id(op), "Idée")
        i["statut"] = "testee"
        if op.get("recette"):
            _trouver(e.recettes, str(op["recette"]), "Recette")
            i["recette"] = op["recette"]
        e.touches.add("idees")
        return f"Idée testée : {i['titre']}"

    if t == "lieu":
        ident = _id(op)
        lieux = e.d["lieux"]["lieux"]
        l = next((x for x in lieux if x["id"] == ident), None)
        nouveau = l is None
        if nouveau:
            _exiger(bool(op.get("nom")), "Nouveau lieu sans nom.")
            l = {"id": ident, "nom": op["nom"], "type": "commerce", "adresse": "", "mentions": []}
            lieux.append(l)
        if "nom" in op:
            l["nom"] = str(op["nom"])
        if "type_lieu" in op:
            _exiger(op["type_lieu"] in TYPES_LIEU, f"Type de lieu : {', '.join(sorted(TYPES_LIEU))}")
            l["type"] = op["type_lieu"]
        if "adresse" in op:
            l["adresse"] = str(op["adresse"])
        e.touches.add("lieux")
        return f"Lieu ajouté : {l['nom']}" if nouveau else f"Lieu mis à jour : {l['nom']}"

    if t == "lieu_mention":
        l = _trouver(e.d["lieux"]["lieux"], _id(op), "Lieu")
        _exiger(bool(op.get("texte")), "Mention vide.")
        l.setdefault("mentions", []).append({"date": _date(op), "texte": str(op["texte"]), "origine": op.get("origine")})
        l["mentions"].sort(key=lambda x: x["date"], reverse=True)
        e.touches.add("lieux")
        return f"{l['nom']} : {op['texte']}"

    if t == "ardoise":
        jours = op.get("jours")
        _exiger(isinstance(jours, list) and all(isinstance(j, dict) and j.get("jour") and isinstance(j.get("repas"), list)
                                                for j in jours), "Ardoise : liste de jours avec leurs repas.")
        for j in jours:
            for r in j["repas"]:
                _exiger(bool(r.get("plat")), f"Ardoise : repas sans plat ({j['jour']}).")
        e.d["ardoise"]["jours"] = jours
        e.d["ardoise"]["semaine"] = op.get("semaine")
        e.touches.add("ardoise")
        return "Ardoise : nouvelle semaine proposée"

    raise ErreurDigestion(f"Type d'opération inconnu : {t!r}")


def appliquer(operations: list[dict], essai: bool = False, maintenant: datetime | None = None) -> list[str]:
    """Applique toutes les opérations, ou aucune si l'une est refusée. Renvoie les descriptions."""
    _exiger(isinstance(operations, list) and bool(operations), "Aucune opération.")
    e = _Etat()
    resumes = []
    for n, op in enumerate(operations, 1):
        _exiger(isinstance(op, dict), f"Opération {n} : objet attendu.")
        try:
            resumes.append(_appliquer_une(e, op))
        except ErreurDigestion as err:
            raise ErreurDigestion(f"Opération {n} ({op.get('type')}) : {err}") from None
    if essai:
        return resumes

    # Sauvegarde de l'état d'avant, puis écriture.
    maintenant = maintenant or datetime.now()
    horodatage = maintenant.strftime("%Y-%m-%d-%H%M%S")
    dossier = config.DOSSIER_DONNEES / "sauvegardes" / horodatage
    n = 1
    while dossier.exists():
        n += 1
        dossier = config.DOSSIER_DONNEES / "sauvegardes" / f"{horodatage}-{n}"
    horodatage = dossier.name
    dossier.mkdir(parents=True)
    existaient = []
    for nom in VIDES:
        if _f(nom).exists():
            shutil.copy2(_f(nom), dossier / f"{nom}.json")
            existaient.append(nom)
    if _f_etat().exists():
        shutil.copy2(_f_etat(), dossier / "digestion.json")

    for nom in e.touches:
        _ecrire(_f(nom), e.d[nom])

    origines = sorted({op["origine"] for op in operations if op.get("origine")})
    etat = _lire(_f_etat(), {"digerees": []})
    etat["digerees"] = sorted(set(etat["digerees"]) | set(origines))
    _ecrire(_f_etat(), etat)

    historique = _lire(_f_historique(), {"digestions": []})
    historique["digestions"].insert(0, {
        "date": maintenant.isoformat(timespec="seconds"), "sauvegarde": horodatage,
        "fichiers_existants": existaient, "fichiers_modifies": sorted(e.touches),
        "entrees": origines, "modifications": resumes, "annulee": False})
    _ecrire(_f_historique(), historique)
    return resumes


def marquer_digerees(origines: list[str]) -> None:
    """Pour une entrée qui ne contient rien à ranger : on la marque digérée sans opération."""
    etat = _lire(_f_etat(), {"digerees": []})
    etat["digerees"] = sorted(set(etat["digerees"]) | set(origines))
    _ecrire(_f_etat(), etat)


def historique() -> list[dict]:
    return _lire(_f_historique(), {"digestions": []})["digestions"]


def annuler_derniere() -> dict:
    """Remet les onglets dans l'état d'avant la dernière digestion non annulée."""
    h = _lire(_f_historique(), {"digestions": []})
    derniere = next((d for d in h["digestions"] if not d["annulee"]), None)
    _exiger(derniere is not None, "Aucune digestion à annuler.")
    dossier = config.DOSSIER_DONNEES / "sauvegardes" / derniere["sauvegarde"]
    _exiger(dossier.is_dir(), "Sauvegarde introuvable.")
    for nom in derniere["fichiers_modifies"]:
        if nom in derniere["fichiers_existants"]:
            shutil.copy2(dossier / f"{nom}.json", _f(nom))
        else:
            _f(nom).unlink(missing_ok=True)
    if (dossier / "digestion.json").exists():
        shutil.copy2(dossier / "digestion.json", _f_etat())
    else:
        _f_etat().unlink(missing_ok=True)
    derniere["annulee"] = True
    _ecrire(_f_historique(), h)
    return derniere


def enregistrer_preferences_ardoise(repas_a_prevoir: dict, contraintes: str) -> dict:
    """Enregistre les choix « Repas à prévoir » et « Cette semaine » de l'Ardoise."""
    cles = ("soirs", "midis_week_end", "midis_semaine", "entrees")
    _exiger(isinstance(repas_a_prevoir, dict), "Préférences illisibles.")
    a = lire_onglet("ardoise")
    a["repas_a_prevoir"] = {k: bool(repas_a_prevoir.get(k, a["repas_a_prevoir"].get(k, False))) for k in cles}
    a["contraintes"] = str(contraintes)[:500]
    _ecrire(_f("ardoise"), a)
    return a
