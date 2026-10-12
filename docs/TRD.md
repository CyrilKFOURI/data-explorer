# TRD — Technical Requirements

> Statut : validé (interview du 2026-10-12).

## Stack

Application **locale** : un serveur Python sur la machine et une interface web ouverte dans le navigateur. Aucune donnée ne sort de la machine.

| Couche | Choix proposé | Pourquoi |
|---|---|---|
| Backend | **Python 3.12 + FastAPI** (géré avec `uv`) | L'écosystème stats et ML est en Python (scipy, statsmodels, scikit-learn, SDV pour CTGAN…) |
| Moteur de données | **DuckDB** sur des fichiers **Parquet** | Interroge des millions de lignes sans tout charger en RAM ; filtres et agrégations en SQL très rapides |
| Calculs | **Polars** (en mémoire, moteur Rust multi-cœur) + numpy / scipy (V1), statsmodels (module séries temporelles) ; pandas seulement si une bibliothèque l'exige | Tests statistiques et ajustement de lois. Pas de backend Rust : le calcul lourd est déjà compilé (DuckDB en C++, Polars en Rust, scipy en C/Fortran), et l'écosystème stats/ML est en Python. Un point chaud pourra être réécrit en Rust via PyO3 si besoin. |
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

**Workspace** : dossier défini par `DATA_EXPLORER_HOME` (`.env`). En Docker, c'est un **volume nommé** (`/workspace`), qui survit aux mises à jour de l'image. En développement natif : `%LOCALAPPDATA%\DataExplorer\`. Il contient `app.db`, `datasets/` et `cache/`, hors du dépôt git.

**Hors-ligne** : l'app est hors-ligne par construction. Polices, plotly.js et icônes sont embarqués, il n'y a ni CDN ni appel externe. En production, le backend sert aussi l'interface buildée.

## Distribution (validé : Docker)

- **Une commande** pour le visiteur : `docker compose up`, puis ouvrir `http://localhost:8000`.
- **Image multi-étapes** : une étape Node build l'interface, l'image finale (Python slim) ne contient que le backend et le front compilé. Objectif : < 600 Mo pour la V1.
- **Accès aux fichiers** : un conteneur ne voit pas `C:\...`. Deux voies d'import :
  1. **Glisser-déposer / upload** depuis le navigateur : marche partout.
  2. **Dossier monté** : `docker-compose.yml` monte un dossier de l'hôte (`./data` par défaut, modifiable dans `.env`) en `/data` **en lecture seule**. Le bouton « Browse » de l'app parcourt `/data`. C'est la voie pour les gros fichiers et les dossiers.
- **Port** publié seulement sur `127.0.0.1:8000` de l'hôte (pas exposé au réseau local).
- **GPU** (modules ML et synthétiques, plus tard) : variante d'image CUDA + `docker-compose.gpu.yml` (nécessite NVIDIA Container Toolkit / WSL2). La V1 n'en a pas besoin.
- **Développement** : en natif (uv + Vite, rechargement à chaud). Docker sert à la distribution et aux tests de fumée en CI.
- Les **images Docker prennent de la place** sur le SSD : prévenir avant les builds lourds (surtout CUDA).
- **Licence : MIT.**

## Services externes / API

- **V1 : aucun.**
- Plus tard, optionnel et désactivé par défaut : un LLM local (Ollama, modèle 7–8B quantifié) pour l'Assistant IA, ou une API distante seulement si l'utilisateur l'active explicitement (clé dans `.env`).

## Sécurité & auth

- Mono-utilisateur local : pas de comptes, pas d'authentification (validé : projet portfolio installé en local, pas de démo hébergée).
- Le serveur n'est accessible que depuis la machine : `127.0.0.1` en natif ; en Docker, il écoute dans le conteneur, mais le port n'est publié que sur `127.0.0.1` de l'hôte.
- Upload : taille max réglable ; dans le dossier monté `/data`, chemins limités à ce dossier (pas de `../`).
- Les fichiers sources sont en **lecture seule** : l'app ne les modifie jamais et travaille sur sa copie Parquet.
- Secrets (clés API futures) uniquement dans `.env`, jamais commités.

## Contraintes

- Machine cible : Windows 11, 32 Go de RAM, RTX 4050 (6 Go de VRAM, CUDA). Utile pour les modules ML et synthétiques.
- Volumes visés (validé) : fluide jusqu'à environ **5 M lignes** × 200 colonnes.
- Budgets de performance proposés : Vue d'ensemble affichée en < 2 s sur 1 M lignes × 50 colonnes (cache froid) ; < 300 ms pour un changement de Top N ou de visuel.
- Interface **en anglais** en V1 ; tous les textes centralisés (fichiers de traduction) pour ajouter le français ensuite. Format des nombres et des dates selon la locale active.
- Docs internes (`docs/`) en français ; README public en anglais.
