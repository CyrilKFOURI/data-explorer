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

## Refonte du rendu (2026-10-21)

- [x] Constats clés (R-REP-14), coup d'œil, fiche en trois colonnes avec le graphique au centre, boîte à moustaches, QQ-plot, densité et repères moyenne / médiane, percentiles, valeurs fréquentes, variables liées, mois et jour de la semaine pour les dates
- [x] Relations (R-REP-15) : nuage de points avec régression, boîtes par groupe, tableau croisé coloré, test recommandé
- [x] Corrections vues dans le navigateur : règle IQR ignorée quand l'IQR vaut 0, pas de boîte ni de QQ-plot pour un nombre à ≤ 12 valeurs, droite d'ajustement coupée au cadre, deux colonnes entre 720 et 1 100 px
- Titanic : 126 Ko, 49 constats dont 12 en tête, 6 paires dessinées, ~4,5 s.
