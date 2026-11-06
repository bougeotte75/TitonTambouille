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
  les onglets, remplis par la digestion du journal. Avant la première digestion,
  les onglets affichent les données d'exemple de `exemples/` ;
- `donnees/digestion.json`, `historique.json`, `sauvegardes/` : suivi de la digestion.

Pense à sauvegarder `donnees/` (Time Machine, copie sur un disque…).

### Format du journal

```
## 2026-11-05

### 13:10
Déjeuner au libanais : moutabal très fumé…

![le moutabal](photos/2026-11-05-131002-1.jpg)
[Moutabal maison, la recette](https://exemple.fr/moutabal)
```

## Digestion

Les onglets se remplissent en « digérant » le journal, selon les consignes de
[`DIGESTION.md`](DIGESTION.md) : rien n'est inventé, les recettes viennent d'une source
(page liée ou personne citée), tes corrections s'affichent à côté de la source.

Pour l'instant, c'est Claude qui digère, à la demande (« digère TitonTambouille »),
avec `digerer.py`. Chaque digestion est sauvegardée et peut être annulée depuis le Journal.

## État

- **v0.1** : Journal complet (entrées, photos avec légende, liens). Recettes, Idées,
  Ardoise et Carte s'affichent en lecture seule, sur des données d'exemple.
- **v0.2** : digestion (consignes, `digerer.py`, sauvegarde et annulation), goûts du foyer,
  préférences de l'Ardoise enregistrées, liens nettoyés des paramètres publicitaires.
- À venir : la carte (OpenStreetMap), puis la digestion automatique par l'API.

## Tests

```bash
python3 -m unittest discover -s tests -t .
```

La police Courier Prime est embarquée dans `interface/polices/` (licence SIL Open Font, voir `OFL.txt`).
