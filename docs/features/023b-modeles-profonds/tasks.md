# 023b — Tâches

Spec : [spec.md](spec.md). Page : [13-donnees-synthetiques.md](../../pages/13-donnees-synthetiques.md).

## Choix de réalisation

- **PyTorch** dans l'extra `deep` de `pyproject.toml`, avec l'index `pytorch-cu130` sous Windows et `pytorch-cpu` sous Linux. Il est importé seulement dans `domain/synthetic/deep/` et seulement à l'appel : l'app démarre sans lui.
- **Même interface que les autres méthodes** : `generate(coded, learned, options, should_stop)` rend des colonnes codées. CTGAN et TVAE partent des colonnes codées de la 023 (nombres, secondes, indices de modalités, NaN) : les bornes, les décimales et les identifiants restent gérés par `generate.py`.
- **Progression** : `Options.progress(fraction, message)` est appelé à chaque époque, et le job le relaie.
- **Appareil** : `Options.device` (« auto », « cpu », « gpu ») et `Options.allow_gpu` (le réglage de l'app). `Fitted.device` donne l'appareil utilisé, et une note signale le repli sur le CPU.

## Tâches

- [x] T1 — Doc de page (méthodes profondes, pastille GPU, progression par époque).
- [x] T2 — Dépendance : extra `deep`, index CUDA 13.0, installation, détection `torch.cuda` dans `gpu.py`.
- [x] T3 — Domaine : `device.py`, `transformer.py` (mélange gaussien par colonne, mode vide), `sampler.py`, `ctgan.py`, `tvae.py` ; enregistrement dans `methods/` et `plan.py` (disponibilité, époques Auto) — tests (ignorés sans PyTorch).
- [x] T4 — Module : requête (`epochs`, `device`), progression du job, appareil et époques dans le run, repli OOM — tests API.
- [x] T5 — Frontend : méthodes désactivées avec leur raison, époques, pastille GPU / CPU avec interrupteur, barre de progression par époque, appareil dans le rapport et la comparaison.
- [x] T6 — Docs (PLAN, USER_GUIDE, BACKEND_SCHEMA si besoin, TRD, README Docker), vérifications, navigateur (GPU réel), commit.

## Découvertes

- **`ctgan` est sous licence BUSL-1.1**, comme `rdt` et SDV. La spec 023 le croyait sous MIT : les deux modèles sont donc codés dans le projet à partir de l'article.
- **TVAE prenait le mode le plus probable** au lieu de le tirer au hasard : 78 % de vides au lieu de 20 %, et un pic d'une distribution bimodale perdu. Il tire maintenant chaque mode et modalité selon les probabilités du décodeur : qualité de 0,67 à 0,95 sur le jeu d'essai.
- **La protection « Drop copies » de la 023 supprimait les lignes banales.** Une ligne « vide, a, 3 » existe forcément dans le réel, donc toutes les lignes à valeur vide disparaissaient. Correction : seules les copies d'une ligne réelle **unique** sont retirées (règle « replicated uniques » de synthpop, appliquée exactement). Le chiffre Privacy suit la même règle ; les copies de lignes quelconques restent affichées pour information.
- **Vitesse sur le GPU (RTX 4050 Laptop)** :
  - un pas de CTGAN prend 23 ms avec des lots de 500 et 51 ms avec des lots de 2 000, soit deux fois plus de lignes par seconde avec 2 000 ;
  - échantillonner sur le GPU et regrouper les activations par taille de bloc n'a gagné que 10 % : la limite est le calcul, pas les copies ;
  - les époques automatiques suivent donc un budget de lignes traitées. Résultat : CTGAN sur 50 000 lignes × 20 colonnes en 170 s (test lent).
- **TVAE sur `sales_timeseries` (GPU, 300 époques)** : 18 s, Quality 97 %, Privacy 100 %, mais Detection 34 %. Le classifieur repère ses valeurs ; CART fait mieux sur ce jeu.
- **CI** : PyTorch CPU sous Linux (`--extra deep`), pour que pyright et les tests profonds y tournent. Le test lent GPU est ignoré sans CUDA.
