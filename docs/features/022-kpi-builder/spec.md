# 022 — Module Builder KPI

## Objectif

Construire en quelques clics un **indicateur métier** — « chiffre d'affaires par mois et par pays », « nombre de clients distincts par semaine », « panier moyen par trimestre » — le voir en **tuiles**, en **graphique** et en **tableau croisé**, puis l'**enregistrer** pour le retrouver. Là où la page Séries temporelles analyse une courbe en profondeur, le Builder KPI est l'outil rapide du tableau de bord. Origine : [modules-futurs/kpi-builder.md](../../modules-futurs/kpi-builder.md). Page : [12-kpi-builder.md](../../pages/12-kpi-builder.md).

## User stories

1. J'ouvre **KPI** dans la barre latérale : un KPI par défaut est déjà proposé (comptage de lignes par période sur la première date, ou par la première catégorie s'il n'y a pas de date) et calculé.
2. Je choisis une **mesure** : nombre de lignes, ou somme · moyenne · médiane · min · max · nombre de valeurs distinctes d'une colonne ; je peux en ajouter jusqu'à 4 (ex. « CA » et « Nombre de commandes ») et définir un **ratio** de deux mesures (« panier moyen = CA ÷ commandes »).
3. Je choisis le **temps** : colonne de date, grain (jour · semaine · mois · trimestre · année), **période** (tout · 12 derniers mois · depuis le début de l'année · plage libre), et si les filtres globaux s'ajoutent ou non à cette période.
4. Je **regroupe** par une ou deux colonnes (pays, puis segment) ; au-delà de N modalités (8 par défaut), les autres sont regroupées en « Other ».
5. Je clique **Calculate** (le calcul n'est pas relancé à chaque réglage) et je vois :
   - des **tuiles** : valeur de la dernière période complète, variation vs la précédente et vs la même période l'an dernier, mini-courbe ;
   - un **graphique** au style de mon choix (barres · barres empilées · ligne · aire · aire empilée), avec option **part en %** affichée dans un second graphique aligné dessous (pas de double axe) ;
   - un **tableau croisé** lignes × colonnes (ex. périodes × pays) avec totaux, ombrage proportionnel et export CSV.
6. J'affiche au choix la **valeur**, la **part du total**, la **variation vs la période précédente** ou le **cumul**.
7. J'**enregistre** le KPI sous un nom ; la liste de mes KPI est à gauche ; je rouvre, renomme, duplique ou supprime.

## Règles

- **Grain par défaut** : celui que choisit la page Séries temporelles (011) pour la colonne de date ; les périodes incomplètes au début et à la fin (sommes, comptages) sont signalées et exclues des tuiles.
- **Médiane** : `median()` DuckDB exacte jusqu'à 200 000 lignes, `approx_quantile` au-delà (CLAUDE.md).
- **Ratio** : calculé par période et par groupe à partir des agrégats (Σ CA ÷ Σ commandes), jamais comme moyenne de ratios ligne à ligne ; division par zéro → vide.
- **Top N** : les N modalités au plus grand total de la première mesure sur la période ; le reste en « Other » (option « Hide Other »).
- **Part en %** : part de chaque groupe dans le total de la période ; **cumul** : somme courante dans l'ordre des périodes (sommes et comptages seulement ; désactivé avec la raison pour moyenne, médiane, min, max, distincts et ratios).
- **Variation vs l'an dernier** : disponible pour les grains jour, semaine, mois, trimestre quand la période de l'an dernier existe.
- **Périodes vides** : affichées à 0 pour un comptage ou une somme, vides sinon.
- **Filtres** : « Use the page filters » (défaut : oui) ajoute les filtres globaux à la période du KPI ; sinon le KPI ne voit que sa propre période.
- **Limites** : 5 000 périodes × groupes au plus dans le graphique, 50 000 cellules dans le tableau croisé (au-delà : message et grain plus grossier suggéré).

## Graphiques (skill dataviz)

- Couleurs : palette catégorielle dans l'ordre fixe ; la couleur suit le groupe, pas son rang (un filtre ne repeint pas les survivants) ; « Other » en gris.
- Un seul axe des y par graphique ; la part en % est un second graphique dessous, même axe x.
- Barres et aires empilées : ≥ 2 groupes ; ligne : ≤ 8 groupes lisibles, au-delà les groupes les plus petits passent en « Other ».
- Survol : info-bulle unifiée par période ; légende toujours présente dès 2 groupes.

## Données et API

- Table `kpi_definitions` (migration) : id, dataset, nom, définition JSON, créé / modifié.
- `POST /modules/kpi/datasets/{id}/compute` (corps : la définition) → périodes, séries par groupe et par mesure, totaux, tableau croisé, tuiles, avertissements.
- `GET / POST / PUT / DELETE /modules/kpi/datasets/{id}/definitions[/{kpi}]`.
- Calcul en une requête DuckDB agrégée (date tronquée au grain, groupes, agrégats), Top N par une sous-requête ; jamais de lignes brutes vers le navigateur.

## Critères d'acceptation

- GIVEN un CSV de ventes WHEN « sum of revenue by month by country, top 3 » THEN les totaux par mois égalent un calcul pandas de référence, « Other » contient le reste, la somme des groupes égale le total.
- GIVEN un ratio CA ÷ commandes THEN chaque valeur = Σ CA / Σ commandes de la cellule (pas une moyenne de ratios).
- GIVEN une moyenne THEN le cumul est désactivé avec sa raison.
- GIVEN un mois de décembre incomplet THEN il est signalé et la tuile utilise novembre.
- GIVEN « Use the page filters » décoché THEN un filtre global ne change pas le résultat.
- GIVEN un KPI enregistré WHEN je le rouvre THEN la définition et le résultat sont identiques.
- Performance : < 2 s sur 5 M lignes pour un KPI à 1 regroupement (test lent à part).
- Accessibilité : tuiles et tableau lisibles au clavier, couleurs jamais seules (légende, libellés).

## Hors scope

Tableaux de bord de plusieurs KPI sur une même page, alertes / objectifs, formules libres (au-delà du ratio de deux mesures), partage.
