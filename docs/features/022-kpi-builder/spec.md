# 022 — Module Builder KPI

## Objectif

Obtenir **en un clic** un indicateur métier lisible : « chiffre d'affaires par mois », « clients distincts par semaine et par pays », « panier moyen par trimestre ». L'app choisit d'elle-même la mesure, le grain, le graphique et la disposition du tableau. On peut ensuite **personnaliser** chaque choix, sans jamais devoir tout construire comme dans Excel.

Là où Séries temporelles analyse une courbe en profondeur, le Builder KPI est l'outil rapide du tableau de bord.

Origine : [modules-futurs/kpi-builder.md](../../modules-futurs/kpi-builder.md). Page : [12-kpi-builder.md](../../pages/12-kpi-builder.md).

## Principe : automatique d'abord, personnalisable ensuite

Trois niveaux, du plus simple au plus fin :

1. **Suggestions.** À l'ouverture, l'app propose 3 à 6 KPI prêts, déduits des colonnes. Le premier est déjà calculé et affiché ; en cliquer un autre l'affiche aussitôt. Aucun réglage n'est demandé.
2. **Builder (une ligne).** Quatre questions en langage naturel :
   - **Measure** : quoi compter ou additionner ;
   - **Over time** : la date et la période ;
   - **Split by** : regrouper par une ou deux colonnes ;
   - **Period** : la plage de dates.

   Tout le reste est déduit.
3. **Customize (panneau repliable).** Graphique, tableau, format des nombres, comparaisons.
   - Chaque réglage vaut **Auto** par défaut. Il affiche ce qu'Auto a choisi (« Auto · stacked bars ») et la raison au survol.
   - Un réglage modifié porte une pastille et un lien « Reset to auto ».
   - « Reset all to auto » remet tout le panneau à zéro.

Une ligne discrète sous le résultat explique les choix automatiques, par exemple : « Stacked bars because revenue adds up across countries · months because the data covers 3 years · top 8 countries, 14 others grouped ».

## User stories

