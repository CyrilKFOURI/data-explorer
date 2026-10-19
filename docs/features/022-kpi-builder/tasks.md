# 022 — Tâches

Spec : [spec.md](spec.md). Page : [12-kpi-builder.md](../../pages/12-kpi-builder.md).

## Choix de réalisation

- **Domaine pur** dans `backend/app/domain/kpi/` :
  - `definition.py` : la définition (pydantic), validée contre les colonnes ;
  - `rules.py` : chaque règle automatique est une fonction pure qui renvoie une `Decision` (valeur, règle, raison, alternatives autorisées ou interdites) ;
  - `suggest.py` : suggestions de KPI et regroupements candidats ;
  - `query.py` : SQL DuckDB, avec Top N, « Other » remplacé avant l'agrégation et `GROUPING SETS` ;
  - `compute.py` : assemble les cellules, les totaux, les tuiles et les décisions.
- **Module** `backend/app/modules/kpi/` : service (lecture via les filtres, cache, CRUD SQLite) et router.
- **Deux requêtes `GROUPING SETS`** sur une table temporaire des lignes typées (« Other » déjà replié) : cellules et totaux par période sur la plage étendue (période précédente et an dernier compris), puis par groupe sur la plage affichée. Toutes les mesures dans la même requête.
- **Faits du résultat** (négatifs, groupe dominant, taux de cellules vides, ordinal) calculés après l'agrégation, puis passés aux règles de graphique. Les règles ne lisent jamais la base.
- **Côté navigateur** : « Show as », disposition, ombrage, format et type de graphique (parmi les alternatives autorisées) sans recalcul.

## Tâches

- [x] T1 — Doc de page `docs/pages/12-kpi-builder.md`.
- [x] T2 — Domaine : définition, règles (temps, graphique, tableau, format), suggestions — tests règle par règle.
- [x] T3 — Requête et calcul : mesures, ratio, % true, Top N + Other, totaux recalculés, périodes vides et incomplètes, contexte (précédente, an dernier), tuiles, plafonds — tests contre pandas.
- [x] T4 — Module : migration 0008 `kpi_definitions`, service, API (suggestions, compute, CRUD, duplicate), enregistrement dans `registry.py` — tests API.
- [x] T5 — Frontend : manifeste, page, suggestions, builder, tuiles, graphique(s), tableau croisé, Customize (Auto / reset), KPI enregistrés, export CSV / copie.
- [x] T6 — Docs (PLAN, USER_GUIDE, BACKEND_SCHEMA, APP_FLOW), vérifications, navigateur, commit.

## Découvertes

- Les règles de graphique fonctionnent sur les vraies données : sur `sales_timeseries`, « promo = False » fait 91 % du CA, donc R-VIS-12 passe en lignes au lieu d'empiler. Sur `typing_traps` avec 2 regroupements (pays, ville), beaucoup de cellules vides font passer en petits multiples de barres (R-VIS-06 + R-VIS-13).
- Une colonne retypée en nombre sans aucune valeur lisible (0 distinct) était suggérée (« Average store ») → les suggestions ignorent les colonnes sans valeur lisible.
- « Hide Other », les noms et les formats des mesures sont des réglages d'affichage : ils ne sont pas envoyés au calcul (pas de recalcul). Top N et l'ordre des groupes restent des changements de données (Calculate).
- Min et max se limitent aux colonnes numériques (pas de dates) pour garder des cellules numériques partout.
- Les erreurs de l'API portent désormais `field` et `suggestion` en plus du code (`AppError.details`) : le builder entoure le champ à corriger, et « Show by quarter » propose le grain plus grossier en un clic.
- Performance : 5 M lignes, 1 regroupement, < 2 s (test lent passé) ; les lignes sont lues une fois dans une table temporaire DuckDB, puis toutes les requêtes portent sur elle.
