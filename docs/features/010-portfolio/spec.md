# 010 — Portfolio

## Objectif

Rendre le projet présentable et installable par un visiteur : README anglais avec captures, installation en une commande, CI qui prouve que tout passe. Référence : [PRD](../../PRD.md) (critère « Prêt pour le portfolio »).

## User stories

1. En arrivant sur le dépôt, je comprends en 30 secondes ce que fait l'app et pourquoi elle se distingue (profondeur statistique), grâce au README et à ses captures.
2. Je l'installe avec `docker compose up --build`, j'ouvre <http://localhost:8000> et j'explore les jeux de démo sans rien configurer.
3. Un badge CI montre que les tests, le lint, le typecheck et le build Docker passent à chaque push.

## Critères d'acceptation

- README anglais : accroche, captures (Overview, fiche variable, Compare, Correlations, Data), fonctionnalités, ce qui le distingue, installation Docker, développement, architecture en bref, lien vers le guide (`docs/USER_GUIDE.md`), licence MIT. Aucune mention d'un employeur.
- Captures dans `docs/screenshots/` (PNG, thème clair, jeux de démo), prises sur l'app réelle.
- CI GitHub Actions (`.github/workflows/ci.yml`) : backend (uv : ruff, format, pyright, pytest hors `slow`), frontend (npm ci : lint, typecheck, tests, build), build Docker puis test de fumée (`/api/v1/health` répond `ok` dans le conteneur).
- Image Docker < 600 Mo ; `docker compose up --build` testé en local : l'app répond, les échantillons s'importent.

## Hors scope

Vidéo / GIF de démo (plus tard), démo hébergée, publication d'image sur un registre.
