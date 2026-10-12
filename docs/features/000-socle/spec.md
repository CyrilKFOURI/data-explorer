# 000 — Socle

## Objectif

Une application vide mais **complète de bout en bout** : backend et frontend qui se parlent, base SQLite migrée, Shell de l'interface au design validé, routage, registres de modules, outils qualité et Docker. Toutes les features suivantes se branchent dessus sans retoucher la structure.

Références : [TRD.md](../../TRD.md), [ARCHITECTURE.md](../../ARCHITECTURE.md), [UI_UX.md](../../UI_UX.md).

## User stories

1. En tant que **développeur**, je lance l'app en développement avec une seule commande et j'ai le rechargement à chaud du backend et du frontend.
2. En tant que **visiteur du portfolio**, je lance `docker compose up` et j'ouvre l'app sur `http://localhost:8000`.
3. En tant qu'**utilisateur**, je vois un Shell soigné (barre latérale, barre du haut, page d'accueil vide) en clair ou en sombre, selon mon système.
4. En tant que **développeur**, j'ajoute un module en créant un dossier et en l'enregistrant dans un registre, sans toucher au Shell.
5. En tant que **développeur**, je lance tests, lint et typecheck avec une commande chacun, et ils passent.

## Critères d'acceptation

**Démarrage en dev**
- GIVEN le dépôt cloné et `uv`, Node installés, WHEN je lance `scripts/dev.ps1`, THEN le backend écoute sur `127.0.0.1:8000`, le frontend Vite sur `127.0.0.1:5173`, et `/api` est relayé vers le backend.

**Santé et base**
- GIVEN le backend démarré, WHEN j'appelle `GET /api/v1/health`, THEN je reçois `200` avec `{status: "ok", version, db: "ok"}`.
- GIVEN un workspace vide, WHEN le backend démarre, THEN `app.db` est créé et toutes les migrations sont appliquées (table `schema_migrations` à jour) ; un second démarrage n'applique rien de plus.
- GIVEN `DATA_EXPLORER_HOME` défini dans `.env`, WHEN le backend démarre, THEN le workspace est créé à cet endroit.

**Shell et thème**
- GIVEN l'app ouverte, WHEN le système est en sombre, THEN l'interface est en sombre ; WHEN je bascule le thème dans la barre latérale, THEN le choix est conservé après rechargement.
- GIVEN l'app ouverte, THEN les couleurs viennent uniquement des tokens de `tokens.css` (aucune couleur Tailwind par défaut dans le code), et les polices IBM Plex sont servies localement (aucune requête réseau externe dans l'onglet Réseau).
- GIVEN l'app ouverte, WHEN je navigue vers `/`, `/settings` ou une route inconnue, THEN je vois respectivement l'accueil (état vide « No dataset yet »), la page Paramètres (squelette) et une page 404 propre.
- GIVEN l'accueil, THEN un indicateur discret montre que le backend répond (et un message clair s'il ne répond pas).

**Modules**
- GIVEN un module de démonstration `hello` enregistré dans les deux registres, WHEN l'app démarre, THEN une entrée apparaît dans la barre latérale et sa route répond ; WHEN je le retire du registre, THEN il disparaît sans autre modification. *Ce module sert seulement aux tests (il est retiré avant la V1, ou réservé aux tests).*

**Qualité**
- GIVEN le code du socle, WHEN je lance test, lint et typecheck (backend et frontend), THEN tout passe sans erreur.
- GIVEN le frontend, THEN le client API est typé à partir du schéma OpenAPI du backend.

**Docker**
- GIVEN Docker installé, WHEN je lance `docker compose up --build`, THEN l'app répond sur `http://localhost:8000` (interface + API depuis le même serveur), le workspace est dans un volume nommé, et `./data` est monté en lecture seule sur `/data`.
- GIVEN le conteneur lancé, THEN le port n'est publié que sur `127.0.0.1`.

## Hors scope

Import de fichiers, détection de types, toute page dataset (features 001+). Pas de CI GitHub dans cette feature (feature 010).
