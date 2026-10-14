# Corrélations & insights — `/d/:id/correlations`

## Rôle

Trouver **automatiquement** les liens entre variables, quels que soient leurs types, et les résumer en phrases.

## Contenu

1. **Matrice d'association mixte** (heatmap, toute la largeur de la page) : chaque paire est mesurée avec la métrique adaptée, ramenée à une échelle 0–1 (ou −1/+1 pour num × num) :
   - num × num : Pearson ou Spearman (au choix)
   - cat × cat : V de Cramér (corrigé du biais)
   - num × cat : rapport de corrélation η
   - Dates exclues (leurs liens se voient dans Comparer)
   - Option : réordonner par **clustering** pour regrouper les variables liées
   - Survol : valeur, métrique, n ; clic → Comparer prérempli
   - Plafond : 60 colonnes (sélection libre) pour rester lisible et rapide
2. **Focus sur une variable** (sous la matrice) : on choisit une variable, la liste classée des variables les plus liées s'affiche avec une barre, la mesure et un lien vers Comparer.
3. **Paires les plus fortes** : tableau classé (variable A, variable B, métrique, valeur, p-value, visuel conseillé, bouton « Voir »).
4. **Insights** : phrases générées par des règles (pas de LLM en V1), chacune avec un lien vers le graphique qui la justifie :
   - « `revenu` est fortement asymétrique à droite (skewness 3,2) : quelques valeurs très élevées. »
   - « `catégorie` est déséquilibrée : "A" représente 72 % des lignes. »
   - « `heures` et `productivité` sont fortement corrélées (ρ = 0,85). »
   - « Le `salaire` diffère selon le `niveau_étude` (Kruskal–Wallis p < 0,001, ε² = 0,18). »
   - « `prix_ht` et `prix_ttc` sont quasi identiques (r = 0,999) : probablement redondantes. »
   - « 38 % de valeurs manquantes dans `téléphone`. »
   - Les insights sont regroupés par thème (redondances, relations, distributions, qualité des données) ; les noms de variables sont colorés selon leur type. Un lien entre deux variables n'est signalé que s'il est significatif (p < 0,05).

## Règles

- Signal de **redondance** au-delà de |r| > 0,95.
- Les identifiants, le texte libre et les colonnes ignorées sont exclus par défaut.
- Au-delà de 200 000 lignes, calcul sur un échantillon reproductible de 200 000 lignes (signalé) ; résultat mis en cache. Les filtres globaux s'appliquent.
- Seuils des insights : asymétrie |skewness| > 2, modalité dominante > 70 %, manquants ≥ 20 %, corrélation forte ≥ 0,7, différence entre groupes η ≥ 0,4, association V ≥ 0,3.
