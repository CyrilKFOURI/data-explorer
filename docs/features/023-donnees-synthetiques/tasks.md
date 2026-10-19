# 023 — Tâches

Spec : [spec.md](spec.md). Page : [13-donnees-synthetiques.md](../../pages/13-donnees-synthetiques.md). Recherche : [evaluation-donnees-synthetiques.md](../../research/evaluation-donnees-synthetiques.md).

## Choix de réalisation

- **Domaine pur** dans `backend/app/domain/synthetic/` (entrées simples, dataclasses en sortie, ni FastAPI ni SQLite) :
  - `plan.py` : règles R-SYN, traitement de chaque colonne, méthode recommandée ;
  - `encode.py` : apprentissage des colonnes (bornes, décimales, modalités, format d'identifiant) et retour aux valeurs typées ;
  - `methods/` : `cart.py`, `copula.py`, `bayes.py`, `independent.py`, plus un tirage commun « valeur réelle de la même feuille / du même intervalle » ;
  - `diagnostic.py`, `quality.py` (formes, paires, couverture, associations), `detection.py`, `utility.py`, `privacy.py` (copies, DCR, CAP), `compare.py` (colonne par colonne, paires, vues d'ensemble) ;
  - `report.py` : assemble le rapport complet d'un run.
- **Représentation commune** : un `DataFrame` pandas typé (nombres en `float`, dates en `datetime64`, catégories en texte, vide = `NaN`/`None`). Les méthodes travaillent sur une matrice codée (nombres, secondes, codes de modalités, vide comme état à part) produite par `encode.py`.
- **Valeurs vides** :
  - CART : un arbre « vide ou non » d'abord, puis l'arbre de la valeur sur les lignes non vides ;
  - copule : le vide est une masse au bas de la loi de la colonne ;
  - réseau bayésien : le vide est un intervalle ou une modalité à part.
- **Fichiers d'un run** : `datasets/<id>/synthetic/<run>/` avec `data.parquet` (synthétique complet), `train.parquet` et `holdout.parquet` (lignes réelles typées, pour les évaluations à la demande), `report.json`. Tout est supprimé avec le dataset source.
- **Jobs en mémoire** comme le module ML : étapes `loading` → `generating` (apprentissage et génération) → `evaluating` → `saving`, annulation vérifiée entre les étapes et entre deux colonnes.
- **Utilité et CAP** : calculés à la demande (POST), puis enregistrés dans le rapport du run.
- **Save as dataset** : le Parquet est copié dans `uploads/` puis importé par l'import habituel ; une étape après l'import recopie les types, rôles et ordres de la source sous forme de corrections (le parseur est recalculé pour les valeurs déjà typées).
- **GPU** : `domain/settings/gpu.py` lit `nvidia-smi` (nom, mémoire, pilote) ; le réglage `compute.use_gpu` est enregistré mais sans effet en 023.

## Tâches

- [x] T1 — Doc de page `docs/pages/13-donnees-synthetiques.md`.
- [x] T2 — Domaine, plan et encodage : règles R-SYN-01 à 08, apprentissage des colonnes, identifiants régénérés, valeurs fictives au même format — tests.
- [x] T3 — Domaine, méthodes : CART séquentiel (ordre automatique, feuilles ≥ 5, lissage), copule gaussienne, réseau bayésien Chow-Liu, colonnes indépendantes — tests (bornes, modalités, entiers, vides ± 3 points, graine, corrélation 0,9 gardée).
- [x] T4 — Domaine, évaluation : diagnostic, qualité (formules contre des cas calculés à la main), détection, utilité, confidentialité (copies, DCR, protections, valeurs rares, CAP), comparaison colonne par colonne et vues d'ensemble — tests.
- [x] T5 — Module : migration 0009 `synthetic_runs`, service (jobs, runs, fichiers, dataset créé), API, enregistrement dans `registry.py` ; GPU dans les réglages — tests API, test lent de performance.
- [x] T6 — Frontend : manifeste, page (plan, réglages, progression), rapport (4 chiffres, Columns, Links, Checks, Privacy, Utility, Overview, Data), runs et comparaison, Save as dataset ; Settings › Compute.
- [x] T7 — Docs (PLAN, USER_GUIDE, BACKEND_SCHEMA, APP_FLOW), vérifications, navigateur, commit.

## Découvertes

- **CART recopiait des lignes** sur les jeux à peu de colonnes : sur `sales_timeseries` (5 colonnes), 52 % des lignes synthétiques étaient à 1 % près d'une vraie ligne, 257 strictement identiques. Deux corrections :
  - **« Smooth numbers » activé par défaut**, comme une option de synthpop. Il ne s'applique qu'aux nombres continus ayant au moins 20 valeurs distinctes, et aussi à la première colonne. Lisser les entiers, les dates ou les années créait des valeurs qui trahissaient le synthétique : la détection tombait à 36 % sur `typing_traps`.
  - **« Drop copies of real rows » activé par défaut**, comme la règle « replicated uniques » de synthpop. On génère 5 % de lignes en plus, puis les lignes identiques à une vraie ligne sont remplacées. Leur nombre est indiqué avec le run.
  - Résultat sur `sales_timeseries` : 0 copie exacte, protection contre la mémorisation de 0,76 à 0,92, qualité inchangée.
- **Copies exactes et copies proches sont séparées.** Le chiffre Privacy utilise les copies exactes. Les copies « à 1 % de l'étendue près » (NewRowSynthesis de SDMetrics) sont affichées à côté : elles sont naturellement nombreuses sur des données à peu de colonnes.
- **Les lignes réelles d'évaluation reçoivent le même regroupement « Other » que l'apprentissage (R-SYN-08).** Sans cela, le détecteur reconnaissait le synthétique à la seule colonne `zip_code` : 0 % de détection sur `typing_traps`.
- **Une colonne au rôle e-mail ou téléphone est laissée de côté même si son type est identifiant**, comme le veut le critère d'acceptation. « Keep unique » et « Fake values » restent proposés.
- **Performance** :
  - HistGradientBoosting avec 200 itérations prenait 20 à 40 s sur cette machine (processeur hybride). Avec l'arrêt anticipé, la détection prend environ 2 s.
  - Les distances de confidentialité sont calculées par blocs en float32, dans des tampons réutilisés : 31 s → 5 s.
  - Test lent (50 000 lignes × 20 colonnes, CART, évaluation comprise) : 27 s, pour une cible de 60 s.
- **Noms de classes uniques dans l'OpenAPI** (`SyntheticRun`, `PairBox`, `DcrHistogram`…). Un nom déjà pris (`Run`, `Box`, `Overview`) renomme les schémas des autres modules et casse les types du frontend.
- **Paramètres** : l'enregistrement envoie maintenant tous les réglages (détection et compute), pour qu'enregistrer l'un ne remette pas l'autre à zéro.
