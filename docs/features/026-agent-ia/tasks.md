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

## 026b+ — Tous fournisseurs

- [x] Dépendance : `openai>=3` dans l'extra `[agent]` (validé)
- [x] `providers/vendors.py` : fournisseurs, préfixes de clé, modèles connus ou préférés, `detect`, `chat_models`, `pick_default`
- [x] `providers/openai_compat.py` : flux chat-completions, appels d'outils réassemblés, usage, erreurs typées + tests (vrais objets du SDK, client simulé)
- [x] Réglages : une clé par fournisseur (env puis fichier), clé rangée selon sa forme, clé mal rangée déplacée au démarrage, fournisseur « auto »
- [x] Budget : coût inconnu → plafond en tokens (2 M), tokens enregistrés (migration `0012`), événements `spent` / `done` avec `conversation_tokens` et `priced`
- [x] API : `providers`, `active`, `ready`, `token_limit`, `GET /settings/models` ; `tokens` sur les conversations
- [x] Panneau : choix du fournisseur, clé du fournisseur actif, adresse d'un serveur local, modèles listés depuis l'API (rafraîchir, saisie libre en repli), effort et budget en dollars pour Claude seulement, pied du panneau en tokens quand le prix est inconnu + tests
- [x] Docs : USER_GUIDE, PLAN
- [x] Essai réel avec la clé Gemini de l'utilisateur (2026-10-22, Titanic, 2 tours) : réponses justes et chiffrées, outils en parallèle, ~23 k puis ~42 k tokens par tour. Corrigé en route : signatures de pensée de Gemini (`extra_content`) gardées et renvoyées au seul Gemini, appels d'outils sans `index` ; modèle par défaut `gemini-flash-latest` (les clés gratuites n'ont pas de quota pour Pro) ; modèles non conversationnels écartés (Lyria, Nano Banana, Live) ; prompt : pas de LaTeX ni de noms d'outils ; erreur de filtre qui donne les opérateurs permis (booléens : `in` avec "True" / "False")

## 026c — Mémoire et qualité (spec § 13.1)

- [x] Vérificateur d'ancrage : `engine/grounding.py` (pur) + tests ; enregistré avec la réponse, événement `done`, transcription ; note sous la réponse dans le panneau
- [x] Notes : migration `0013_agent_notes.sql`, repository, outil `remember` (write), routes `GET|POST|DELETE /datasets/{id}/notes`, injection dans le prompt ; vue Notes dans le panneau + tests
- [x] Playbooks : six fichiers markdown, outil `get_playbook`, ligne dans le prompt + tests
- [x] Compaction : `engine/compaction.py` (pur), appliquée à chaque requête + tests
- [x] Évaluation : `backend/evals/agent_eval.py` (`--model`, `--only`, pauses, reprise après une limite par minute, arrêt net sur un quota du jour) et 15 cas dans `agent_cases.json`. Premiers passages (2026-10-22, clé Gemini gratuite : **20 requêtes par jour et par modèle**, d'où 6 cas joués sur `gemini-3.6-flash` et `gemini-3.5-flash`) : 3 réussis (titanic-drivers, titanic-quality, sales-top-store). Échecs utiles, tous corrigés :
  - le vérificateur signalait 10 chiffres justes calculés par le modèle à partir du tableau croisé → `compare_columns` donne désormais totaux et pourcentages par ligne et par colonne ;
  - le modèle divisait lui-même des effectifs (62 / 714) → `count_rows` accepte `within` (taux dans un groupe, calculé par l'app) ;
  - un filtre booléen écrit `true` (JSON) ou `"true"` échouait ou ne gardait aucune ligne → valeurs converties en texte, booléens reconnus quelle que soit l'écriture ;
  - quota du jour : message clair (« today's quota of 20 requests… again in 21h56m ») au lieu d'une limite générique
- [ ] Rejouer les 15 cas quand le quota le permet (ou avec une clé payante)
- [ ] Docs : USER_GUIDE, BACKEND_SCHEMA, ARCHITECTURE, PLAN
- [ ] Partage des lignes (`sample_rows`) : reporté en V2
