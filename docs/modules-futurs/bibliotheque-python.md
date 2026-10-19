# Bibliothèque Python — `pip install` du moteur d'analyse

> **Statut : à planifier, après les modules (dernière étape du projet).** Ce document fixe l'intention dès maintenant (décidé le 2026-10-19), pour que tout le code écrit d'ici là reste réutilisable hors de l'app.

## Objectif

Tout ce que l'app sait faire doit aussi s'utiliser **en Python**, dans un notebook ou un script, sans lancer l'interface :
- le typage automatique des colonnes ;
- le profil d'une variable, les comparaisons et les corrélations avec leurs insights ;
- les séries temporelles, le machine learning, les KPI, les données synthétiques.

L'app devient une interface parmi d'autres sur un même moteur. Une seule base de code : les mêmes calculs, les mêmes règles automatiques et les mêmes verdicts dans l'app et dans la bibliothèque.

## Ce que ça donnerait

```python
import dataexplorer as dx            # nom provisoire, disponibilité PyPI à vérifier

ds = dx.load("sales.csv")            # import + typage automatique (même détection que l'app)
ds.columns                           # types, rôles, confiance, raisons
ds.filter("country in ['FR', 'DE']") # mêmes filtres que la barre de l'app

ds.profile("revenue")                # fiche variable : describe, normalité, lois, aberrants
ds.compare("revenue", "country")     # tests bivariés avec verdict
ds.correlations().insights           # matrice + phrases d'insight

ts = ds.timeseries(time="date", value="revenue")
ts.stationarity(); ts.decompose(); ts.forecast(horizon=12)

run = ds.ml.train(target="churned")  # préparation automatique (règles R-*) + modèle recommandé
run.metrics; run.explain(); run.predict(new_rows)

kpi = ds.kpi("sum:revenue", time="date", split="country")
kpi.table(show_as="share_total"); kpi.chart()

syn = ds.synthesize(method="cart", rows=10_000)
syn.fidelity.score; syn.privacy.verdict; syn.to_parquet("synthetic.parquet")

dx.app(port=8000)                    # ouvre l'interface sur les mêmes données
```

**Résultats :**
- les mêmes dataclasses que l'API, avec `.to_dict()` et `.to_frame()` (pandas, optionnel) ;
- un affichage riche dans Jupyter (`_repr_html_` : verdict, tableau, graphique) ;
- `.plot()` qui rend la même figure plotly que l'app, avec les mêmes règles dataviz.

## Paquet et dépendances (extras pip)

| Installation | Contenu |
|---|---|
| `pip install dataexplorer` | cœur : DuckDB, pyarrow, numpy, scipy, typage, profils, comparaisons, corrélations, KPI |
| `[timeseries]` | statsmodels, arch |
| `[ml]` | scikit-learn, xgboost, lightgbm, optuna |
| `[synthetic]` | données synthétiques sans PyTorch (023) |
| `[deep]` | PyTorch, ctgan (CTGAN, TVAE, TimeGAN, 023b ; GPU détecté comme dans l'app) |
| `[app]` | FastAPI, uvicorn et l'interface déjà construite, embarquée dans la roue ; commande `dataexplorer app` |
| `[all]` | tout |

## Ce que ça demande à l'architecture

1. **Séparer le moteur de l'app.**
   - Un paquet `dataexplorer/` avec les calculs, les règles et le typage.
   - L'app (`backend/app/`) garde FastAPI, l'espace de travail SQLite, les jobs et le cache, et appelle le moteur.
   - Aujourd'hui, `backend/app/domain/` est déjà presque ce moteur ; seuls les services qui lisent ou écrivent SQLite (colonnes, datasets, filtres enregistrés, réglages) restent côté app.
2. **Un objet `Dataset` en mémoire** pour la bibliothèque : chemin Parquet ou relation DuckDB, plus les colonnes typées. Pas de base SQLite obligatoire. Les corrections de types se font en code (`ds.set_type("zip", "categorical_nominal")`).
3. **Les mêmes tests** couvrent les deux usages ; les tests d'API restent dans l'app.
4. **La documentation de l'API** est générée depuis les docstrings (mkdocs + mkdocstrings), avec des exemples exécutés en intégration continue.
5. **Publication sur PyPI** (trusted publishing depuis GitHub) et versionnement sémantique. À faire seulement avec l'accord explicite de l'utilisateur, car c'est une publication publique.

## Règle à appliquer dès maintenant

Voir [ARCHITECTURE.md](../ARCHITECTURE.md), « Règles de dépendance » : tout nouveau calcul de `domain/`
- prend des entrées simples (connexion DuckDB et relation, ou tableaux, plus des descriptions de colonnes) ;
- rend des dataclasses ;
- ne dépend ni de FastAPI, ni de SQLite, ni des services de l'app.

Les modules KPI (022) et Données synthétiques (023) respectent déjà cette forme (`domain/kpi/compute.py` reçoit une connexion, une source et des colonnes).

## Hors scope

- Réécrire les calculs dans un autre langage.
- Une API web publique hébergée.
- La compatibilité avec des versions de Python antérieures à celle de l'app.
