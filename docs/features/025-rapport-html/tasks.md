# 025 — Tâches

- [x] Docs : pages 03 et 07 (bouton, menu), USER_GUIDE ; BACKEND_SCHEMA inchangé (aucune table : jobs et fichiers en mémoire)
- [x] Domaine `app/domain/report/` : `model.py` (dataclasses du rapport), `build.py` (assemble overview, profils, graphiques, corrélations), `svg.py` (histogramme, barres, chronologie, heatmap, barres de manquants), `html.py` (gabarit, CSS, échappement)
- [x] Service `ReportService` : job en tâche de fond, progression, annulation, fichier temporaire
- [x] API : POST rapport, GET / DELETE job, GET fichier
- [x] Tests unitaires (SVG, échappement, sections, filtres) et API (Titanic, job annulé)
- [x] Frontend : bouton Export report (Vue d'ensemble) et entrée du menu d'export (Données), progression, téléchargement
- [x] Vérifier : tests, lint, typecheck, rapport ouvert dans le navigateur (clair, sombre)
- [ ] Aperçu d'impression / PDF (feuille d'impression écrite, pas encore vue)
- [x] PLAN + commit local

Mesuré sur Titanic : 46 Ko, 12 fiches, aucun script ; ~3 s machine au calme (17 s avec le CPU occupé par un autre projet). Le coût vient surtout de l'ouverture d'une connexion DuckDB à chaque appel de service (~70 ms) : piste d'optimisation commune à toute l'app, pas propre au rapport.
