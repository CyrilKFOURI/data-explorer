# 012 — Séries temporelles : page, vue d'ensemble, saisonnalité, décomposition

## Objectif

Créer la page `/d/:id/timeseries` (module branché par les registres), sa barre de configuration, et les trois premières sections : **Overview**, **Seasonality**, **Decomposition**. Référence : [10-series-temporelles.md](../../pages/10-series-temporelles.md).

> **Méthodes** : celles décrites ci-dessous sont les méthodes cochées par défaut ; toutes les méthodes de la section listées dans [TIMESERIES_METHODS.md](../../TIMESERIES_METHODS.md) sont proposées via « + Add method », avec la même présentation (`TestResult`, options, contribution au verdict).

## User stories

1. Dans la barre latérale, une entrée **Time series** (section Modules) ouvre la page, déjà configurée : je vois la série tout de suite.
2. Je change la date, la variable, la période, l'agrégation, le groupe ou la gestion des trous dans la barre de configuration ; tout est dans l'URL.
3. **Overview** : la courbe, la moyenne et l'écart-type glissants (réglables comme en 011), un curseur de plage sous le graphique pour zoomer, et quatre chiffres clés : début–fin, nombre de périodes, périodes manquantes, variation totale (premier → dernier quart de la série, en %).
4. **Seasonality** :
   - « une courbe par année » (axe = mois ou semaine de l'année), l'année en cours mise en avant ;
   - boîtes par mois, par jour de semaine (et par heure si date-heure), selon ce que la période permet ;
   - verdict : la saisonnalité la plus marquée (« strong weekly pattern: Saturdays are 38 % above average ») d'après Kruskal–Wallis entre les sous-périodes et la taille d'effet ε².
5. **Decomposition** : STL (robuste) en quatre panneaux alignés — série, tendance, saisonnalité, résidu — avec la **force de la tendance** et la **force de la saisonnalité** (Hyndman, 0–1) et leur lecture (« the trend explains most of the variation »). Bascule STL / classique (additive, multiplicative).
6. Avec un groupe, je choisis la série étudiée ; Overview peut superposer toutes les séries (case « Show all series »).
7. Depuis Comparer (011), « Analyze as time series → » arrive ici prérempli.

## Critères d'acceptation

- **Module** : déclaré dans `backend/app/modules/registry.py` et `frontend/src/modules/registry.ts` ; exige au moins une colonne date (sinon grisé avec infobulle). Le module de démonstration « Hello » est retiré.
- **Série** : construite par le même code que 011 (agrégation, trous, période Auto) — une seule implémentation dans `domain/timeseries/series.py`, réutilisée par Comparer.
- **Trous** : Leave / Interpolate / Fill 0 / Carry forward. GIVEN [1, ∅, 3] WHEN Interpolate THEN [1, 2, 3] ; Carry forward → [1, 1, 3].
- **Période saisonnière** déduite de la période : Day → 7 (et 365 si ≥ 2 ans), Week → 52, Month → 12, Quarter → 4, Hour → 24. Modifiable (« Season length ») dans la section Decomposition.
- **STL** : `statsmodels.tsa.seasonal.STL(robust=True)` sur la série complétée (interpolation signalée). Exige au moins 2 cycles complets, sinon message chiffré.
- **Forces** (Hyndman & Athanasopoulos) : F_T = max(0, 1 − Var(R) / Var(T + R)), F_S = max(0, 1 − Var(R) / Var(S + R)). GIVEN une série synthétique tendance + saison + bruit connue THEN F_T et F_S sont dans les bornes attendues (tests).
- **Saisonnalité (verdict)** : Kruskal–Wallis entre sous-périodes sur la série **sans tendance** (résidu + saison de STL, sinon série différenciée) ; ε² et l'écart du sous-groupe le plus extrême à la moyenne, en %.
- **Volumes** : séries de plus de 5 000 points → période relevée automatiquement pour les calculs (signalé) ; 2 000 points dessinés au plus par tracé.
- **Performance** : 5 M lignes → configuration + Overview en moins de 2 s ; STL sur 5 000 points en moins de 1 s.
- **Tests** : série (agrégations, trous), forces, saisonnalité sur données synthétiques, module grisé sans date, URL.

## Hors scope

Stationnarité, autocorrélation (013), volatilité, ruptures (014), prévision (015).
