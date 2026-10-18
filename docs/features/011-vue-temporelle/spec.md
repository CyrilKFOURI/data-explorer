# 011 — Vue temporelle dans Comparer

## Objectif

Quand on croise **une date et une variable numérique** dans Comparer, montrer d'emblée ce qu'un analyste regarde en premier dans une série : la courbe agrégée par période, sa **moyenne glissante**, sa **bande ± écart-type glissant**, et un vrai **test de tendance**. Sans réglage obligatoire, en quelques secondes. Les analyses lourdes (décomposition, stationnarité, prévision…) restent dans la page Séries temporelles (012+), ouverte par un lien prérempli.

Remplace la vue date × num actuelle de 006 (« moyenne par période avec min–max, Spearman »). Références : [05-comparer.md](../../pages/05-comparer.md), [DATES.md](../../DATES.md), [10-series-temporelles.md](../../pages/10-series-temporelles.md).

## Principe : toujours agréger d'abord

Une série temporelle a **une valeur par période**. Or un fichier en a souvent plusieurs par date (les ventes de 10 magasins le même jour). Une moyenne glissante calculée ligne à ligne n'a alors aucun sens. La vue agrège donc **toujours** par période, puis calcule les statistiques glissantes sur la série agrégée. Le choix fait est affiché en clair.

> **Méthodes** : celles décrites ci-dessous sont les méthodes cochées par défaut ; toutes les méthodes de la section listées dans [TIMESERIES_METHODS.md](../../TIMESERIES_METHODS.md) sont proposées via « + Add method », avec la même présentation (`TestResult`, options, contribution au verdict).

## User stories

1. Je choisis X = `order_date`, Y = `revenue` : la vue **Time series** s'affiche avec la courbe agrégée, la moyenne glissante et la bande ± 1 écart-type glissant, sans rien régler.
2. Une barre d'options discrète au-dessus du graphique me laisse changer, si je le veux :
   - **Period** : Auto · Day · Week · Month · Quarter · Year ;
   - **Aggregate** : Sum · Mean · Median · Min · Max · Count ;
   - **Window** : la fenêtre glissante (en nombre de périodes) ;
   - **Show** : courbe brute, moyenne glissante, bande ± σ (cases à cocher).
3. Avec une **Couleur** (catégorie), j'obtiens une courbe par groupe (8 groupes au plus, les plus importants ; le reste en « Others ») ; la moyenne glissante est tracée pour chacune, la bande seulement quand il n'y a qu'une série (lisibilité).
4. Le panneau « Statistical test » donne un **test de tendance** : Mann-Kendall + pente de Sen (« revenue increases by about 1 240 per month, p < 0.001 »), au lieu de Spearman.
5. Un lien **Analyze as time series →** ouvre la page Séries temporelles avec la date, la variable, l'agrégation, la période et le groupe déjà choisis.
6. Tous les choix sont dans l'URL (partageables, conservés au retour).

## Valeurs par défaut (pensées pour ne rien avoir à régler)

| Réglage | Défaut | Règle |
|---|---|---|
| Period | Auto | Le pas typique détecté (DATES.md), relevé si la série dépasse **400 périodes** (jour → semaine → mois…) ; ex. 3 ans de données quotidiennes → semaines (~156 points). |
| Aggregate | Sum ou Mean | **Sum** si le rôle de Y est `amount` ou `quantity` (des montants et volumes s'additionnent), **Mean** sinon (prix, âge, note, pourcentage…). |
| Window | selon la période | Day → 7, Week → 4, Month → 3, Quarter → 4, Year → 3 ; jamais plus du quart de la série. Fenêtre **centrée** ou **arrière** (défaut : arrière, celle qui « ne voit pas le futur »). |
| Show | courbe + moyenne + bande | — |

Le libellé sous le titre résume le choix : « Weekly sum of revenue · 7-period rolling mean ± 1σ ».

## Combinaison avec les autres variables

- **Couleur** = catégorie → une série par groupe (agrégation par période et groupe).
- **Z** : non proposé avec une date.
- **X = partie de date** (`order_date › Month`, `› Day of week`) : ce n'est pas une série temporelle mais une saisonnalité → vue existante num × cat (boîtes), inchangée.
- **date × cat** : inchangé (effectifs par période, aire empilée).

## Critères d'acceptation

- **Agrégation** : calculée en SQL (DuckDB, `date_trunc`) sur **toutes les lignes** filtrées. GIVEN 3 lignes le 2024-01-01 (10, 20, 30) WHEN Aggregate = Sum, Period = Day THEN la valeur du 2024-01-01 vaut 60 ; Mean → 20 ; Count → 3.
- **Périodes vides** : une période sans ligne reste un **trou** dans la courbe (pas de 0 inventé), sauf pour Count et Sum, où l'absence vaut 0 (« rien vendu cette semaine-là »). Les statistiques glissantes ignorent les trous (`min_periods` = moitié de la fenêtre).
- **Statistiques glissantes** : moyenne et écart-type (ddof = 1) glissants sur la série agrégée, fenêtre arrière par défaut. GIVEN une série de référence THEN les valeurs égalent `pandas.Series.rolling(w, min_periods=⌈w/2⌉).mean() / .std()` à 1e-9 près.
- **Test de tendance** :
  - Mann-Kendall (S, Z avec correction des ex-aequo, p bilatérale) et pente de Sen (médiane des pentes, en unités de Y par période) avec IC 95 % ;
  - calculés sur la série agrégée (une valeur par période) ; si plus de 5 000 périodes, échantillon régulier signalé ;
  - verdict en une phrase : sens, ampleur (« about +4 % per year relative to the mean »), significativité ; « No clear trend » si p ≥ α ;
  - mise en garde affichée si une autocorrélation forte est probable (lag-1 > 0,5) : « Successive values are strongly linked; the p-value may be optimistic. The time series page tests this properly. »
  - GIVEN une série de référence THEN S, Z, p et la pente égalent une implémentation de référence (`pymannkendall` utilisé seulement dans les tests, ou valeurs publiées) — pas de dépendance d'exécution ajoutée.
- **Périodes incomplètes** : si les données commencent après le début de la première période (ou finissent avant la fin de la dernière), cette période est tracée mais exclue du test de tendance pour Sum et Count (sa somme est trop basse), avec une note sous les options.
- **Moins de 8 périodes** : courbe affichée, pas de statistique glissante ni de test, message « Too few periods for a trend test (8 needed). »
- **Volumes** : au plus 2 000 points par série dessinés (au-delà, la période est relevée automatiquement, signalé). Performance : 5 M lignes en moins de 2 s.
- **Couleurs** : série unique en `--chart-1`, moyenne glissante en trait plus épais de la même teinte, bande = même teinte à 15 % d'opacité ; groupes : palette catégorielle dans l'ordre fixe. Infobulle : période, valeur, moyenne glissante, ± σ, nombre de lignes agrégées.
- **Accessibilité** : la légende nomme chaque tracé (« Weekly sum », « 4-week rolling mean », « ± 1σ band ») ; la table des données utilisées liste période, valeur, moyenne, écart-type, n.

## Hors scope

Décomposition, stationnarité, autocorrélation, hétéroscédasticité, prévision, zoom sur plage (page Séries temporelles, 012+). Plusieurs Y numériques superposés.
