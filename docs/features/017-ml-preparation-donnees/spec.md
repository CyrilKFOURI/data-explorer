# 017 — Machine learning : préparation des données automatique et modifiable

## Objectif

Préparer les données **sans que l'utilisateur ait à y penser** — imputation, encodage, transformation, mise à l'échelle, sélection de variables, déséquilibre des classes — par un **moteur de règles explicites**, décidées à partir du **type détecté** de chaque colonne, de ses **statistiques** et du **profil du modèle** choisi. Puis permettre de **tout changer**, colonne par colonne ou globalement, dans un éditeur simple qui dit toujours *quelle règle* a décidé et *pourquoi*.

C'est ce qui distingue l'app des consoles ML génériques : la préparation n'est ni cachée ni laissée à l'utilisateur ; elle est **décidée comme le ferait un data scientist**, et **justifiée**. Références : [11-machine-learning.md](../../pages/11-machine-learning.md), [COLUMN_DETECTION.md](../../COLUMN_DETECTION.md), [DATES.md](../../DATES.md).

## Principes

1. **Par défaut, rien à faire.** La préparation s'applique toute seule ; une ligne la résume dans la colonne Réglages : « Preparation · Automatic · 18 columns → 41 model inputs · Edit ».
2. **Chaque décision est une règle nommée**, déterministe et testée (`R-NUM-03 : skewness > 1 and all values ≥ 0 → log1p`). L'infobulle « Why » d'une cellule affiche la règle et les chiffres qui l'ont déclenchée.
3. **Deux entrées décident** : le *profil de la colonne* (type validé, rôle, statistiques) et le *profil du modèle* (a-t-il besoin d'une échelle commune ? gère-t-il les vides ? les catégories ?). Changer de modèle recalcule les choix automatiques ; les choix manuels sont conservés.
4. **Jamais de fuite.** Tout ce qui apprend quelque chose des données (médiane, quantiles, encodage de cible, sélection) est ajusté **sur l'apprentissage seulement**, dans le pipeline, pli par pli en validation croisée.
5. **Le résultat se vérifie.** Un aperçu montre les premières lignes de la matrice réellement donnée au modèle.

## Profil du modèle

Chaque modèle du catalogue ([019](../019-ml-catalogue-modeles/spec.md)) déclare ses besoins ; les règles s'en servent.

| Drapeau | Sens | Exemples |
|---|---|---|
| `needs_scaling` | sensible à l'échelle des variables | linéaires régularisés, logistique, SVM, KNN, MLP, SGD |
| `handles_missing` | accepte les vides nativement | XGBoost, LightGBM, CatBoost, HistGradientBoosting |
| `native_categorical` | accepte les catégories sans encodage | XGBoost, LightGBM, CatBoost, HistGradientBoosting |
| `sensitive_to_skew` | bénéficie d'une variable symétrique | linéaires, logistique, LDA/QDA, KNN, SVM, MLP, Gaussian NB |
| `sensitive_to_collinearity` | coefficients instables si variables liées | régression linéaire non régularisée, logistique sans pénalité, LDA |
| `distance_based` | repose sur des distances | KNN, SVM à noyau, Gaussian process |
| `nonnegative_inputs` | exige des entrées ≥ 0 | Multinomial / Complement NB |
| `tree_based` | invariant aux transformations monotones | arbres, forêts, boosting |

## Profil de la colonne

Calculé une fois (réutilise les résumés de la page Colonnes et de la fiche variable) : type validé, rôle, % de vides, nombre de modalités et part de la plus rare, asymétrie (skewness), aplatissement (kurtosis), part de valeurs aberrantes (règle IQR 1,5), signe des valeurs (toutes ≥ 0 ? toutes > 0 ?), constance, ordre (ordinal), granularité (date).

## Étapes du pipeline (dans cet ordre)

1. **Lignes** — retirer les lignes sans cible ; option : retirer les doublons exacts (désactivée par défaut, sauf si > 1 % de doublons : suggérée).
2. **Sélection des colonnes** — exclusions par règle (ci-dessous), puis sélection statistique optionnelle.
3. **Valeurs manquantes** — imputation et indicateurs.
4. **Valeurs aberrantes** — aucune action par défaut ; options de traitement.
5. **Transformations** — symétrisation, dates, texte.
6. **Encodage** — catégories et booléens.
7. **Mise à l'échelle**.
8. **Interactions** (optionnel).
9. **Déséquilibre des classes** (classification).
10. **Transformation de la cible** (régression).

## Règles par défaut

### Sélection des colonnes (étape 2)

| Règle | Condition | Décision |
|---|---|---|
| R-SEL-01 | colonne = cible, ou colonne source d'une cible en classes (018) | exclue |
| R-SEL-02 | type identifiant ; ou catégorie avec > 50 % de valeurs distinctes ou > 100 modalités | exclue · « behaves like an identifier » |
| R-SEL-03 | texte libre | exclue (options texte, étape 5) |
| R-SEL-04 | constante, ou modalité dominante > 99 % | exclue · « almost always the same value » |
| R-SEL-05 | > 80 % de vides | exclue · « 92 % empty » |
| R-SEL-06 | fuite suspectée : \|r\| ≥ 0,98 ou V de Cramér ≥ 0,98 avec la cible, ou une modalité prédit la classe à 100 % sur > 5 % des lignes | exclue · « looks like it contains the answer » (bien visible) |
| R-SEL-07 | paire de numériques (ou de dates, prises comme du temps) avec \|r\| > 0,95 et modèle `sensitive_to_collinearity` | la colonne la moins liée à la cible est exclue · « nearly duplicates mileage » |
| R-SEL-08 | colonne ignorée dans la page Colonnes | exclue |

**Sélection statistique** (désactivée par défaut, au choix dans l'éditeur) : seuil de variance ; filtre de corrélation (seuil réglable) ; **VIF** > seuil (10) itératif ; information mutuelle (garder les k meilleures ou un % ) ; test univarié (F de Fisher / χ²) ; sélection par régularisation L1 ; **RFE** (élimination récursive) avec validation croisée ; importance par permutation (garder celles qui dégradent le score). Toute sélection statistique est ajustée dans le pipeline (sur l'apprentissage).

### Numériques — continues et discrètes (étapes 3 à 7)

| Règle | Condition | Décision |
|---|---|---|
| R-NUM-01 | modèle `handles_missing` | pas d'imputation (« handled natively by XGBoost ») |
| R-NUM-02 | sinon, \|skewness\| ≤ 0,5 | imputation par la **moyenne** |
| R-NUM-03 | sinon | imputation par la **médiane** |
| R-NUM-04 | vides > 5 % et modèle sans `handles_missing` | + indicateur `col_was_missing` (le fait d'être vide est souvent informatif) |
| R-NUM-05 | modèle `sensitive_to_skew`, skewness > 1, toutes valeurs ≥ 0 | **log1p** |
| R-NUM-06 | modèle `sensitive_to_skew`, \|skewness\| > 1, valeurs de signe quelconque | **Yeo-Johnson** |
| R-NUM-07 | modèle `needs_scaling`, part d'aberrantes (IQR) > 5 % | **RobustScaler** (médiane / IQR) |
| R-NUM-08 | modèle `needs_scaling`, sinon | **StandardScaler** |
| R-NUM-09 | modèle `nonnegative_inputs` | **MinMaxScaler** [0, 1] après imputation |
| R-NUM-10 | modèle `tree_based` | aucune transformation ni échelle |
| R-NUM-11 | rôle `percentage` en 0–100 | divisé par 100 avant échelle (lisibilité des coefficients) |
| R-NUM-12 | rôle `latitude` / `longitude` | gardées brutes pour les arbres ; standardisées sinon ; option « distance to centre » |
| R-NUM-13 | réglage global « imputation numérique » ≠ auto | cette stratégie (mean · median · 0 · KNN · iterative) ; pas d'indicateur avec KNN / iterative |

Valeurs aberrantes : **aucune action par défaut** (les supprimer biaise souvent le modèle) ; options : écrêtage aux percentiles (1–99 par défaut), écrêtage IQR, suppression des lignes (apprentissage seulement, jamais le test).

### Booléens

| Règle | Décision |
|---|---|
| R-BOOL-01 | encodés 0 / 1 |
| R-BOOL-02 | vides : modalité « Missing » (donc deux indicateurs) si vides > 5 %, sinon la valeur la plus fréquente ; rien pour `handles_missing` |

### Catégories nominales

| Règle | Condition | Décision |
|---|---|---|
| R-CAT-01 | toujours | vides = modalité **« Missing »** ; modalités rares (< 1 % **et** < 10 lignes, sur l'apprentissage) regroupées en **« Other »** ; modalité inconnue à la prédiction → « Other » |
| R-CAT-02 | 2 modalités | une colonne 0 / 1 |
| R-CAT-03 | modèle `native_categorical` | passée en catégorie native (pas d'encodage) |
| R-CAT-04 | modèle `tree_based` sans catégories natives (arbre, forêt, Extra trees) | **encodage ordinal** (ordre arbitraire mais stable) jusqu'à 50 modalités ; au-delà, **target encoding** |
| R-CAT-05 | autres modèles, ≤ 15 modalités | **one-hot** ; la première modalité est retirée seulement pour les modèles linéaires **non régularisés** (piège des variables muettes) |
| R-CAT-06 | autres modèles, 16 à 100 modalités | **target encoding** croisé (5 plis sur l'apprentissage, lissage m = 10) ; en multiclasse, une colonne par classe |
| R-CAT-07 | modèle `nonnegative_inputs` | one-hot (jamais de target encoding, qui peut être négatif en régression) |

### Catégories ordinales

| Règle | Décision |
|---|---|
| R-ORD-01 | **encodage ordinal selon l'ordre validé** dans la page Colonnes (0 … k−1), pour tous les modèles ; mis à l'échelle comme une numérique si `needs_scaling` |
| R-ORD-02 | ordre absent → traitée comme nominale, avec un avertissement « set the order in Columns to use it » |

### Dates et parties de date

| Règle | Condition | Décision |
|---|---|---|
| R-DATE-01 | toujours | la date brute est remplacée par : année, mois, jour du mois, jour de semaine, week-end (0/1), heure (si date-heure, et si l'heure varie), **jours depuis le début** (numérique) ; seules les parties qui varient dans les données sont gardées |
| R-DATE-02 | modèle `tree_based` | parties cycliques en entiers |
| R-DATE-03 | autres modèles | mois, jour de semaine et heure en **sin / cos** (décembre est proche de janvier) |
| R-DATE-04 | colonnes à rôle `month`, `weekday` | mêmes règles que les parties de date |
| R-DATE-05 | rôle `year` | numérique |

### Texte libre (options, désactivées par défaut)

Longueur, nombre de mots, présence de chiffres ; **TF-IDF** (200 termes au plus, mots vides anglais retirés) pour les modèles linéaires et Naive Bayes.

### Interactions (option, modèles linéaires)

Polynômes de degré 2 ou 3 sur les numériques (interactions seules ou complètes), avec avertissement au-delà de 200 entrées produites.

### Déséquilibre des classes (étape 9)

| Règle | Condition | Décision |
|---|---|---|
| R-IMB-01 | classe minoritaire ≥ 20 % | rien |
| R-IMB-02 | sinon, modèle acceptant des poids | **poids de classes équilibrés** (`class_weight="balanced"`, `scale_pos_weight`, poids d'échantillon) |
| R-IMB-03 | sinon | rien, avec avertissement et métrique principale = balanced accuracy |

Options : aucun · poids · sur-échantillonnage aléatoire · sous-échantillonnage aléatoire (appliqués à l'apprentissage uniquement, jamais au test). SMOTE n'est pas proposé (dépendance `imbalanced-learn`, à reconsidérer).

### Cible (régression, étape 10)

| Règle | Condition | Décision |
|---|---|---|
| R-TGT-01 | skewness de la cible > 1, toutes valeurs > 0, modèle non `tree_based` | **log de la cible suggéré** (pas appliqué d'office : bandeau « Price is skewed — predicting its log usually helps. [Apply] ») |
| R-TGT-02 | log appliqué | prédictions retransformées ; métriques toujours calculées **dans l'unité d'origine** |

## Éditeur (« Preparation · Edit »)

S'ouvre dans le tiroir **Settings** (onglet **Preparation**, voir [019](../019-ml-catalogue-modeles/spec.md)), sans quitter les résultats.

```
Preparation                                    [Automatic ◉ | Custom ○]   Reset all
"18 columns → 41 model inputs · 3 excluded · 2 log-transformed · 5 one-hot · weights for imbalance"

[ Columns ] [ Selection ] [ Missing & outliers ] [ Imbalance ] [ Preview ]

Column        Use   Missing        Transform     Encoding        Scaling
mileage  #    ☑    Auto: median   Auto: log1p   —               Auto: robust      ⓘ
fuel     ◇    ☑    Auto: Missing  —             Auto: one-hot   —                 ⓘ
segment  ≡    ☑    Auto: Missing  —             Auto: ordinal   Auto: standard    ⓘ
vin      ⌗    ☐    excluded · behaves like an identifier                          ⓘ
```

- **Columns** : une ligne par colonne, cellules = petits menus. Une valeur automatique s'affiche en gris « Auto: median » ; une valeur choisie s'affiche en encre normale avec un point et « Reset ». Les colonnes exclues sont en bas, grisées, avec leur raison, et se réactivent d'un clic (la fuite de cible demande une confirmation).
- **Selection** : méthodes de sélection statistique (cases à cocher, chacune avec son seuil) et le nombre de variables qu'elles gardent.
- **Missing & outliers** : réglages globaux — stratégie d'imputation numérique par défaut (auto · mean · median · constant · KNN imputer · iterative imputer), seuil de l'indicateur de vide (5 %), seuil des modalités rares (1 % / 10 lignes), limite du one-hot (15), lissage du target encoding (10), traitement des aberrantes.
- **Imbalance** : stratégie (auto · aucun · poids · sur- / sous-échantillonnage), avec la répartition des classes avant / après.
- **Preview** : les 20 premières lignes d'apprentissage **après** préparation (noms des colonnes produites : `fuel=diesel`, `order_date_month_sin`…), avec le nombre total d'entrées du modèle.
- **Automatic / Custom** : « Automatic » (défaut) applique les règles ; dès qu'un choix est modifié, le mode passe en « Custom » ; « Reset all » revient à « Automatic ».
- **Choix incompatibles** : désactivés avec la raison (« No imputation: this model cannot handle missing values ») ; quand un changement de modèle rend un choix manuel incompatible, il est remplacé par le choix automatique et un bandeau le signale.

## Critères d'acceptation

- **Moteur** : `domain/ml/preparation/` — chaque règle est une fonction pure (profil colonne × profil modèle → décision + explication), avec son identifiant ; le pipeline scikit-learn (`ColumnTransformer`) est construit à partir des décisions. Aucune règle n'est codée dans le frontend.
- **Tests par règle** : GIVEN une colonne asymétrique positive (skewness 2,4) WHEN modèle linéaire THEN log1p (R-NUM-05) ; WHEN XGBoost THEN aucune transformation (R-NUM-10) ; GIVEN 30 modalités WHEN logistique THEN target encoding croisé (R-CAT-06) ; WHEN Random forest THEN ordinal (R-CAT-04) ; GIVEN une colonne ordinale avec ordre validé THEN codes dans cet ordre (R-ORD-01) ; GIVEN `order_date` WHEN SVM THEN mois et jour de semaine en sin/cos (R-DATE-03).
- **Pas de fuite** : GIVEN un target encoding THEN les valeurs d'une ligne d'apprentissage sont calculées sans sa propre cible (plis croisés) ; GIVEN une validation croisée THEN imputation, échelle et sélection sont réajustées dans chaque pli (test : statistiques différentes d'un pli à l'autre).
- **Reproductibilité** : la préparation (décisions + choix manuels) est enregistrée dans le run ; relancer un run donne les mêmes entrées.
- **Explications** : chaque décision automatique a un texte « Why » avec les chiffres (« skewness 2.4 > 1 and all values ≥ 0 »).
- **Aperçu** : GIVEN la préparation courante THEN l'aperçu égale `pipeline.fit(train).transform(train)[:20]`.
- **Performance** : construction des décisions < 200 ms pour 200 colonnes ; aperçu < 2 s sur 200 000 lignes.
- **Documentation** : toutes les règles listées dans le guide utilisateur (section « How data is prepared »), en langage simple.

## Hors scope

SMOTE et variantes, imputation par modèle génératif, plongements (embeddings) de texte, génération automatique de variables (feature engineering automatique au-delà des règles ci-dessus).
