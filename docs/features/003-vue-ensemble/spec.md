# 003 — Vue d'ensemble

## Objectif

La première page d'analyse : balayer toutes les variables d'un coup d'œil. Bandeau de résumé, alertes qualité, grille de cartes (3 par ligne, paginée) avec le bon graphique Plotly pour chaque type, règles d'affichage des catégories, plein écran. Introduit les **parties de date** ([DATES.md](../../DATES.md)). Références : [03-vue-ensemble.md](../../pages/03-vue-ensemble.md), [VISUALS.md](../../VISUALS.md).

## User stories

1. En ouvrant un dataset, j'arrive sur la Vue d'ensemble. Après un import, j'arrive d'abord sur Columns ; si les types n'ont jamais été validés, un bandeau me le rappelle.
2. Le bandeau me donne lignes, colonnes, % de vides, lignes et colonnes dupliquées, taille, répartition des types.
3. Les alertes me signalent ce qui mérite attention ; un clic mène à la colonne.
4. La grille montre une carte par variable (colonnes exclues masquées), 3 par ligne, 12 par page (réglable), triable et filtrable.
5. Chaque carte a le visuel adapté à son type, quelques chiffres clés, et des actions : changer de visuel, plein écran, export PNG, changer le type.
6. Pour une catégorie, je vois le Top N (réglable) + « Others » + « (missing) » ; le plein écran montre toutes les modalités avec recherche.
7. Pour une date, je bascule entre *Timeline*, *Month*, *Day of week* et *Hour* (si la colonne a une heure).
8. La page se souvient de ma pagination, mon tri, mes filtres et mon Top N pour ce dataset.

## Critères d'acceptation

**Résumé et alertes**
- GIVEN `typing_traps`, THEN le bandeau affiche 600 lignes, 21 colonnes, le % global de vides, 0 ligne dupliquée et la répartition des types.
- GIVEN un dataset avec des lignes en double, THEN leur nombre et leur % sont affichés et une alerte apparaît.
- GIVEN deux colonnes au contenu identique, THEN « colonnes dupliquées » les compte et une alerte nomme la paire.
- Alertes aussi pour : colonnes ignorées (vides/constantes), types à confirmer, forte asymétrie (|skewness| > 2), très forte cardinalité, valeurs illisibles.

**Graphiques** (données préparées côté backend, rendu Plotly côté frontend)
- Continu : histogramme (bins de Freedman–Diaconis, 10–60), statistiques (moyenne, médiane, écart-type, min, max, Q1, Q3, asymétrie) ; vue alternative boîte à moustaches.
- Discret : une barre par valeur, dans l'ordre numérique.
- Catégoriel / booléen : Top N (10 par défaut, 5–50) par fréquence ; le reste en « Others (k categories, x%) », les vides en « (missing) », tous deux distincts visuellement ; barres horizontales si libellés > 12 caractères ou > 8 barres ; camembert proposé seulement si ≤ 5 modalités.
- Ordinal : barres dans l'ordre défini sur la page Columns.
- Forte cardinalité (distinctes / lignes > 50 %, hors identifiant) : pas de barres, un message et une suggestion de type.
- Date : timeline au pas automatique (≤ 120 périodes) ; vues Month (Jan–Dec), Day of week (Mon–Sun), Hour (0–23, si heures présentes), dans l'ordre naturel.
- Texte libre : histogramme des longueurs. Identifiant : nombre de valeurs uniques et de doublons.
- Plein écran catégoriel : toutes les modalités (jusqu'à 1 000 en barres, tableau avec recherche et % cumulé au-delà).

**Grille**
- 3 cartes par ligne (2 puis 1 quand la fenêtre rétrécit), 12 par page (6/12/24/48), pagination.
- Recherche par nom, filtre par type, tri : ordre du fichier, nom, % de vides, cardinalité, asymétrie.
- Les graphiques hors écran ne sont chargés qu'en devenant visibles.
- Les réglages sont mémorisés par dataset.

## Hors scope

Filtres globaux (005), fiche variable détaillée (004, bouton visible mais inactif), cache persistant des analyses (DuckDB suffit aux volumes visés ; à ajouter si une mesure le justifie).