1. J'ouvre **KPI** dans la barre latérale. Le premier KPI suggéré est déjà calculé : tuiles, graphique, tableau. Les autres suggestions sont des pastilles au-dessus.
2. Sous le graphique, des pastilles **« Split by country · segment · status »** proposent les colonnes de regroupement les plus pertinentes. Un clic ajoute le regroupement et recalcule.
3. Dans le builder, je change la mesure. J'en ajoute jusqu'à 4 (ex. « CA » et « commandes ») et je définis un **ratio** de deux mesures (« panier moyen = CA ÷ commandes »).
4. Je change la date, le grain (Auto · jour · semaine · mois · trimestre · année) et la période (tout · 12 derniers mois · depuis le début de l'année · plage libre). Je décide aussi si les filtres de la page s'ajoutent.
5. Je regroupe par 1 ou 2 colonnes. Au-delà de N modalités (8 par défaut), le reste passe en « Other ».
6. Un changement de **données** (mesures, temps, regroupements, Top N, période) active le bouton **Calculate**. Rien ne se recalcule à chaque clic. Un changement d'**affichage** (graphique, tableau, format, valeurs affichées) s'applique tout de suite, sans recalcul.
7. Dans **Customize**, je force le type de graphique, j'inverse lignes et colonnes du tableau, j'affiche des parts ou des variations, je renomme une mesure, je règle les décimales et ajoute une unité (« € »).
8. J'**enregistre** le KPI sous un nom (proposé automatiquement : « Revenue by month by country »). Mes KPI apparaissent dans une liste à gauche, où je les rouvre, renomme, duplique ou supprime.
9. J'exporte le tableau en CSV ou je le copie, pour le coller dans un tableur.

## 1. Suggestions de KPI (niveau 1)

Construites à partir du type d'analyse et du **rôle** des colonnes (`roles.toml`), sur la colonne de date par défaut (même choix que Séries temporelles : la seule date, sinon la première). Ordre et maximum de 6 :

| # | Condition | KPI suggéré | Nom affiché |
|---|---|---|---|
| 1 | toujours | nombre de lignes | « Rows » |
| 2 | colonne de rôle `amount` (2 au plus) | somme | « Total revenue » |
| 3 | colonne de rôle `quantity` (1 au plus) | somme | « Total units » |
| 4 | colonne identifiant **répétée** (valeurs distinctes < 90 % des lignes, ex. `customer_id`) | nombre de distincts | « Distinct customer_id » |
| 5 | un `amount` et un identifiant répété | ratio somme ÷ distincts | « Revenue per customer_id » |
| 6 | colonne booléenne (1 au plus) | part de « vrai » | « % churned » |
| 7 | colonne de rôle `rating` · `percent` · `duration` · `age` (1 au plus) | moyenne | « Average rating » |

- Un identifiant presque unique (≥ 90 % de valeurs distinctes) désigne la ligne elle-même : il n'est pas suggéré, puisque son comptage vaut « Rows ».
- Une colonne qui a déjà fourni un KPI ne revient pas sous une autre forme. Les suggestions s'arrêtent à 6.
- Sans date, les mêmes suggestions s'affichent en valeur unique, et le premier regroupement candidat (ci-dessous) est appliqué d'office : un KPI sans date ni regroupement ne serait qu'un nombre.

**Regroupements candidats** (pastilles « Split by ») : colonnes catégorielles, booléennes ou ordinales ayant entre 2 et 50 modalités, triées ainsi :

1. rôle `country`, `region`, `city`, `status`, `gender` d'abord ;
2. puis, par nombre de modalités, les plus proches de 3 à 12 ;
3. à égalité, par taux de valeurs vides croissant.

Les 3 premières sont proposées. Les identifiants et le texte libre ne le sont jamais.

## 2. Mesures

| Agrégat | Colonnes | Additif ¹ | Mesure par défaut d'une colonne |
|---|---|---|---|
| Rows (`count(*)`) | — | oui | — |
| Sum | numériques | oui | rôles `amount`, `quantity` |
| Mean | numériques | non | autres numériques (prix unitaire, note, âge, %) |
| Median | numériques | non | — |
| Min, Max | numériques, dates | non | — |
| Distinct count | toutes | **non** ² | identifiants, catégories |
| % true | booléennes | non | booléennes |
| Ratio A ÷ B | deux mesures du KPI | non | — |

¹ Additif : la valeur d'un ensemble est la somme des valeurs de ses parties. Seuls Rows et Sum le sont. Cela détermine le graphique, les totaux et le cumul (voir 4 et 6).

² Un même client acheté dans deux pays compte une fois au total, pas deux.

Quand on choisit une colonne, son agrégat par défaut suit la dernière colonne du tableau ci-dessus ; on peut le changer.

Règles de calcul :

- **Médiane** : `median()` exacte jusqu'à 200 000 lignes, `approx_quantile` au-delà (règle CLAUDE.md), signalée par « ≈ ».
- **Ratio** : calculé par cellule à partir des agrégats, soit Σ A ÷ Σ B, jamais comme une moyenne de ratios ligne à ligne. Une division par zéro donne une cellule vide. Option « Show as % » (× 100).
- **% true** : part de « vrai » parmi les valeurs non vides.
- **Valeurs vides** : ignorées par tous les agrégats sauf Rows.
- Au plus **4 mesures + 1 ratio**. La première mesure est la **mesure principale** : elle classe le Top N et ses tuiles viennent en premier.

## 3. Temps et période

- **Colonne** : dates et dates-heures. Sans aucune date, la section « Over time » est remplacée par « No date column — values over the whole data ».
- **Grain Auto** : le plus fin parmi jour · semaine · mois · trimestre · année qui donne **au plus 60 périodes** sur la plage choisie, et jamais plus fin que l'écart habituel entre deux dates (`typical_period` de 011). Exemples :
  - 3 ans de ventes quotidiennes → mois (36) ;
  - 6 mois quotidiens → semaine (26) ;
  - 10 ans mensuels → trimestre (40).
- **Grain forcé** : plafonné à 2 000 périodes ; au-delà, le grain est grossi et un avertissement le dit.
- **Période** :
  - All (défaut) ;
  - Last N periods (12 par défaut, dans l'unité du grain) ;
  - Year to date ;
  - Custom range (du … au …).
- **Use the page filters** (défaut : oui) : les filtres globaux s'ajoutent à la période. Décoché, le KPI ne voit que sa propre période.
- **Périodes incomplètes**. La première période est incomplète si la première date tombe après le début de la période. La dernière l'est si la dernière date est à plus d'un écart habituel avant la fin de la période. Une période incomplète est :
  - dessinée hachurée et notée « partial » dans le graphique ;
  - marquée † dans le tableau ;
  - **exclue des tuiles et des variations**.
- **Périodes vides** dans la plage : 0 pour Rows et Sum, vides pour les autres agrégats.
- **Contexte de comparaison** : quand la période est restreinte, le serveur lit en plus une période en amont (pour « vs previous ») et l'année précédente (pour « vs last year »). Ces valeurs servent aux variations et ne sont pas affichées comme des périodes.

## 4. Choix automatique du graphique

Le type est déduit de trois faits : présence d'une date, nombre de regroupements, additivité de la mesure.

| Date | Regroupements | Mesure | Graphique Auto |
|---|---|---|---|
| oui | 0 | additive, ≤ 24 périodes | barres verticales |
| oui | 0 | additive, > 24 périodes | aire (ligne + remplissage léger) |
| oui | 0 | non additive | ligne avec marqueurs (≤ 60 points) |
| oui | 1 | additive | **barres empilées** (≤ 24 périodes) / **aire empilée** (> 24) |
| oui | 1 | non additive | **lignes**, une par groupe |
| oui | 2 | toute | **petits multiples** : un mini-graphique par modalité du 1er regroupement (6 au plus, le reste en « Other »), le 2e regroupement en couleurs |
| non | 0 | toute | pas de graphique : **tuiles seulement** |
| non | 1 | toute | **barres horizontales** triées par valeur décroissante, « Other » en bas |
| non | 2 | additive | barres horizontales empilées (1er regroupement en lignes, 2e en couleurs) |
| non | 2 | non additive | **carte de chaleur** (1er × 2e) |

- **Plusieurs mesures** : un graphique par mesure, empilés avec le même axe des x (petits multiples). **Jamais de double axe.** Le ratio a son propre graphique.
- **Part en %** (option, auto à « off ») : un second graphique aligné dessous (barres 100 % ou aires 100 %), même axe x. Disponible seulement pour une mesure additive avec au moins un regroupement.
- **Types forcés possibles** : bars · stacked bars · grouped bars · line · area · stacked area · horizontal bars · heatmap. Un type incompatible est grisé avec sa raison, par exemple :
  - empilé : « Stacking needs an additive measure: a mean doesn't add up across groups » ;
  - aucun type empilé avec un seul groupe.
- **Couleurs** (skill dataviz) :
  - palette catégorielle dans l'ordre fixe ; la couleur suit la modalité, pas son rang, et reste la même après un filtre ;
  - « Other » toujours en gris ;
  - une seule série : la couleur d'accent, titre au lieu de légende ;
  - légende dès 2 séries, plus des libellés directs en bout de ligne jusqu'à 4 séries.
- **Survol** : info-bulle unifiée par période, avec les valeurs triées comme la légende et le total de la période pour une mesure additive.
- **Lisibilité** : au-delà de 8 groupes dans des lignes, les plus petits passent en « Other » et un avertissement le dit.

## 5. Choix automatique du tableau

Le tableau est un tableau croisé calculé sur les mêmes cellules que le graphique.

**Disposition Auto :**

| Cas | Lignes | Colonnes |
|---|---|---|
| date, 0 regroupement | périodes | mesures (+ ratio) |
| date, 1 regroupement, ≤ 13 périodes | groupes | **périodes** (« les mois en travers », comme un reporting) + Total |
| date, 1 regroupement, > 13 périodes | périodes | groupes + Total |
| date, 2 regroupements | 1er › 2e regroupement (hiérarchique, sous-totaux par 1er) | périodes si ≤ 13, sinon les 13 dernières périodes et un message « showing the last 13 periods; switch to periods in rows to see all » |
| pas de date, 1 regroupement | groupes | mesures + « % of total » de la mesure principale |
| pas de date, 2 regroupements | 1er regroupement | 2e regroupement + Total |

- Avec plusieurs mesures et des groupes en colonnes, chaque mesure forme un bloc de colonnes, avec un en-tête à deux niveaux.

**Totaux :**
- une ligne et une colonne Total quand elles ont un sens ;
- mesure additive : la somme des cellules ;
- mesure **non additive** (moyenne, médiane, distincts, ratio, % true) : la mesure **recalculée sur l'ensemble des lignes** (`GROUPING SETS`), jamais la somme ou la moyenne des cellules. Le total des moyennes est la moyenne globale, et le total des clients distincts compte chaque client une fois.

**Tri :**
- les périodes dans l'ordre chronologique ;
- les groupes par valeur décroissante de la mesure principale sur toute la plage, « Other » en dernier ;
- un clic sur un en-tête de colonne trie le tableau par cette colonne (le choix est conservé dans la vue).

**Ombrage Auto :**
- activé quand le tableau croise deux dimensions : une teinte séquentielle par bloc de mesure, de clair à foncé, les totaux exclus ;
- désactivé pour une simple liste.

**Lecture** : les cellules vides restent vides (pas « 0 »), sauf pour Rows et Sum sur une période vide. Les périodes incomplètes sont en italique avec †. La première colonne et la ligne d'en-tête restent figées au défilement.

**Export** : « Download CSV » (exactement le tableau affiché, valeurs brutes non formatées) et « Copy » (texte séparé par des tabulations, collable dans un tableur).

## 6. Valeurs affichées (graphique et tableau)

**Show as** : Value (Auto) · % of total · % of row · % of column · Change vs previous · % change vs previous · % change vs last year · Running total.

- **% of total** : la part de chaque groupe dans le total de sa période. En tableau, % of row et % of column précisent le sens.
- Les **variations** utilisent les périodes de contexte (section 3). Une période précédente incomplète ou absente donne une cellule vide.
- **vs last year** : grains jour, semaine, mois et trimestre, quand l'année précédente existe.
- **Running total** : somme courante dans l'ordre des périodes.
- **Parts et running total** n'existent que pour les mesures additives ; sinon l'option est grisée avec sa raison (« A running total of an average means nothing »).
- **Compare columns** (tableau, option) : ajoute à côté de chaque valeur les colonnes « Δ vs previous » et/ou « Δ% vs last year ».

## 7. Format des nombres

**Auto, par mesure :**
- Rows, Sum de valeurs entières, Distinct : entiers, séparateur de milliers.
- Mean, Median, Ratio : 2 décimales sous 10, 1 sous 1 000, aucune au-delà.
- % true et ratio « as % » : pourcentage avec 1 décimale.
- Rôle `percent` : suffixe « % ». Les valeurs sont multipliées par 100 si toutes sont entre 0 et 1.
- **Tuiles et axes** compacts (12.3k, 4.5M). **Tableau** en nombres complets.

**Personnalisable, par mesure :**
- nom affiché ;
- décimales (Auto, 0 à 4) ;
- compact (Auto · on · off) ;
- préfixe et suffixe libres (« € », « km », « pts »).

## 8. Tuiles

Une tuile par mesure (et par ratio), dans l'ordre des mesures.

- **Avec date** :
  - nom et valeur de la **dernière période complète** (avec son libellé : « Sep 2026 ») ;
  - variation vs la période précédente et vs l'an dernier : flèche ↑ ↓, %, et valeur précédente au survol ;
  - mini-courbe des 24 dernières périodes, la période de la tuile marquée.
  - Les variations restent en encre neutre avec une flèche : une hausse n'est pas toujours une bonne nouvelle (couleurs de statut réservées, skill dataviz).
- **Sans date** : la valeur sur l'ensemble, plus « Top: France · 34 % » quand il y a un regroupement et une mesure additive.
- Les tuiles portent sur le total, même avec des regroupements.

## 9. Personnalisation (niveau 3) : contenu du panneau Customize

| Section | Réglages (tous « Auto » par défaut) |
|---|---|
| Chart | type · part en % dessous (on/off) · libellés de valeurs (Auto : seulement les extrémités et au plus 4 séries) |
| Table | disposition (Auto · periods in rows · periods in columns) + bouton **⇄ Swap rows and columns** · totaux (lignes, colonnes) · ombrage · compare columns |
| Values | show as (section 6) |
| Groups | Top N (1–20, défaut 8) · Other : show / hide · ordre des groupes (by value · A → Z) |
| Format | par mesure : nom, décimales, compact, préfixe, suffixe |

- Les réglages **Groups** sont des changements de données : ils activent Calculate. Tous les autres sont des réglages d'affichage, appliqués immédiatement.
- Hors scope assumé : glisser-déposer des champs comme un pivot de tableur, formules libres, mise en forme conditionnelle par règles.

## 10. Disposition de la page

```
┌ KPI ─────────────────────────────────────────────────────────────────────────────────────┐
│ Saved      │ Suggested: [Rows] [Total revenue] [Distinct customers] [Revenue per customer]│
│ ─────────  │ ┌ Builder ────────────────────────────────────────────────────────────────┐ │
│ Revenue by │ │ Measure [Sum of revenue ▾] [+ Measure] [+ Ratio]                       │ │
│  country   │ │ Over time [order_date ▾] [Auto · month ▾]   Period [All ▾] ☑ page filters│ │
│ Churn rate │ │ Split by [country ▾] [+]                         [Calculate]  [Save]     │ │
│ + New      │ └─────────────────────────────────────────────────────────────────────────┘ │
│            │ [Tile Revenue Sep 2026 1.2M ↑ 4 % · ↑ 12 % yoy ~~~]  [Tile …]              │
│            │ Chart  ─────────────────────────────────────────────── [Customize ▸]       │
│            │ Why this view: stacked bars because revenue adds up across countries…      │
│            │ Split by: [country] [segment] [status]                                     │
│            │ Table  ─────────────────────────────────── [⇄] [Copy] [Download CSV]       │
└──────────────────────────────────────────────────────────────────────────────────────────┘
```

- Le panneau **Customize** s'ouvre à droite, par-dessus sans décaler le graphique sur grand écran, et en dessous sur petit écran.
- La définition courante est dans l'URL (`?kpi=<id>` pour un KPI enregistré, sinon la définition encodée), pour pouvoir partager le lien en local et revenir en arrière.

## 11. Données et API

**Définition** (JSON stocké et envoyé ; `"auto"` ou `null` signifient « laisser l'app choisir ») :

```json
{
  "measures": [
    {"id": "m1", "agg": "sum", "column": "revenue",
     "label": null, "format": {"decimals": "auto", "compact": "auto", "prefix": "", "suffix": ""}}
  ],
  "ratio": {"numerator": "m1", "denominator": "m2", "label": null, "percent": false},
  "time": {"column": "order_date", "grain": "auto",
           "period": {"kind": "all", "n": 12, "from": null, "to": null}, "page_filters": true},
  "groups": [{"column": "country"}],
  "top": 8, "other": "show", "group_order": "value",
  "view": {"chart": "auto", "share": false, "labels": "auto",
           "table": {"layout": "auto", "totals": "auto", "shading": "auto", "compare": [], "sort": null},
           "show_as": "value"}
}
```

`ratio` et `time` valent `null` quand il n'y en a pas ; `groups` compte de 0 à 2 éléments.

**Endpoints :**
- `GET /modules/kpi/datasets/{id}/suggestions` → KPI suggérés (définition complète + nom) et regroupements candidats.
- `POST /modules/kpi/datasets/{id}/compute` (corps : la définition, plus les filtres de la page) renvoie :
  - `resolved` : chaque choix Auto résolu (grain, graphique, disposition, format), avec sa raison en une phrase ;
  - `periods` : libellé, début, `partial` ;
  - `groups` : modalités dans l'ordre, couleur par index stable, `other_count` ;
  - `cells` : par mesure × période × groupe : `value`, `previous`, `last_year` ;
  - `totals` : par période, par groupe et global, recalculés via `GROUPING SETS` ;
  - `tiles` ;
  - `name` : le nom proposé ;
  - `warnings`.

  « Show as », la disposition, l'ombrage et le format sont appliqués **côté navigateur** à partir de ces cellules ; aucun changement d'affichage ne recalcule.
- `GET / POST / PUT / DELETE /modules/kpi/datasets/{id}/definitions[/{kpi}]` ; `POST …/{kpi}/duplicate`.

**Table `kpi_definitions`** (migration 0008) : id, dataset_id, name, definition (JSON), created_at, updated_at. Les KPI d'un dataset sont supprimés avec lui. Une définition dont une colonne a disparu se rouvre avec un message (« Column revenue no longer exists ») et le builder désigne le champ à corriger.

**Calcul** : une seule requête DuckDB.
- Une sous-requête classe le Top N : les modalités au plus grand total de la mesure principale sur la plage.
- Les autres modalités sont remplacées par « Other » **avant** l'agrégation. Ainsi « Other » est juste même pour une médiane ou des distincts.
- `date_trunc` au grain, puis `GROUP BY GROUPING SETS` pour les cellules et tous les totaux.
- Aucune ligne brute n'est envoyée au navigateur.

**Code** :
- `backend/app/domain/kpi/` : `definition.py` (schéma), `auto.py` (suggestions, grain, graphique, disposition, format : fonctions pures testées une à une), `query.py` (SQL), `tiles.py` ;
- `backend/app/modules/kpi/` : service, router ;
- frontend `modules/kpi/`.

## 12. Limites et cas limites

- **Plafonds** : 5 000 points (périodes × groupes) dans un graphique ; 50 000 cellules dans le tableau. Au-delà : un message avec un grain plus grossier proposé en un clic.
- **Plages vides** :
  - 0 ligne après filtres et période : « No rows in this period » et un bouton « Use all dates » ;
  - une seule période : tuiles et tableau, pas de courbe.
- **Regroupement** : une colonne avec une seule modalité est refusée (« country has a single value here ») ; les valeurs vides deviennent une modalité « (empty) ».
- **Dates** : les dates futures sont gardées. Une période vide au milieu de la plage reste affichée (section 3).

## Critères d'acceptation

**Automatique :**
- GIVEN un CSV de ventes (date, `revenue`, `units`, `customer_id` répété, `country`, `churned` booléen) WHEN j'ouvre KPI THEN les suggestions sont, dans l'ordre : Rows, Total revenue, Total units, Distinct customer_id, Revenue per customer_id, % churned ; « Rows » est calculé, et « Split by » propose country en premier.
- GIVEN 3 ans de dates quotidiennes THEN le grain Auto est le mois ; GIVEN 6 mois THEN la semaine.
- GIVEN chaque ligne du tableau de la section 4 THEN le graphique Auto est celui indiqué (test unitaire par ligne). De même pour la disposition de la section 5.
- GIVEN une moyenne par pays THEN le graphique Auto est en lignes, pas empilé, et forcer « stacked bars » est grisé avec sa raison.

**Calcul :**
- GIVEN « sum of revenue by month by country, top 3 » THEN les cellules égalent un calcul pandas de référence, « Other » contient le reste, et la somme des groupes égale le total.
- GIVEN une médiane par pays THEN le total vaut la médiane de toutes les lignes, pas la somme ni la moyenne des médianes. GIVEN des clients distincts par pays THEN le total compte chaque client une fois.
- GIVEN un ratio CA ÷ commandes THEN chaque cellule = Σ CA / Σ commandes de la cellule.
- GIVEN un mois de décembre incomplet THEN il est marqué « partial », et la tuile utilise novembre et le compare à octobre.
- GIVEN « Last 12 months » THEN « % change vs last year » est rempli pour les 12 mois grâce à la période de contexte.
- GIVEN « Use the page filters » décoché THEN un filtre global ne change pas le résultat.

**Personnalisation :**
- GIVEN un résultat affiché WHEN je change « Show as », la disposition ou le format THEN aucune requête n'est envoyée.
- GIVEN un réglage modifié WHEN je clique « Reset to auto » THEN le choix Auto revient et la pastille disparaît.
- GIVEN un KPI enregistré avec des personnalisations WHEN je le rouvre THEN la définition, l'affichage et les valeurs sont identiques.

**Transverse :**
- **Performance** : < 2 s sur 5 M lignes pour un KPI à 1 regroupement (test lent à part).
- **Accessibilité** : tuiles, tableau et panneau utilisables au clavier ; la couleur n'est jamais le seul repère (légende, libellés directs, † pour les périodes incomplètes).

## Hors scope

- Tableaux de bord de plusieurs KPI sur une même page.
- Alertes et objectifs.
- Formules libres (au-delà du ratio de deux mesures) et colonnes calculées.
- Pivot en glisser-déposer.
- Mise en forme conditionnelle par règles.
- Partage hors de la machine.
