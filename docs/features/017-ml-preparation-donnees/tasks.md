# 017 — Tâches

Spec : [spec.md](spec.md). Le moteur de règles (R-SEL, R-NUM, R-CAT, R-ORD, R-DATE, R-BOOL) existe depuis 016 ; cette feature le rend **modifiable** et ajoute sélection, aberrantes, déséquilibre et aperçu.

## Choix de réalisation

- Le tiroir **Settings** de 019 n'existe pas encore : l'éditeur s'ouvre dans une grande fenêtre (« Preparation · Edit ») depuis la colonne de réglages ; il y migrera en 019.
- Les choix de l'utilisateur (`Choices`) voyagent dans le corps JSON de `POST /runs` et de `POST /preparation` (aperçu) ; ils sont validés côté serveur et enregistrés dans le run (reproductibilité).
- Le serveur renvoie pour chaque colonne la valeur automatique, la valeur appliquée, les options possibles et, pour chaque option impossible, la raison : aucune règle dans le frontend.
- Aucune dépendance ajoutée : KNN / iterative imputer, sélecteurs, RFE, permutation viennent de scikit-learn ; sur- / sous-échantillonnage aléatoires écrits à la main (pas d'imbalanced-learn, pas de SMOTE).
- KNN imputer : les voisins sont cherchés parmi 5 000 lignes d'apprentissage au plus ; iterative imputer ajusté sur 20 000 lignes au plus (temps de réponse). L'indicateur « was missing » n'est pas disponible avec ces deux imputations (dit dans le « Why »).
- Suppression des lignes aberrantes : lignes d'apprentissage avec une valeur au-delà de 3 IQR (aberrantes extrêmes), jamais le test.
- Sélection statistique : ajustée dans le pipeline après la préparation, sur un échantillon de 20 000 lignes d'apprentissage au plus pour les méthodes coûteuses (information mutuelle, RFE, permutation).

## Tâches

- [x] T1 — `Choices` (globaux + par colonne) dans `domain/ml/preparation.py` ; `decide()` applique les règles puis les choix ; valeurs auto, options et raisons d'incompatibilité par colonne ; choix incompatible → valeur auto + avertissement.
- [x] T2 — Réglages globaux branchés : imputation numérique par défaut (auto · mean · median · constant · KNN · iterative), seuil de l'indicateur, modalités rares, limite du one-hot, lissage du target encoding.
- [x] T3 — Aberrantes : écrêtage percentiles 1–99, écrêtage IQR, suppression des lignes d'apprentissage.
- [x] T4 — Sélection statistique : variance, corrélation, VIF, information mutuelle, test univarié, L1, RFE (validation croisée), permutation ; nombre de variables gardées par méthode.
- [x] T5 — Déséquilibre (R-IMB-01/02/03) : auto · aucun · poids · sur- / sous-échantillonnage (apprentissage seulement), répartition avant / après.
- [x] T6 — `train()` reçoit les choix ; le run les enregistre ; noms des entrées après sélection.
- [x] T7 — `POST /modules/ml/datasets/{id}/preparation` : décisions + aperçu (20 premières lignes d'apprentissage préparées) + nombre d'entrées.
- [x] T8 — Tests : règles × choix, incompatibilités, globaux, aberrantes, sélection, déséquilibre, aperçu = `fit(train).transform(train)[:20]`, pas de fuite (statistiques ajustées sur l'apprentissage), API.
- [x] T9 — Frontend : fenêtre « Preparation » (Automatic / Custom, Reset all, onglets Columns · Selection · Missing & outliers · Imbalance · Preview), menus « Auto: … », point + Reset sur un choix, colonnes exclues en bas, confirmation pour une fuite suspectée ; « Train » envoie les choix.
- [x] T10 — Docs : `docs/pages/11`, guide (« How data is prepared »), PLAN, BACKEND_SCHEMA si besoin.
- [x] T11 — Vérifications (tests, lint, typecheck), contrôle dans le navigateur, commit local.

## Écarts

- R-NUM-11 (pourcentages ÷ 100), R-NUM-12 (lat / lon), R-DATE-04/05 (rôles mois / année), R-TGT (log de la cible), texte libre et interactions : non faits ici ; repris avec 019 (catalogue) où ils deviennent utiles.
- La part de vides de chaque colonne est renvoyée avec sa décision : la case « was missing » n'apparaît que pour les colonnes qui ont des vides.
