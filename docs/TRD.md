# TRD — Technical Requirements

> Statut : **proposition**, à valider pendant l'interview (la stack surtout).

## Stack

Application **locale** : un serveur Python sur la machine et une interface web ouverte dans le navigateur. Aucune donnée ne sort de la machine.

| Couche | Choix proposé | Pourquoi |
|---|---|---|
| Backend | **Python 3.12 + FastAPI** (géré avec `uv`) | L'écosystème stats et ML est en Python (scipy, statsmodels, scikit-learn, SDV pour CTGAN…) |
| Moteur de données | **DuckDB** sur des fichiers **Parquet** | Interroge des millions de lignes sans tout charger en RAM ; filtres et agrégations en SQL très rapides |
| Calculs | pandas / numpy / scipy (V1), statsmodels (module séries temporelles) | Tests statistiques et ajustement de lois |
| Base de l'app | **SQLite** | Métadonnées, types corrigés, préférences, cache des analyses ; un seul fichier, zéro serveur |
| Frontend | **React + TypeScript + Vite** | Contrôle total de l'ergonomie et du design, ce que Dash permet mal |
| Routage | TanStack Router | Routes typées, paramètres d'URL (dataset, variable, filtres) partageables |
| Données côté client | TanStack Query (+ persistance IndexedDB) | Cache, rechargement en arrière-plan, réouverture instantanée |
| État d'interface | Zustand | Filtres actifs, préférences |
| Graphiques | **plotly.js** (bundle local) | Imposé ; couvre la 3D, les cartes et les visuels de niche |
| Tables | TanStack Table + TanStack Virtual | Des milliers de lignes sans ralentir |
| Style | Tailwind CSS + primitives Radix (accessibles, sans style imposé) | Design system maison, pas un thème générique |
| Tests | pytest · Vitest · Playwright (e2e) | |
| Qualité | ruff + pyright (Python) · ESLint + `tsc` (TS) | |

**Alternative écartée : Plotly Dash.** Une seule langue, mais l'ergonomie est limitée, les callbacks deviennent ingérables quand l'app grossit (les erreurs « ID not found in layout » de l'ancienne app), et il est difficile d'obtenir un design soigné.

## Architecture

```
Navigateur (React)  ──HTTP /api/v1──▶  FastAPI
   │ cache TanStack Query                 │
   │ (mémoire + IndexedDB)                ├─ domain/ (logique pure : typage, stats, charts…)
   ▼                                      ├─ DuckDB ──▶ workspace/datasets/<id>/data.parquet
 plotly.js                                └─ SQLite ──▶ workspace/app.db
```

- Le **backend renvoie des données préparées** (bins, effectifs, statistiques, résultats de tests), jamais des figures toutes faites. Le **frontend construit les graphiques Plotly** avec le thème courant : payloads légers, thème cohérent, réglages instantanés (Top N, orientation).
- **Filtres** : décrits en JSON côté interface, traduits en SQL DuckDB côté backend, appliqués à toutes les requêtes.
- **Modules** : chaque grande fonctionnalité future (séries temporelles, ML…) est un module branché par un registre, des deux côtés. Détails dans [ARCHITECTURE.md](ARCHITECTURE.md).
- **Calculs longs** (import d'un gros dossier, plus tard l'entraînement ML ou la génération synthétique) : tâches en arrière-plan avec progression, sondée par l'interface.

## Cache et persistance

| Niveau | Quoi | Clé | Invalidation |
|---|---|---|---|
| Import | Copie Parquet normalisée de la source | Empreinte de la source (chemins + tailles + dates de modif) | Source modifiée → proposition de réimporter |
| Analyses | Résultats de profils, tests, préparations de graphiques (SQLite ou fichiers) | hash(empreinte dataset, version des types, filtres, analyse, paramètres) | Changement de type ou de filtre → nouvelle clé ; LRU avec plafond de taille (Paramètres) |
| Client | Réponses API en mémoire + IndexedDB | Clé de requête | Revalidation en arrière-plan |

**Workspace** : `%LOCALAPPDATA%\DataExplorer\` par défaut, modifiable avec `DATA_EXPLORER_HOME` dans `.env`. Il contient `app.db`, `datasets/` et `cache/`. Il est hors du dépôt git.

**Hors-ligne** : l'app est hors-ligne par construction. Polices, plotly.js et icônes sont embarqués, il n'y a ni CDN ni appel externe. En production, le backend sert aussi l'interface buildée : une seule commande lance tout.

## Services externes / API

- **V1 : aucun.**
- Plus tard, optionnel et désactivé par défaut : un LLM local (Ollama, modèle 7–8B quantifié) pour l'Assistant IA, ou une API distante seulement si l'utilisateur l'active explicitement (clé dans `.env`).

## Sécurité & auth

- Mono-utilisateur local : pas de comptes, pas d'authentification (à confirmer).
- Le serveur écoute uniquement sur `127.0.0.1`.
- Les fichiers sources sont en **lecture seule** : l'app ne les modifie jamais et travaille sur sa copie Parquet.
- Secrets (clés API futures) uniquement dans `.env`, jamais commités.

## Contraintes

- Machine cible : Windows 11, 32 Go de RAM, RTX 4050 (6 Go de VRAM, CUDA). Utile pour les modules ML et synthétiques.
- Volumes visés : à définir en interview. Proposition : fluide jusqu'à environ 5 M lignes × 200 colonnes.
- Budgets de performance proposés : Vue d'ensemble affichée en < 2 s sur 1 M lignes × 50 colonnes (cache froid) ; < 300 ms pour un changement de Top N ou de visuel.
- Interface en français, nombres au format français.
