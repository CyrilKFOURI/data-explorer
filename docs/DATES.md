# Dates et parties de date

Une colonne de type **date / date-heure** n'est pas une variable comme les autres : c'est une **hiérarchie**. À partir d'`order_date`, l'app sait produire l'année, le trimestre, le mois, la semaine, le jour de la semaine, le jour du mois, l'heure… et chacune de ces **parties** répond à une question différente :

| Question | Partie utilisée | Exemple de visuel |
|---|---|---|
| Comment ça évolue ? | la date elle-même, regroupée par période (jour, semaine, mois…) | Courbe / barres dans le temps |
| Y a-t-il une saisonnalité annuelle ? | Mois de l'année (Jan…Déc) | Barres sur 12 mois, toutes années confondues |
| Un effet jour de semaine ? | Jour de la semaine (Lun…Dim) | Barres sur 7 jours |
| Un effet heure ? | Heure (0–23), seulement si la colonne a une heure | Barres sur 24 heures |
| Comparer des années ? | Année | Couleur / facette par année |

## Principe : des colonnes virtuelles

Chaque colonne date expose ses parties comme des **colonnes virtuelles**, nommées `order_date › Month`. Elles ne sont pas stockées : elles sont calculées à la lecture (SQL DuckDB), à partir de la valeur typée de la colonne. Elles sont donc toujours cohérentes avec le parseur choisi.

Partout où l'utilisateur choisit une colonne, les parties d'une date sont proposées juste sous elle :
- **Vue d'ensemble (003)** : la carte d'une date bascule entre *Timeline*, *Month*, *Day of week* et *Hour*.
- **Fiche variable (004)** : onglets de saisonnalité et trous dans la série.
- **Filtres (005)** : « `order_date` › Day of week ∈ {Sat, Sun} », « 12 derniers mois ».
- **Comparer (006)** : X, couleur ou facette = une partie de date (ex. montant par jour de semaine).
- **Corrélations (007)** : les parties cycliques peuvent être testées comme catégories.
- **Modules futurs** : séries temporelles (fréquence, saisonnalité), KPI (grain temporel).

## Parties disponibles

| Partie | Valeurs | Nature | Disponible si |
|---|---|---|---|
| `year` | 2019, 2020… | ordonnée | toujours |
| `quarter` | Q1…Q4 | cyclique, ordonnée | toujours |
| `month` | Jan…Dec | cyclique, ordonnée | toujours |
| `year_month` | 2024-03… | période | toujours |
| `week` | semaine ISO 1…53 | cyclique | toujours |
| `day_of_week` | Mon…Sun (semaine commençant le lundi) | cyclique, ordonnée | toujours |
| `day_of_month` | 1…31 | cyclique | toujours |
| `hour` | 0…23 | cyclique | la colonne contient une heure non nulle |

Les parties ordonnées gardent leur ordre naturel dans les visuels (jamais triées par fréquence).

## Granularité détectée

Pour chaque colonne date, la détection mesure :
- **avec ou sans heure** (des heures non nulles existent-elles ?) ;
- **la plage** (min → max) ;
- **le pas typique** entre deux dates distinctes consécutives (quotidien, hebdomadaire, mensuel, annuel, irrégulier).

Ces informations s'affichent sur la page Columns et servent à choisir le pas par défaut de la timeline.

## Pas automatique de la timeline

Le pas est choisi pour garder un nombre de points lisible (≤ ~120 barres ou points) : jour → semaine → mois → trimestre → année. L'utilisateur peut le changer.

## Rôles Year / Month / Day of week

Ces rôles s'appliquent aux colonnes qui **ne contiennent que** cette partie (une colonne `mois` à valeurs 1–12, une colonne `annee`). Une colonne `annee` (1800–2100) devient une date (rôle année) ; ses parties se limitent alors à `year`.
