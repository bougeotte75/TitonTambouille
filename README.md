# TitonTambouille

Journal culinaire : quelques lignes par jour, d'où se remplissent un livre de recettes,
un carnet d'idées, une ardoise de menus pour la semaine et une carte des lieux.

## Lancer

Double-clic sur `lancer.command` (la première fois : clic droit → Ouvrir),
ou dans le Terminal :

```bash
python3 app.py
```

L'interface s'ouvre dans le navigateur. Aucune dépendance à installer : Python 3 suffit.
Le serveur n'écoute que sur ce Mac (127.0.0.1).

## Où sont les données

Tout est dans `donnees/`, **exclu de Git** : rien de ton journal ne part sur GitHub.

- `donnees/journal.md` : le journal, lisible et modifiable à la main ;
- `donnees/photos/` : les photos jointes aux entrées ;
- `donnees/recettes.json`, `idees.json`, `ardoise.json`, `lieux.json`, `foyer.json` :
  les onglets, remplis par la digestion du journal. Tant qu'un fichier manque,
  l'onglet affiche les données d'exemple de `exemples/`.

Pense à sauvegarder `donnees/` (Time Machine, copie sur un disque…).

### Format du journal

```
## 2026-11-05

### 13:10
Déjeuner au libanais : moutabal très fumé…

![le moutabal](photos/2026-11-05-131002-1.jpg)
[Moutabal maison, la recette](https://exemple.fr/moutabal)
```

## État

- **v0.1** : Journal complet (entrées, photos avec légende, liens). Recettes, Idées,
  Ardoise et Carte s'affichent en lecture seule, sur des données d'exemple.
- À venir : la digestion du journal par l'IA, l'ardoise interactive, la carte (OpenStreetMap).

## Tests

```bash
python3 -m unittest discover -s tests -t .
```

La police Courier Prime est embarquée dans `interface/polices/` (licence SIL Open Font, voir `OFL.txt`).
