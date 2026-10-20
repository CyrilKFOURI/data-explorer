# 023b — Données synthétiques : modèles profonds (CTGAN, TVAE) et GPU

Suite de la [023](../023-donnees-synthetiques/spec.md). Page : [13-donnees-synthetiques.md](../../pages/13-donnees-synthetiques.md).

## Objectif

Ajouter deux générateurs par réseaux de neurones, **CTGAN** et **TVAE** (Xu et al., *Modeling Tabular Data using Conditional GAN*, NeurIPS 2019). Ils captent des distributions multimodales et des liens que les méthodes de la 023 ratent. L'entraînement **utilise la carte graphique** quand elle est prête et que l'utilisateur le permet.

## Décisions (2026-10-20)

- **Le paquet `ctgan` n'est pas utilisé.** Il est passé sous licence BUSL-1.1, comme sa dépendance `rdt` et SDV, ce qui est incompatible avec un projet MIT. Les deux modèles sont **codés dans le projet à partir de l'article**, sans reprendre le code BUSL.
- **Seule dépendance ajoutée : PyTorch**, compilé pour CUDA 13.0 (pilote ≥ 580), dans l'extra optionnel `deep` (`uv sync --extra deep`).
  - Sans PyTorch, les deux méthodes restent listées, mais désactivées avec la raison « Needs the deep extra (PyTorch) ».
  - L'image Docker par défaut reste sans PyTorch.
- **TimeGAN est reporté en 023c.** Il génère des **séquences** (une colonne d'entité, l'ordre dans le temps), ce qui demande une préparation et une page à part.

## Principe

Mêmes règles que la 023 :
- même plan des colonnes (règles R-SYN), mêmes identifiants régénérés et colonnes laissées de côté ;
- même rapport (Diagnostic, Quality, Detection, Privacy, comparaison, utilité) ;
- même protection « Drop copies of real rows ».

Seule la méthode change.

## 1. Préparation des colonnes (« mode-specific normalization »)

- **Nombre ou date** (en secondes) :
  - un mélange gaussien bayésien (scikit-learn, 10 composantes au plus, a priori de concentration 0,001) trouve les modes de la colonne ;
  - les composantes de poids < 0,005 sont ignorées ;
  - chaque valeur est codée par **un mode** (one-hot, tiré selon sa probabilité d'appartenance) et **un scalaire** α = (x − μ_mode) / (4 σ_mode), borné à [−0,99 ; 0,99] ;
  - **valeur vide** : un mode « empty » de plus, avec α = 0. Ajout par rapport à l'article, qui ne traite pas les vides.
- **Catégorie, booléen, ordinal** : one-hot, le vide étant une modalité.
- **Retour** : le mode le plus probable, puis x = α · 4 σ + μ, ramené aux bornes réelles, arrondi aux décimales (entiers, jours) par le même décodage que la 023.

## 2. CTGAN

- **Vecteur conditionnel et « training-by-sampling »** :
  - à chaque ligne d'un lot, une colonne discrète (catégorie ou mode d'un nombre) est tirée au hasard, puis une modalité selon le **log** de sa fréquence ;
  - une vraie ligne ayant cette modalité est tirée en face.
  - Les modalités rares sont ainsi apprises.
- **Générateur** :
  - bruit (128) et vecteur conditionnel en entrée ;
  - 2 blocs résiduels (linéaire 256, normalisation de lot, ReLU, concaténation) ;
  - sorties : tanh pour les α, Gumbel-softmax (τ = 0,2) pour les modes et les modalités.
- **Critique** : PacGAN (10 lignes jugées ensemble), 2 couches linéaires de 256 (LeakyReLU 0,2, dropout 0,5).
- **Perte** :
  - WGAN-GP (pénalité de gradient λ = 10) ;
  - plus une entropie croisée qui force le générateur à respecter la condition.
- **Optimisation** : Adam (lr 2·10⁻⁴, β = (0,5 ; 0,9), décroissance des poids 10⁻⁶), lots de 500.
- **Génération** : vecteurs conditionnels tirés selon les fréquences réelles (pas le log), donc les bonnes proportions.

## 3. TVAE

