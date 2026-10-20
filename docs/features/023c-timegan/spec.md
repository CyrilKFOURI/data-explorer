# 023c — Données synthétiques : séquences avec TimeGAN

Suite de la [023](../023-donnees-synthetiques/spec.md) et de la [023b](../023b-modeles-profonds/spec.md). Page : [13-donnees-synthetiques.md](../../pages/13-donnees-synthetiques.md).

## Objectif

Les méthodes de la 023 et de la 023b génèrent des **lignes indépendantes** : l'ordre dans le temps et les historiques par entité (un magasin jour après jour, un client achat après achat) sont perdus. **TimeGAN** (Yoon, Jarrett, van der Schaar, NeurIPS 2019) apprend des **séquences** : leur dynamique, l'autocorrélation et les liens entre colonnes au fil du temps. Le modèle est codé dans le projet à partir de l'article, en PyTorch (extra `deep`), sur le GPU quand il est prêt.

## User stories

1. Sur un dataset avec une date, je choisis **TimeGAN**. La page propose automatiquement :
   - la colonne de temps ;
   - la colonne d'entité, s'il y en a une ;
   - la longueur des séquences ;
   - le nombre de séquences à produire.
   Chaque choix a sa raison.
2. Je génère : la barre suit les trois phases de l'article (autoencodeur, supervision, entraînement adverse).
3. Le rapport habituel s'affiche, plus un onglet **Sequences** :
   - des séquences réelles et synthétiques superposées ;
   - l'autocorrélation comparée colonne par colonne ;
   - le score discriminant et le score prédictif de l'article.
4. **Save as dataset** donne une table normale : une ligne par pas de temps, avec une entité régénérée et des dates.

## 1. Préparation automatique des séquences

