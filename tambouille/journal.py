"""
Lecture et écriture du journal (donnees/journal.md).

Le journal est un fichier texte lisible tel quel, dans l'ordre chronologique :

    ## 2026-11-05

    ### 13:10
    Déjeuner au libanais : moutabal très fumé…

    ![le moutabal](photos/2026-11-05-131002-1.jpg)
    [Moutabal maison, la recette](https://exemple.fr/moutabal)

- « ## AAAA-MM-JJ » ouvre une journée, « ### HH:MM » ouvre une entrée ;
- une ligne « ![légende](photos/…) » est une photo, « [titre](https://…) » est un lien ;
- tout le reste est le texte de l'entrée.

Une ligne de texte qui ressemblerait à l'une de ces balises est précédée d'une
barre oblique inverse à l'écriture, retirée à la lecture : le texte reste intact.
"""
from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from . import config

RE_JOUR = re.compile(r"^## (\d{4}-\d{2}-\d{2})\s*$")
RE_HEURE = re.compile(r"^### (\d{2}:\d{2})\s*$")
RE_PHOTO = re.compile(r"^!\[(.*)\]\((photos/[^)\s]+)\)\s*$")
RE_LIEN = re.compile(r"^\[(.*)\]\((https?://[^)\s]+)\)\s*$")


@dataclass
class Photo:
    fichier: str            # chemin relatif : photos/xxx.jpg
    legende: str = ""


@dataclass
class Lien:
    url: str
    titre: str = ""


@dataclass
class Entree:
    jour: str               # AAAA-MM-JJ
    heure: str              # HH:MM
    texte: str = ""
    photos: list[Photo] = field(default_factory=list)
    liens: list[Lien] = field(default_factory=list)

    def en_dict(self, numero: int) -> dict:
        return {
            "id": f"{self.jour}-{numero}",
            "jour": self.jour,
            "heure": self.heure,
            "texte": self.texte,
            "photos": [{"fichier": p.fichier, "legende": p.legende} for p in self.photos],
            "liens": [{"url": l.url, "titre": l.titre} for l in self.liens],
        }


class ErreurEntree(ValueError):
    """Entrée refusée (vide, lien ou photo invalide)."""


# --------------------------------------------------------------------------- lecture

def _est_balise(ligne: str) -> bool:
    return bool(RE_JOUR.match(ligne) or RE_HEURE.match(ligne)
                or RE_PHOTO.match(ligne) or RE_LIEN.match(ligne))


def analyser(contenu: str) -> list[Entree]:
    """Transforme le texte du journal en liste d'entrées (ordre du fichier)."""
    entrees: list[Entree] = []
    jour: str | None = None
    courante: Entree | None = None
    lignes_texte: list[str] = []

    def clore() -> None:
        nonlocal courante, lignes_texte
        if courante is not None:
            courante.texte = "\n".join(lignes_texte).strip("\n")
            entrees.append(courante)
        courante, lignes_texte = None, []

    for brute in contenu.splitlines():
        ligne = brute.rstrip("\r")
        if m := RE_JOUR.match(ligne):
            clore()
            jour = m.group(1)
        elif (m := RE_HEURE.match(ligne)) and jour:
            clore()
            courante = Entree(jour=jour, heure=m.group(1))
        elif courante is None:
            continue                                  # texte hors entrée : ignoré
        elif m := RE_PHOTO.match(ligne):
            courante.photos.append(Photo(fichier=m.group(2), legende=m.group(1)))
        elif m := RE_LIEN.match(ligne):
            courante.liens.append(Lien(url=m.group(2), titre=m.group(1)))
        else:
            if ligne.startswith("\\"):
                ligne = ligne[1:]                     # échappement retiré
            lignes_texte.append(ligne)
    clore()
    return entrees


def lire(fichier: Path | None = None) -> list[Entree]:
    fichier = fichier or config.F_JOURNAL
    if not fichier.exists():
        return []
    return analyser(fichier.read_text(encoding="utf-8"))


# --------------------------------------------------------------------------- écriture

def _nettoyer_ligne(texte: str) -> str:
    """Une légende ou un titre tient sur une ligne, sans crochets."""
    return " ".join(texte.replace("[", "(").replace("]", ")").split())


def formater_entree(entree: Entree) -> str:
    lignes = [f"### {entree.heure}"]
    for ligne in entree.texte.strip("\n").splitlines():
        if _est_balise(ligne) or ligne.startswith("\\"):
            ligne = "\\" + ligne
        lignes.append(ligne)
    if entree.photos or entree.liens:
        lignes.append("")
    for p in entree.photos:
        lignes.append(f"![{_nettoyer_ligne(p.legende)}]({p.fichier})")
    for l in entree.liens:
        lignes.append(f"[{_nettoyer_ligne(l.titre)}]({l.url})")
    return "\n".join(lignes) + "\n"


def _valider(texte: str, photos: list[Photo], liens: list[Lien]) -> None:
    if not texte.strip() and not photos and not liens:
        raise ErreurEntree("L'entrée est vide.")
    for p in photos:
        if not RE_PHOTO.match(f"![x]({p.fichier})") or ".." in p.fichier:
            raise ErreurEntree(f"Photo invalide : {p.fichier}")
        if not (config.DOSSIER_DONNEES / p.fichier).is_file():
            raise ErreurEntree(f"Photo introuvable : {p.fichier}")
    for l in liens:
        if not RE_LIEN.match(f"[x]({l.url})"):
            raise ErreurEntree(f"Lien invalide (il doit commencer par http:// ou https://) : {l.url}")


def ajouter(texte: str, photos: list[Photo] | None = None, liens: list[Lien] | None = None,
            maintenant: datetime | None = None, fichier: Path | None = None) -> Entree:
    """Ajoute une entrée datée de maintenant à la fin du journal et la renvoie."""
    photos, liens = photos or [], liens or []
    _valider(texte, photos, liens)
    maintenant = maintenant or datetime.now()
    fichier = fichier or config.F_JOURNAL
    entree = Entree(jour=maintenant.strftime("%Y-%m-%d"), heure=maintenant.strftime("%H:%M"),
                    texte=texte.strip("\n"), photos=photos, liens=liens)

    contenu = fichier.read_text(encoding="utf-8") if fichier.exists() else ""
    jours = re.findall(r"^## (\d{4}-\d{2}-\d{2})[ \t]*$", contenu, re.M)
    morceaux = [contenu.rstrip("\n")] if contenu.strip() else []
    if not jours or jours[-1] != entree.jour:
        morceaux.append(f"## {entree.jour}")
    morceaux.append(formater_entree(entree).rstrip("\n"))
    _ecrire_atomique(fichier, "\n\n".join(morceaux) + "\n")
    return entree


def _ecrire_atomique(fichier: Path, contenu: str) -> None:
    """Écrit dans un fichier temporaire puis le substitue : jamais de journal à moitié écrit."""
    fichier.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=fichier.parent, prefix=".journal-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(contenu)
        os.replace(tmp, fichier)
    except BaseException:
        Path(tmp).unlink(missing_ok=True)
        raise
