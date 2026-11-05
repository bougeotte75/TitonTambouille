# Visuels de TitonTambouille : spécifications

Ce dossier accueille les visuels dessinés à la main pour l'application : symboles des onglets, boutons, icône d'application.
Tant qu'un fichier manque, l'application garde le symbole provisoire dessiné en code.

## Charte actuelle (pour référence)

- Fond : blanc `#FFFFFF`
- Texte : noir doux `#1A1A1A`, texte secondaire gris `#595959`
- Couleur d'accent : `#9999FF` (dates, onglet actif, soulignement des liens)
- Police : Courier Prime (Google Fonts), regular et bold

## Liste des visuels à fournir

| Fichier attendu          | Rôle                              | Symbole provisoire       |
|--------------------------|-----------------------------------|--------------------------|
| `onglet-journal.svg`     | Onglet Journal                    | stylo                    |
| `onglet-recettes.svg`    | Onglet Recettes                   | livre                    |
| `onglet-idees.svg`       | Onglet Idées                      | ampoule                  |
| `onglet-ardoise.svg`     | Onglet Ardoise (menus de la semaine) | ardoise avec lignes   |
| `onglet-carte.svg`       | Onglet Carte                      | repère de lieu           |
| `bouton-photo.svg`       | Ajouter une photo à une entrée    | appareil photo           |
| `bouton-lien.svg`        | Ajouter un lien à une entrée      | maillon de chaîne        |
| `icone-app.png`          | Icône sur l'écran d'accueil iPhone | (aucune pour l'instant) |

Le nom de fichier compte : c'est lui qui permet à l'application de trouver le visuel.
Le PNG est accepté à la place du SVG pour les symboles (`onglet-journal.png`, etc.).

## Formats

Sur écran, la résolution en ppp (dpi) n'a pas d'importance : seules les dimensions en pixels comptent.

- **Idéal : SVG (vectoriel).** Net à toutes les tailles et recolorable par le code (gris quand l'onglet est inactif, noir quand il est actif). Export depuis Illustrator, Inkscape, Affinity ou Figma.
- **Possible : PNG.** Carré, **96 × 96 px minimum**, fond transparent. Les tailles d'affichage (24, 48 et 72 px) sont produites à partir de ce fichier.
- **Dessin papier :** scan à **300 ppp minimum**, noir sur blanc bien contrasté. Il sera vectorisé en SVG automatiquement, avec une légère retouche du trait.

## Règles de dessin (pour que les symboles aillent ensemble)

1. **Même plan de travail carré pour tous** (par exemple 24 × 24 ou 96 × 96).
2. **Marge vide d'environ 8 %** sur chaque bord (2 px sur 24, 8 px sur 96) : le dessin ne touche pas les bords.
3. **Une seule couleur, noir**, sans dégradé ni ombre : la couleur est appliquée par le code.
4. **Même épaisseur de trait partout** : environ 6 à 8 % de la largeur du carré (1,5 à 2 px sur 24, 6 à 8 px sur 96). Un trait trop fin disparaît sur iPhone.
5. **Poids visuel comparable** : soit tout en trait, soit tout en plein. Un symbole plein au milieu de symboles en trait ressortira trop.
6. **Formes simples** : affichés à 24 px, les détails de moins d'un pixel ne se voient plus.

## Tailles d'affichage dans l'application

- Onglets, barre du bas sur iPhone : 24 × 24 px, avec un libellé de 11 px dessous
- Boutons photo et lien : 20 × 20 px, dans un bouton de 44 × 44 px
- Petits symboles de lien dans les entrées : 16 × 16 px

## Icône d'application (écran d'accueil iPhone)

- **PNG de 180 × 180 px**, carré.
- **Fond coloré plein, pas de transparence** : iOS remplit la transparence en noir.
- Pas besoin d'arrondir les coins : iOS les arrondit tout seul. Gardez le dessin important à l'écart des coins (environ 10 % de marge).
