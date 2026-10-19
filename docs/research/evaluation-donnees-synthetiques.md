# Recherche : évaluer des données synthétiques (table-evaluator, SDMetrics, Sweetviz)

Recherche du 2026-10-19 pour la spec [023](../features/023-donnees-synthetiques/spec.md). Les trois projets ont été lus dans leur code source et leur documentation.

**Principe retenu : on réimplémente les formules utiles, on n'ajoute aucun de ces paquets comme dépendance.** Les formules tiennent en quelques lignes de numpy, scipy ou scikit-learn, et les paquets posent des problèmes : versions figées, sortie matplotlib seulement, dépendances lourdes.

## Les trois projets en bref

| | table-evaluator | SDMetrics | Sweetviz |
|---|---|---|---|
| Rôle | Rapport réel vs synthétique en un appel | Bibliothèque de métriques et rapports de qualité de SDV | Rapport d'exploration HTML, dont la comparaison de deux jeux |
| Licence | MIT | **MIT** (SDV, lui, est sous BSL : ne pas reprendre son code de génération) | MIT |
| Maintenance | 1.9.0 (07/2025), un seul mainteneur, peu actif | Active : 0.32.0 (09/2026) | Maintenance seulement : 2.3.3 (04/2026) |
| Point fort | Visuels : fonctions de répartition, superpositions, matrice d'écarts, PCA ; idée TSTR/TRTR | Structure de rapport claire, métriques 0–1 bien définies, confidentialité (DCR, CAP) | Présentation côte à côte : pourcentages, catégories alignées, statistiques appariées, cible superposée |
| Point faible | Score global non fondé (moyenne d'échelles différentes), catégories codées en entiers, distances non normalisées | Pas de référence TRTR en ML, rapports sans cible | Aucune mesure d'écart, deux matrices sans différence, valeurs vides remplacées par 0 |

Sources : https://github.com/Baukebrenninkmeijer/table-evaluator · https://docs.sdv.dev/sdmetrics · https://github.com/sdv-dev/SDMetrics · https://github.com/fbdesignpro/sweetviz

## SDMetrics : la structure à reprendre

**Rapport Quality :** propriétés notées de 0 à 1 ; chaque propriété = moyenne de ses détails ; score global = moyenne des propriétés.

- **Column Shapes** :
  - KSComplement = 1 − statistique KS (numériques et dates converties en nombres, valeurs vides ignorées) ;
  - TVComplement = 1 − ½ Σ |R − S| (catégories, booléens, ordinaux).
- **Column Pair Trends** :
  - entre nombres : CorrelationSimilarity = 1 − |S − R| / 2 (Pearson, Spearman en option) ;
  - entre catégories : ContingencySimilarity = 1 − ½ ΣΣ |S − R| sur les tableaux croisés normalisés, la valeur vide comptant comme une catégorie ;
  - paire mixte : la colonne continue est d'abord découpée en 10 intervalles égaux **calculés sur le réel**, puis appliqués au synthétique.
  - **Filtre de force (depuis 0.27)** : seules les paires où le réel montre un vrai lien comptent dans la moyenne (|Pearson| > 0,5 ou V de Cramér > 0,3) ; le détail garde toutes les paires, avec une colonne « Meets threshold ».
- **Visualisation** : barres des scores par colonne ; matrice des similarités, plus matrices réelle et synthétique côte à côte.
- **Volontairement rien au-delà des paires** : reproduire des liens d'ordre supérieur reviendrait à copier les données.

**Rapport Diagnostic** (attendu : 100 %) :
- **BoundaryAdherence** : part des valeurs synthétiques dans [min, max] du réel.
- **CategoryAdherence** : part des catégories synthétiques présentes dans le réel.
- **KeyUniqueness** : 1 − part de doublons d'identifiant.
- **TableStructure** : |colonnes communes| / |union|, sur les paires (nom, type).

**Couverture** (détecte un générateur qui s'effondre sur quelques modes, utile avec CTGAN) :
- **RangeCoverage** : 1 − (part de l'étendue réelle manquée en bas + en haut) ;
- **CategoryCoverage** : part des catégories réelles présentes dans le synthétique ;
- **MissingValueSimilarity** : 1 − |écart des taux de vides| ;
- **StatisticSimilarity** : 1 − |écart de moyenne, médiane ou écart-type| / étendue ;
- **OutlierCoverage** : part de valeurs hors des clôtures 1,5 × IQR du réel, synthétique vs réel, plafonnée à 1. Réservée à la version payante de SDMetrics, mais la formule est publique.

**Confidentialité :**
- **Distance DCR** : pour un nombre ou une date, |a − b| / étendue réelle, plafonnée à 1 ; pour une catégorie ou une valeur vide, 0 ou 1. Distance d'une ligne = moyenne sur les colonnes. Calcul par blocs de 1 000 lignes.
- **DCRBaselineProtection** = min(1, médiane DCR(synthétique → réel) / médiane DCR(aléatoire uniforme dans les étendues → réel)).
- **DCROverfittingProtection** : nécessite des lignes réelles **tenues à l'écart**. Score = min(1, 2 × (1 − part des lignes synthétiques plus proches de l'apprentissage que des lignes tenues à l'écart)).
- **NewRowSynthesis** : 1 − part des lignes synthétiques identiques à une ligne réelle (nombres mis à l'échelle min-max, tolérance 0,01).
- **DisclosureProtection (CAP)** : l'utilisateur désigne des colonnes « connues » et une colonne « sensible ». Pour chaque ligne réelle, on regarde les lignes synthétiques qui ont les mêmes valeurs connues ; leur vote sur la colonne sensible est-il juste ? Le résultat est comparé à une référence aléatoire. Variantes zero-CAP et generalized-CAP.

**Detection** : LogisticDetection. Réel et synthétique sont empilés et étiquetés, imputés et mis à l'échelle, puis évalués en validation croisée stratifiée 3 plis. Score = 1 − (max(AUC, 0,5) × 2 − 1).

**ML efficacy (TSTR)** : arbre de décision, régression logistique, MLP ; F1 pour une classification, R² pour une régression. **SDMetrics ne calcule pas la référence TRTR** (entraîné sur réel, testé sur réel) : à ajouter de notre côté.

**Écartés** : CSTest (la doc elle-même le déconseille), vraisemblances BN, GM et LSTM (dépendances lourdes, sens flou), SVCDetection (O(n²)), attaques par modèle (beta), contraintes au format SDV.

## table-evaluator : les visuels et l'utilité

**À reprendre :**
- **Matrice d'associations mixte** pour le réel, pour le synthétique, puis **|Δ|** (échelle des écarts plafonnée à 0,3). Pearson entre nombres, V de Cramér corrigé (Bergsma) ou U de Theil entre catégories, η en mixte, paires incomplètes retirées.
- **Fonctions de répartition empiriques (ECDF)** réel et synthétique superposées par colonne. Plus lisibles qu'un histogramme pour voir des queues de distribution coupées.
- **Nuage moyenne / écart-type en log**, réel en x, synthétique en y, avec la diagonale : un aperçu d'un coup d'œil quand il y a beaucoup de colonnes numériques.
- **PCA ajustée sur le réel**, synthétique projeté dans le même plan, les deux superposés.
- **Utilité** : idée TRTR / TSTR, mais **à corriger** (voir ci-dessous).
- **Comparaison de plusieurs générateurs** sur une même figure, une colonne par méthode.

**À ne pas reprendre (défauts trouvés dans le code) :**
- le « Similarity Score » : une moyenne d'échelles hétérogènes ;
- le score « basic statistics » : une corrélation de Spearman qui vaut toujours environ 0,99 ;
- des catégories codées en entiers, différemment dans le réel et le synthétique ;
- des valeurs vides numériques remplacées par la moyenne de chaque jeu ;
- des distances calculées sans mise à l'échelle ;
- un modèle « entraîné sur synthétique » testé sur du synthétique ;
- des seuils absolus de Wasserstein ;
- une « membership inference » qui n'est qu'un détecteur.

**Correction retenue pour l'utilité** : entraîner sur le réel d'apprentissage et sur le synthétique, puis tester **les deux sur les mêmes lignes réelles tenues à l'écart**. On présente les deux scores côte à côte et leur rapport.

## Sweetviz : la présentation côte à côte

**À reprendre :**
- **Tout en % de son propre jeu** (comptage + %), car réel et synthétique n'ont pas forcément le même nombre de lignes.
- **Histogrammes sur les mêmes limites d'intervalles**, normalisés en %.
- **Tableau des catégories aligné** : réel %, synthétique %, 0 si absente d'un côté, trié par fréquence réelle, reste en « Others ». Les catégories inventées ou perdues sautent aux yeux.
- **Statistiques appariées** : libellé, valeur réelle, valeur synthétique sur min, 5 %, Q1, médiane, Q3, 95 %, max, moyenne, écart-type, IQR, asymétrie, aplatissement. **On ajoute une colonne Δ**, absente de Sweetviz.
- **Bande de base par colonne** : valeurs, vides, distinctes, zéros, chacune en comptage et en %.
- **Valeurs les plus fréquentes, plus petites et plus grandes**, avec leur fréquence dans l'autre jeu. Elles repèrent la mémorisation (mêmes valeurs fréquentes), les queues coupées et les arrondis.
- **Cible superposée** : par intervalle ou par catégorie, la moyenne de la cible (ou la part de « vrai ») dans le réel et dans le synthétique. Cela montre si le lien avec la cible est conservé, pas seulement les distributions.
- **En-tête** : lignes, doublons, colonnes par type, colonnes absentes d'un côté.
- **Une couleur fixe par jeu** dans tous les graphiques et nombres.
- **Lignes compactes qui se déplient** pour parcourir beaucoup de colonnes.

**À améliorer plutôt que copier :**
- ajouter la matrice des différences d'associations ;
- ajouter un score d'écart par colonne pour trier les colonnes de la plus abîmée à la moins abîmée ;
- retirer les lignes incomplètes au lieu de remplacer les vides par 0 ;
- proposer Spearman en plus de Pearson.

**À ne pas reprendre :** images matplotlib en PNG, erreurs bloquantes sur les types mélangés, texte libre traité comme une simple liste de fréquences, calcul sur toutes les lignes sans échantillon.

## Ce que la 023 en retient (résumé)

1. **Deux rapports à la SDMetrics** :
   - **Diagnostic** (validité, attendu 100 %) ;
   - **Quality** : Column shapes + Column pair trends ; global = moyenne, donc comparable aux scores SDMetrics publiés ; filtre de force des paires.
   - S'y ajoutent, à part, la couverture et les valeurs vides.
2. **Détection** (réel ou synthétique ?) avec un score de 0 à 1 et les colonnes qui trahissent le synthétique. Présentée comme une mesure de fidélité, pas de confidentialité.
3. **Utilité TSTR avec la référence TRTR** sur les mêmes lignes réelles tenues à l'écart.
4. **Confidentialité** : copies exactes (avec tolérance), DCR avec référence aléatoire (BaselineProtection), DCR apprentissage vs tenu à l'écart (OverfittingProtection), valeurs rares ; CAP en option.
5. **Comparaison colonne par colonne à la Sweetviz**, améliorée :
   - %, intervalles communs, catégories alignées, statistiques appariées avec Δ, ECDF ;
   - valeurs fréquentes, extrêmes et rares croisées ;
   - cible superposée en option ;
   - colonnes triées par score.
6. **Liens** : matrices réelle, synthétique et |Δ| ; les 5 paires les plus abîmées.
7. **Vues d'ensemble** : nuage moyenne / écart-type, PCA ajustée sur le réel.
8. **Comparaison de runs** : une colonne par méthode.
