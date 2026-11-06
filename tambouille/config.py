"""
Paramètres généraux de TitonTambouille.

Tout ce qu'on peut vouloir ajuster sans toucher à la logique :
emplacements, adresse du serveur, limites.
"""
from __future__ import annotations

from pathlib import Path

VERSION = "0.2"

# --------------------------------------------------------------------------- emplacements

RACINE = Path(__file__).resolve().parent.parent      # dossier du projet
DOSSIER_INTERFACE = RACINE / "interface"              # pages web (HTML, CSS, JS)
DOSSIER_EXEMPLES = RACINE / "exemples"                # données d'exemple (versionnées)

# Les chemins des données sont fixés par utiliser_dossier(),
# ce qui permet aux tests de travailler dans un dossier temporaire.
DOSSIER_DONNEES: Path
F_JOURNAL: Path
DOSSIER_PHOTOS: Path


def utiliser_dossier(dossier: Path) -> None:
    """Définit le dossier où sont lus et écrits le journal et les photos."""
    global DOSSIER_DONNEES, F_JOURNAL, DOSSIER_PHOTOS
    DOSSIER_DONNEES = Path(dossier)
    F_JOURNAL = DOSSIER_DONNEES / "journal.md"
    DOSSIER_PHOTOS = DOSSIER_DONNEES / "photos"


utiliser_dossier(RACINE / "donnees")   # données personnelles, exclues de Git

# --------------------------------------------------------------------------- serveur

HOTE = "127.0.0.1"        # uniquement accessible depuis ce Mac
PORT = 8742               # si occupé, le serveur prend un port libre

# --------------------------------------------------------------------------- limites

TAILLE_MAX_PHOTO = 25 * 1024 * 1024        # 25 Mo par photo
TAILLE_MAX_REQUETE = 1 * 1024 * 1024       # 1 Mo pour une entrée (texte + liens)
EXTENSIONS_PHOTO = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".heic"}

# Onglets alimentés par la digestion du journal (un fichier JSON chacun).
ONGLETS = ("recettes", "idees", "ardoise", "lieux", "foyer")