- **Encodeur** : 2 couches de 128 (ReLU), puis moyenne et log-variance (dimension latente 128).
- **Décodeur** : 2 couches de 128, puis α (avec un écart-type appris par colonne) et logits des one-hot.
- **Perte** : reconstruction (erreur quadratique pondérée par l'écart-type appris pour les α, entropie croisée pour les one-hot, facteur 2) plus divergence de Kullback-Leibler.
- **Optimisation** : Adam (lr 10⁻³, décroissance 10⁻⁵), lots de 500.
- **Génération** : tirage dans la loi normale latente, puis décodage.

## 4. Entraînement

- **Époques (Auto)** : 300 comme l'article, sauf si l'entraînement verrait plus de lignes que le budget de l'appareil (époques × lignes). Toujours entre 30 et 300 époques.
  - GPU : 6 millions de lignes, donc 120 époques pour 50 000 lignes (environ 3 minutes sur la RTX 4050).
  - CPU : 1,5 million de lignes, donc 30 époques pour 50 000 lignes et 300 pour 5 000.
- **Lots** : 500 lignes, comme l'article ; 2 000 pour CTGAN sur un GPU, qui traite ainsi deux fois plus de lignes par seconde.
  - Le nombre se change (10 à 1 000).
- **Progression** : la barre suit les époques (« Epoch 120 / 300 · loss … »). L'annulation est vérifiée à chaque époque.
- **Graine** : `torch.manual_seed`. Le résultat est le même sur le CPU ; sur le GPU, il peut varier légèrement, ce qui est indiqué.

## 5. GPU

- **Appareil** :
  - « Auto » utilise le GPU si PyTorch voit CUDA (ou MPS sur Apple) et si **Settings › Compute › Use the GPU** le permet ;
  - sur la page, une pastille à côté de Generate (« GPU · RTX 4050 » ou « CPU ») avec un interrupteur **pour ce run** ; elle est désactivée avec sa raison si aucune carte n'est prête.
- **Repli automatique** : si la carte manque de mémoire (CUDA out of memory), l'entraînement reprend sur le CPU et le run le dit (« GPU ran out of memory: finished on CPU »).
- **Le run enregistre** l'appareil utilisé (nom de la carte ou CPU), les époques et la durée ; la comparaison de runs les montre.
- **Détection** (déjà dans la 023) : avec PyTorch installé, `torch.cuda.is_available()` précise l'état :
  - prête ;
  - « GPU found but this build has no GPU support (CPU PyTorch) » ;
  - pas de carte.

## 6. Méthode recommandée

Sequential CART reste la méthode ★ par défaut : elle est rapide, sans entraînement, et la meilleure sur la plupart des jeux tabulaires de taille moyenne. CTGAN et TVAE portent le badge « Deep · GPU » ou « Deep · CPU (slow) ». Au-delà de 20 000 lignes d'apprentissage avec un GPU prêt, la raison affichée suggère CTGAN pour les distributions multimodales.

## API

- `POST …/runs` accepte :
  - `method: "ctgan" | "tvae"` ;
  - `epochs` (null = Auto) ;
  - `device: "auto" | "cpu" | "gpu"`.
- Le job expose `progress` (0 à 1) et `message` (« Epoch 12 / 300 »).
- `GET …/plan` : chaque méthode porte `available` et `unavailable_reason`. Le plan donne aussi les époques Auto et l'appareil proposé.
- Le run expose `device`, `epochs` et `notes` (repli sur le CPU).

## Code

`backend/app/domain/synthetic/deep/` :
- `device.py` : choix de l'appareil, repli ;
- `transformer.py` : préparation et retour ;
- `sampler.py` : vecteur conditionnel ;
- `ctgan.py`, `tvae.py`.

Tout est importé paresseusement, pour que l'app démarre sans PyTorch.

## Critères d'acceptation

- GIVEN PyTorch absent THEN CTGAN et TVAE sont listés mais désactivés avec la raison, et les tests profonds sont ignorés.
- GIVEN une colonne bimodale (deux pics) THEN la préparation trouve deux modes et le retour redonne les valeurs à 10⁻⁶ près (aller-retour sans entraînement).
- GIVEN une génération CTGAN ou TVAE THEN le Diagnostic vaut 100 % (bornes, modalités, entiers, structure) et le taux de vides de chaque colonne est à ± 5 points.
- GIVEN un jeu avec une modalité à 2 % THEN CTGAN la produit (training-by-sampling).
- GIVEN une colonne bimodale THEN CTGAN et TVAE gardent les deux pics : KSComplement ≥ 0,8 après entraînement court en test.
- GIVEN la même graine sur le CPU THEN le même jeu est produit.
- GIVEN l'annulation pendant l'entraînement THEN le job s'arrête à l'époque suivante et rien n'est enregistré.
- GIVEN un manque de mémoire GPU simulé THEN l'entraînement finit sur le CPU et le run porte la note.
- GIVEN Settings › Use the GPU = Off THEN l'appareil Auto est le CPU.
- **Performance** (test lent, GPU) : 50 000 lignes × 20 colonnes, CTGAN Auto, en moins de 5 minutes sur la RTX 4050.

## Hors scope (023b)

- TimeGAN et les séquences (023c).
- Modèles de diffusion (TabDDPM), confidentialité différentielle (DP-SGD).
- XGBoost et LightGBM sur GPU dans le module ML (le même réglage servira).
