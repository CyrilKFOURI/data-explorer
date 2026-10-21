# 025 — Rapport HTML du dataset

Pages : [03-vue-ensemble.md](../../pages/03-vue-ensemble.md) (bouton), [07-donnees.md](../../pages/07-donnees.md) (menu d'export). Réutilise la 003 (vue d'ensemble), la 004 (fiche variable) et la 007 (corrélations).

## Objectif

Un fichier `.html` unique qui résume tout le dataset : on l'ouvre hors-ligne dans n'importe quel navigateur, on l'envoie par mail, on l'imprime en PDF. Même idée que le rapport de ydata-profiling, avec la profondeur de l'app : verdicts, tests, tailles d'effet, insights.

Le contenu est calculé par des fonctions pures du domaine (`app/domain/report/`), pour que la future bibliothèque Python ([bibliotheque-python.md](../../modules-futurs/bibliotheque-python.md)) puisse faire `ds.report().to_html()` avec le même code.

## User stories

1. Sur la Vue d'ensemble de Titanic, je clique **Export report**. Une barre de progression avance colonne par colonne, puis `Titanic-Dataset-report.html` se télécharge.
2. J'ouvre le fichier sans connexion : en-tête, résumé et alertes, une fiche par variable avec son graphique, les corrélations et leurs insights, les manquants, une annexe sur les méthodes.
3. Avec un filtre actif (Sex = female), le rapport le dit dans l'en-tête et tous ses chiffres portent sur les lignes filtrées.
4. Je l'imprime en PDF : les fiches ne sont pas coupées en deux, et le thème clair est utilisé.
5. Sur un gros dataset, je peux annuler la génération.

## Règles

| Id | Règle |
|---|---|
| R-REP-01 | **Autonome** : un seul fichier, aucune ressource externe (ni police, ni script, ni CDN), lisible sans JavaScript. CSS intégré, thème clair et sombre selon le système (`prefers-color-scheme`), feuille d'impression (thème clair, pas de coupure dans une fiche). |
| R-REP-02 | **Sections, dans l'ordre** : en-tête, résumé, variables, corrélations, valeurs manquantes, méthodes. Un sommaire en tête renvoie à chaque section et à chaque variable. |
| R-REP-03 | **En-tête** : nom du dataset, fichier source, lignes (filtrées / totales) × colonnes, date de génération, filtres actifs écrits en clair, version de l'app. |
| R-REP-04 | **Résumé** : colonnes par type, cellules manquantes, lignes et colonnes en double, taille, et les alertes qualité de la Vue d'ensemble (mêmes textes). |
| R-REP-05 | **Fiche variable**, selon le type : type et rôle détectés, puis les statistiques clés. Pour les nombres : moyenne, écart-type, min, quartiles, max, asymétrie, zéros, verdict de normalité (« k of n tests reject normality at α = 0.05 ») et nombre de valeurs aberrantes (IQR). Pour les catégories : distinctes, mode et sa part. Pour les dates : min, max, étendue. Pour les identifiants et les textes : distinctes et doublons. Chaque fiche affiche les manquants et les alertes de la colonne. |
| R-REP-06 | **Graphiques en SVG**, dessinés par le backend à partir des mêmes données que la Vue d'ensemble (histogramme aux classes de Freedman-Diaconis, Top 10 + « Others », chronologie). Couleurs des tokens de l'app, textes dans les couleurs de texte, une infobulle native (`<title>`) par barre. Pas de graphique pour les identifiants et les textes libres. |
| R-REP-07 | **Corrélations** : la matrice mixte en heatmap SVG (ordre groupé de la page Corrélations, au plus 30 colonnes comme elle), les 10 paires les plus liées (mesure, valeur, q-value, niveau de preuve) et les insights rédigés de la page Corrélations. |
| R-REP-08 | **Valeurs manquantes** : la part de manquants par colonne en barres horizontales, colonnes sans manquant regroupées en une ligne. |
| R-REP-09 | **Méthodes** : une phrase par méthode utilisée (tests de normalité, IQR, r / ρ, V de Cramér corrigé, η, Benjamini-Hochberg), pour le niveau d'explication « étudiant ». |
| R-REP-10 | **Pas d'ajustement de lois** (trop lent sur 5 M lignes × toutes les colonnes) ; les colonnes exclues ne sont pas analysées, mais elles sont listées. |
| R-REP-11 | **Aucune ligne entière** dans le rapport : seulement des agrégats, les catégories les plus fréquentes et les bornes. Pas d'exemples de valeurs pour les identifiants et les textes. |
| R-REP-12 | **Sécurité** : tout texte venu des données (noms de colonnes, catégories, nom du dataset) est échappé. |
| R-REP-13 | **Génération en tâche de fond**, avec progression (« Variables 12 / 40 ») et annulation. Nom du fichier : `<dataset>-report.html`, caractères interdits remplacés. |

## Données et API

- `POST /datasets/{id}/report?filters=…` → 202, `ReportJob` (id, status, progress, message).
- `GET /reports/jobs/{job_id}` → `ReportJob` ; `DELETE` l'annule.
- `GET /reports/jobs/{job_id}/file` → le fichier HTML en téléchargement, une fois le job terminé.

## Critères d'acceptation

- GIVEN Titanic WHEN je génère le rapport THEN le fichier contient une fiche par colonne non exclue, la heatmap et au moins un insight, sans aucune balise `<script>` ni lien `http`.
- GIVEN un filtre Sex = female THEN l'en-tête dit « Sex is female » et le nombre de lignes est celui des femmes.
- GIVEN une colonne nommée `<b>x</b>` THEN elle apparaît échappée.
- GIVEN Age THEN sa fiche porte un histogramme SVG, le verdict de normalité et le nombre d'aberrants.
- GIVEN Embarked THEN un Top N en barres.
- GIVEN une colonne exclue THEN elle n'a pas de fiche mais est listée.
- GIVEN un job annulé THEN pas de fichier, statut `cancelled`.
