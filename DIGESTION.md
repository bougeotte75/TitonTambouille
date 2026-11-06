# Consignes de digestion du journal

Ces consignes disent comment lire le journal pour remplir les onglets Recettes, Idées,
Carte et les goûts du foyer. Aujourd'hui c'est Claude qui les applique à la demande
(« digère TitonTambouille ») ; plus tard, le même texte servira de consigne à l'API.

## Déroulé

1. `python3 digerer.py a-digerer` affiche, en JSON, les entrées pas encore digérées et
   l'état actuel des onglets (identifiants des recettes, idées, lieux, membres du foyer).
2. On écrit les opérations dans un fichier JSON (format plus bas), de préférence dans
   `donnees/a_appliquer/`.
3. `python3 digerer.py appliquer <fichier> --essai` vérifie sans rien changer ;
   `python3 digerer.py appliquer <fichier>` applique, après une sauvegarde automatique.
4. `python3 digerer.py annuler` (ou le bouton Annuler du Journal) revient à l'état
   d'avant la dernière digestion.

## Règles de fond

1. **Ne rien inventer.** On ne remplit un champ que si le journal, une page liée dans
   le journal ou une personne citée dans le journal le dit. Dans le doute, on ne crée rien.
2. **Une recette vient d'une source.** Ingrédients, quantités et étapes sont recopiés
   tels quels depuis :
   - une page web liée dans une entrée (on lit la page et on recopie, sans reformuler) ;
   - ou une personne citée (« maman m'a dit 100 g de farine et 50 g de beurre »).
   Jamais de recette proposée ou complétée par l'IA. Pas de source : pas de cadre
   « La recette », seulement les notes.
3. **Les corrections de l'utilisatrice s'ajoutent à côté, sans effacer la source.**
   « Trop sucré, 80 g de sucre la prochaine fois » → correction de l'ingrédient
   sucre : ancien « 100 g », nouveau « 80 g », datée. L'interface barre l'ancien et
   affiche le nouveau en couleur.
4. **Une recette n'est créée que si un plat est cuisiné et présenté comme tel.**
   Si l'entrée dit « pas de quoi en faire une recette », on ne crée pas de recette.
   On garde quand même ce qu'elle apprend sur les goûts du foyer.
5. **Une idée** est quelque chose à essayer : un plat goûté ailleurs (resto, amis,
   boutique), lu ou vu, une variante envisagée. Elle indique sa source et sa date.
   Quand elle est réalisée, elle est marquée testée et reliée à sa recette.
6. **Saison** : on ne l'indique que si elle découle des produits (asperges : mai à juin)
   ou si le journal la donne. Les mois sont numérotés de 1 (janvier) à 12.
   Plat sans produit saisonnier : pas de saison.
7. **Régime, coût** : seulement si le journal le dit ou si c'est évident à la lecture
   de la recette source (aucune viande ni poisson → « Végétarien »). Coût : 1 à 3,
   uniquement si le journal en parle.
8. **Goûts du foyer** : les membres sont désignés par leur initiale (A, M, B).
   On note un avis de 1 à 3 (1 n'aime pas, 2 mitigé, 3 adore) quand le journal dit
   comment quelqu'un a réagi à un plat (avis sur la recette) ou à un aliment
   (goût général : « M adore l'emmental »). On recopie la nuance dans `note`.
9. **Lieux** : restaurants, cafés, plats à emporter, marchés, commerces cités.
   Types : `restaurant`, `a_emporter`, `cafe`, `marche`, `commerce`.
   On ajoute à chaque fois une mention datée qui dit ce qui s'y est passé ou ce qu'on
   y a trouvé. Pas d'adresse inventée : seulement ce que dit le journal.
10. **Contexte des notes** : avec qui et dans quel cadre (« en famille · dîner en
    semaine »), seulement si le journal le dit.
11. **Ton** : les notes reprennent les mots de l'utilisatrice, résumés au besoin, à la
    première personne comme dans le journal. Pas de jugement ajouté.

## Format des opérations

Un fichier JSON : `{"operations": [ … ]}`. Chaque opération a un `type` et une
`origine` : la clé de l'entrée du journal (fournie par `a-digerer`), ce qui permet
de retrouver d'où vient chaque information. Les identifiants (`id`) sont courts,
en minuscules, sans accents, avec des tirets : `dahl-lentilles-corail`.

| type | champs | effet |
|---|---|---|
| `recette` | `id`, `nom`, `categorie`, `saison` {`mois`, `texte`}, `regime`, `cout` | crée la recette ou met à jour les champs fournis |
| `recette_source` | `id`, `source` {`titre`, `url`, `date`}, `pour`, `ingredients` [texte], `etapes` [texte] | remplace le cadre « La recette » par le contenu d'une source |
| `recette_correction` | `id`, `ingredient` (mot pour le retrouver), `ancien`, `nouveau`, `date` | correction affichée barré + couleur |
| `recette_cuisinee` | `id`, `date` | compte une fois de plus, met à jour la dernière date |
| `recette_note` | `id`, `date`, `contexte`, `texte` | ajoute une note |
| `recette_photo` | `id`, `fichier`, `legende`, `date` | rattache une photo du journal |
| `avis` | `membre`, `sujet`, `niveau` (1–3), `date`, `note` | `sujet` = id de recette → avis sur la recette ; sinon goût pour un aliment |
| `idee` | `id`, `titre`, `source`, `date`, `note`, `type`, `saison` | crée l'idée ou met à jour les champs fournis |
| `idee_testee` | `id`, `recette` | marque l'idée testée |
| `lieu` | `id`, `nom`, `type`, `adresse` | crée le lieu ou met à jour les champs fournis |
| `lieu_mention` | `id`, `date`, `texte` | ajoute une mention datée au lieu |
| `ardoise` | `semaine`, `jours` | remplace la semaine proposée (préférences conservées) |

Exemple :

```json
{"operations": [
  {"type": "lieu", "origine": "2026-11-06 10:53 1a2b3c4d", "id": "sur-les-quais",
   "nom": "Sur les Quais", "type_lieu": "commerce", "adresse": "marché d'Aligre"},
  {"type": "lieu_mention", "origine": "2026-11-06 10:53 1a2b3c4d", "id": "sur-les-quais",
   "date": "2026-11-06", "texte": "confiture de myrtille de la maison Perrotte, très très bonne (pas donnée)"}
]}
```

Pour `lieu` et `idee`, le type du lieu ou de l'idée s'écrit `type_lieu` / `type_idee`
(le champ `type` est réservé au type d'opération).

## Ardoise de la semaine

À la demande (« propose ma semaine »), on lit `ardoise.json` (repas à prévoir,
contraintes), les recettes, les idées et les deux dernières semaines du journal, puis
on écrit une opération `ardoise`. Règles :

- un repas = un plat et un dessert ; une entrée seulement si « Entrées » est coché ;
- seulement les repas cochés (soirs, midis du week-end, midis en semaine) ;
- uniquement des recettes et idées de saison ;
- soir pressé → plat simple, restes ou préparé d'avance, jamais une idée à tester ;
- éviter ce que le foyer n'aime pas, varier, ne pas reprendre ce qui a été mangé ces derniers jours ;
- `raison` dit en quelques mots pourquoi ce choix.
