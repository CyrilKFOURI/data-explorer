# 009 — Paramètres & finitions : tâches

## Guide
- [x] `docs/USER_GUIDE.md` : prise en main, chaque page, filtres, métriques, raccourcis
- [x] Page `/help` (rendu Markdown maison, sommaire), lien Guide, guide dans l'image Docker ; tests

## Paramètres
- [x] Backend : `GET / PUT /settings` (seuils de détection, bornes), détection paramétrée ; `GET /storage`, `POST /storage/clear-caches` ; tests
- [x] Front : apparence (thème, densité, animations), valeurs par défaut (Top N, cartes par page, α), seuils, stockage, About ; Reset par réglage ; tests

## Palette & raccourcis
- [x] Palette Ctrl+K (pages, variables, datasets, actions), clavier ; tests
- [x] Fenêtre des raccourcis `?` ; tests

## Revue
- [x] Audit (Web Interface Guidelines) : contraste AA corrigé (`ink-3` 3,2→4,5:1 en clair et 3,75→4,9:1 en sombre, accent 4,1→4,7:1, warn), `color-scheme` suivant le thème forcé (listes natives, barres de défilement), lien « Skip to content », focus visible du champ de la palette ; aucun bouton-icône sans nom, pas de `transition-all`, pas de div cliquable hors combobox
- [x] PLAN.md, docs ; vérification navigateur (Guide, Settings avec vraies tailles, palette Ctrl+K → variable, couleurs calculées)