| Id | Choix | Règle par défaut |
|---|---|---|
| R-SEQ-01 | Colonne de temps | la première colonne date modélisée ; sans date, TimeGAN est désactivé (« Needs a date column ») |
| R-SEQ-02 | Colonne d'entité | une catégorie ou un identifiant qui revient plusieurs fois et donne au moins 2 séquences d'au moins 8 pas, en préférant le plus de séquences de longueur régulière (ex. `store`) ; sinon aucune : une seule longue série, découpée en fenêtres |
| R-SEQ-03 | Pas de temps | l'écart médian entre deux dates d'une même entité (« daily », « weekly », « monthly » ou une durée) ; les pas manquants ne sont pas comblés |
| R-SEQ-04 | Longueur des séquences | 24, ou l'historique le plus court s'il est plus court (au moins 8, au plus 100) |
| R-SEQ-05 | Fenêtres d'apprentissage | toutes les fenêtres glissantes de cette longueur, dans chaque historique trié par date (comme l'article) ; au plus 20 000 fenêtres, tirées de façon reproductible |
| R-SEQ-06 | Colonnes apprises | les nombres (ramenés entre 0 et 1, selon les bornes réelles) et les catégories (en one-hot ; jusqu'à 20 modalités, au-delà « Other ») ; les vides sont remplacés par la médiane, avec un indicateur « empty » par colonne qui en a ; la colonne de temps et l'entité ne sont pas apprises comme valeurs |
| R-SEQ-07 | Nombre de séquences générées | autant que d'entités réelles, sinon autant que de fenêtres sans chevauchement ; de 1 à 10 000 |

Tout se change dans la barre de réglages (groupe « Sequences »).

## 2. Le modèle (d'après l'article)

**Cinq réseaux GRU** (3 couches, dimension cachée 24 ou nombre de colonnes × 2, dimension la plus grande des deux, au plus 64) :
- **embedder** : séquence réelle → séquence latente ;
- **recovery** : séquence latente → séquence réelle (sigmoïde) ;
- **generator** : bruit uniforme (séquence) → séquence latente ;
- **supervisor** : latent au temps t → latent au temps t + 1 ;
- **discriminator** : séquence latente → réel ou synthétique, à chaque pas.

**Trois phases**, chacune avec le même nombre de pas :
1. **Autoencodeur** : perte 10·√MSE(X, X̃).
2. **Supervision** : MSE(H_{t+1}, S(H)_t), qui apprend la dynamique.
3. **Entraînement conjoint** : à chaque pas, 2 mises à jour du générateur et 1 du discriminateur.
   - générateur : pertes adverses (sur Ê supervisé, γ = 1, et sur E), plus 100·√supervision, plus 100 × écarts de moyenne et d'écart-type (moments) ;
   - embedder : 10·√reconstruction + 0,1 × supervision ;
   - discriminateur : mis à jour seulement si sa perte dépasse 0,15.

**Optimisation** : Adam (lr 10⁻³), lots de 128 fenêtres.

**Budget automatique** : sur le GPU, 1 000 pas par phase, soit environ 2 minutes ; sur le CPU, 150, avec une note qui prévient que le résultat sera grossier (les GRU y sont environ 5 fois plus lents). Modifiable de 100 à 20 000 (« Steps »). L'article utilise 50 000 itérations, ce qui donnerait des heures sur un portable.

**Génération** :
- N séquences de bruit → generator → supervisor → recovery ;
- colonnes reconverties dans leurs unités, bornées, arrondies comme ailleurs ;
- catégories et vides tirés selon les sorties ;
- chaque séquence reçoit une **nouvelle entité** au format des vraies, jamais une vraie valeur ;
- elle reçoit aussi des **dates** : un départ tiré parmi les dates réelles, puis le pas de temps ;
- sans entité, les séquences sont **chaînées** bout à bout en une seule série, et repartent du début si elles dépassent la période réelle ;
- si les dates se répètent sans entité, la page avertit que les lignes d'une même date se suivent dans l'ordre du fichier.

## 3. Évaluation des séquences (onglet « Sequences »)

Le rapport habituel (Diagnostic, Quality, Detection, Privacy, colonnes, liens) s'applique aux lignes générées. S'y ajoutent :
- **Autocorrelation similarity** :
  - pour chaque colonne numérique, l'autocorrélation moyenne des séquences réelles et synthétiques aux retards 1 à min(10, longueur − 1) ;
  - score = 1 − moyenne des |écarts| (au moins 0 ; 1 = même dynamique) ;
  - courbes superposées par colonne.
- **Discriminative score** (article) :
  - un petit GRU (2 couches) apprend à distinguer les fenêtres réelles des synthétiques, sur 80 % des fenêtres de chaque côté ;
  - le score est son exactitude sur les 20 % restants, présenté comme 1 − 2 × |exactitude − 0,5| (100 % = indiscernables, même convention que Detection).
- **Predictive score** (article, TSTR / TRTR) :
  - un petit GRU prédit le pas suivant de chaque colonne à partir des précédents ;
  - deux entraînements, sur les fenêtres synthétiques et sur les fenêtres réelles d'apprentissage, testés tous les deux sur les fenêtres des lignes réelles tenues à l'écart (MAE) ;
  - rapport « The synthetic sequences keep 91 % of the real predictive power » ;
  - les lignes tenues à l'écart sont des entités entières (20 %) quand il y a une entité, sinon la fin de la série.
- **Séquences superposées** : 5 séquences réelles et 5 synthétiques par colonne numérique (réel gris plein, synthétique accent pointillé), au choix de la colonne.
- **Lecture** : une phrase pour chaque score, et le rappel que TimeGAN apprend des fenêtres de longueur fixe (pas les tendances plus longues).

## API

- `POST …/runs` accepte :
  - `method: "timegan"` ;
  - `sequence: {time, entity, length, sequences, steps}`, chaque champ facultatif (Auto).
- `GET …/plan` :
  - la méthode `timegan` porte `available` et sa raison ;
  - le plan donne `sequence_plan` : colonne de temps, candidates d'entité avec raison, pas de temps, longueur et nombre de séquences proposés.
- Le job expose la phase et la progression (« Autoencoder · step 400 / 2 000 »).
- Le rapport porte `sequences` (scores, autocorrélations, séquences d'exemple) quand la méthode est TimeGAN.

## Code

- `backend/app/domain/synthetic/sequences.py` : plan R-SEQ, fenêtres, aller-retour, métriques (autocorrélation, discriminant, prédictif) ;
- `backend/app/domain/synthetic/deep/timegan.py` : le modèle ;
- intégration dans `generate.py` : une branche séquences, puisque le temps et l'entité ne sont pas des colonnes comme les autres.

## Critères d'acceptation

- GIVEN `sales_timeseries` WHEN je choisis TimeGAN THEN le temps vaut `date`, l'entité `store` (3 séquences de 1 095 jours), le pas « daily », la longueur 24, et 3 séquences sont proposées.
- GIVEN un dataset sans date THEN TimeGAN est désactivé avec « Needs a date column ».
- GIVEN une série sinusoïdale bruitée (période 12) THEN après un entraînement court en test :
  - l'autocorrélation synthétique au retard 1 est positive et celle au retard 6 négative, comme le réel ;
  - l'Autocorrelation similarity dépasse 0,8.
- GIVEN une génération TimeGAN THEN chaque entité synthétique est nouvelle, a exactement `length` lignes, des dates croissantes au pas réel ; le Diagnostic vaut 100 %.
- GIVEN un jeu synthétique = des fenêtres réelles recopiées THEN le Discriminative score est proche de 100 %.
- GIVEN la même graine sur le CPU THEN la même séquence est produite.
- GIVEN l'annulation pendant une phase THEN le job s'arrête au pas suivant et rien n'est enregistré.
- **Performance** (test lent, GPU) : `sales_timeseries`, budget Auto, en moins de 3 minutes.

## Hors scope

- Séquences de longueur variable, et prolonger une séquence au-delà de la longueur apprise.
- Contraintes entre entités (somme des magasins = total).
- Séries irrégulières : le pas médian est utilisé et les trous ne sont pas modélisés.
