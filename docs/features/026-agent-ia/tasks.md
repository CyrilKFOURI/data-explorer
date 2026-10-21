# 026 — Tâches

Décisions prises avant de coder (2026-10-21) : SDK officiel `anthropic` dans l'extra `[agent]` (accord donné) ; Anthropic seul en 026a ; l'agent répond dans la langue de l'utilisateur ; pas de `run_sql` en v1 ; budget 1 $ par conversation ; modèle par défaut `claude-opus-5-5`, réglable (Sonnet 5.5, Haiku 5.5) ; repli automatique côté serveur (`fallbacks: "default"`) activé pour Opus 5.5 et Sonnet 5.5.

## Architecture (module isolé)

Le module ne modifie le code existant qu'à des points d'extension : une ligne dans `modules/registry.py`, une migration numérotée ; côté frontend, le registre des panneaux (point d'extension générique du Shell, ajouté pour l'occasion : type `PanelManifest`, liste `panels`, rendu dans le Shell, option du routeur) et l'export de `request` / `apiError` dans `api/client.ts` ; l'extra `[agent]` dans la CI et l'image Docker.

```
backend/app/modules/agent/
  __init__.py        setup(app) : crée AgentService sur app.state ; router
  router.py          HTTP (réglages, conversations, flux SSE, Stop)
  service.py         AgentService : tours dans un thread, file d'événements, persistance, budget
  repository.py      SQLite (agent_conversations, agent_messages)
  settings.py        réglages (workspace/agent/settings.json) et clé (env ou workspace/agent/secrets.env)
  engine/            pur : ni FastAPI, ni SQLite, ni SDK
    messages.py      blocs neutres (texte, réflexion, appel d'outil, résultat) ; blocs propres au fournisseur gardés tels quels
    provider.py      interface Provider, événements, usage, erreurs typées
    tools.py         contrat d'outil (classe read/compute/write/rows, entrée Pydantic, sortie compacte + lien app), registre
    loop.py          boucle ReAct : étapes max, budget, Stop, outils en parallèle, erreurs réinjectées, garde write/rows
    budget.py        prix par modèle, coût d'un usage
    prompt.py        prompt système stable (mis en cache) + bloc de contexte par tour (filtres, page)
  providers/anthropic.py   SDK officiel (import paresseux), flux, cache, repli serveur, erreurs
  tools/             outils 026a (lecture seule, sur les services V1) : dataset.py, relations.py
```

## 026a — Socle

- [x] Dépendance : extra `[agent]` (`anthropic>=2`), CI
- [x] Moteur pur : messages, provider, tools, loop, budget, prompt + tests (fournisseur simulé)
- [x] Fournisseur Anthropic : flux, outils, cache de prompt, réflexion adaptative, repli serveur, erreurs typées + tests (client simulé)
- [x] Outils lecture seule : `get_dataset_overview`, `list_columns`, `profile_column`, `compare_columns`, `get_correlations`, `rank_associations_with`, `count_rows` + tests contre les services
- [x] Persistance : migration `0011_agent.sql`, repository + tests
- [x] Réglages et clé : lecture env / fichier, masquage, test de la clé + tests
- [x] Service et routes : conversations, tour en flux SSE, Stop, coût cumulé + tests API (fournisseur simulé)
- [x] Frontend : point d'extension « panneaux » du Shell ; panneau de l'agent (Ctrl+J), messages en flux, étapes repliables avec liens « Open in … », réglages et clé, coût, Stop, état vide avec questions suggérées
- [x] Docs : BACKEND_SCHEMA, USER_GUIDE, ARCHITECTURE (point d'extension), page d'aide ; PLAN
- [x] Vérifier : tests (backend 26 + frontend 3 nouveaux), lint, typecheck, panneau vu dans le navigateur sans clé (mise en route, réglages)
- [ ] Essai réel avec la clé de l'utilisateur (un appel facturé : à faire avec lui)

## 026b — Actions

- [x] Contrat d'outil déplacé dans `app/core/tools.py` (partagé, neutre) + `wait_for` (suivi d'une tâche de fond avec progression, annulation au Stop, délai) + `compact` (résultat allégé) ; le moteur le réexporte
- [x] Point d'extension `Module.agent_tools` dans `modules/registry.py` : chaque module déclare ses outils, collectés après tous les `setup` dans `app.state.agent_tools` ; registre de l'agent construit à la première utilisation
- [x] ML (`modules/ml/agent_tools.py`) : `list_ml_targets`, `list_ml_models`, `train_model`, `compare_models`, `tune_model`, `explain_model`, `list_ml_runs`
- [x] Séries temporelles : `analyze_time_series` (tendance, saisonnalité, stationnarité), `forecast`
- [x] KPI : `suggest_kpis`, `compute_kpi`, `save_kpi` (write)
- [x] Synthétique : `plan_synthetic`, `generate_synthetic`, `save_synthetic_dataset` (write)
- [x] Rapport HTML (service du domaine, outil de l'agent) : `export_report`, lien de téléchargement
- [x] Confirmation des `write` : événement `confirm`, le tour attend la décision (10 min max, Stop = refus), route `POST /conversations/{id}/confirm/{call_id}` ; carte Confirm / Dismiss dans le panneau
- [x] Progression des tâches longues dans l'étape (`step_progress`), liens vers ML, séries temporelles, KPI, synthétique, nouveau dataset, téléchargement du rapport
- [x] Tests : contrat partagé, collecte des outils, chaque outil sur les jeux de démo, confirmation acceptée / refusée, progression, carte de confirmation et liens côté panneau

## 026c — Mémoire et qualité (plus tard)

Notes du dataset, compaction côté serveur, playbooks, partage des lignes et masquage, OpenAI, évaluation réelle.
