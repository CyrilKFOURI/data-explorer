# 010 — Portfolio : tâches

- [x] Captures de l'app réelle depuis le conteneur Docker (Overview, fiche variable, Compare, Correlations, Data) dans `docs/screenshots/` ; chemins neutres (`/app/samples/...`)
- [x] README anglais, court et simple
- [x] CI GitHub Actions : backend, frontend, build Docker + contrôle de taille + test de fumée
- [x] Build Docker local : image en plusieurs étapes (sans cache uv ni binaire uv, sans les dossiers de tests des bibliothèques), Polars retiré (lecture Excel par openpyxl → Arrow) : 799 → 557 Mo de contenu ; `docker compose up` testé (santé, page, import des 2 échantillons)
- [x] PLAN.md (000 et 010), release V1.0
