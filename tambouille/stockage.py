"""
Photos et données des onglets.

- Les photos envoyées depuis le journal sont rangées dans donnees/photos/,
  nommées par date et heure d'envoi.
- Chaque onglet (recettes, idées, ardoise, lieux, foyer) lit son fichier JSON
  dans donnees/ ; tant qu'il n'existe pas, on affiche celui de exemples/.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from . import config


class ErreurPhoto(ValueError):
    """Photo refusée (format ou taille)."""


def enregistrer_photo(nom_origine: str, contenu: bytes, maintenant: datetime | None = None) -> str:
    """Range une photo et renvoie son chemin relatif (photos/xxx.jpg)."""
    ext = Path(nom_origine).suffix.lower()
    if ext not in config.EXTENSIONS_PHOTO:
        raise ErreurPhoto(f"Format non pris en charge : {ext or 'aucune extension'}")
    if not contenu:
        raise ErreurPhoto("Le fichier est vide.")
    if len(contenu) > config.TAILLE_MAX_PHOTO:
        raise ErreurPhoto("La photo dépasse 25 Mo.")
    if ext == ".jpeg":
        ext = ".jpg"
    maintenant = maintenant or datetime.now()
    config.DOSSIER_PHOTOS.mkdir(parents=True, exist_ok=True)
    base = maintenant.strftime("%Y-%m-%d-%H%M%S")
    n = 1
    while (cible := config.DOSSIER_PHOTOS / f"{base}-{n}{ext}").exists():
        n += 1
    cible.write_bytes(contenu)
    return f"photos/{cible.name}"


def chemin_photo(nom: str) -> Path | None:
    """Chemin sur disque d'une photo demandée par son nom, ou None si invalide."""
    if not nom or "/" in nom or "\\" in nom or nom.startswith("."):
        return None
    chemin = (config.DOSSIER_PHOTOS / nom).resolve()
    if chemin.parent != config.DOSSIER_PHOTOS.resolve() or not chemin.is_file():
        return None
    return chemin


def lire_onglets() -> dict:
    """Renvoie les données de tous les onglets, en signalant celles qui sont des exemples."""
    donnees: dict = {"exemples": []}
    for nom in config.ONGLETS:
        propre = config.DOSSIER_DONNEES / f"{nom}.json"
        source = propre if propre.exists() else config.DOSSIER_EXEMPLES / f"{nom}.json"
        if source != propre:
            donnees["exemples"].append(nom)
        try:
            donnees[nom] = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            donnees[nom] = None
    return donnees
