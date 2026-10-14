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
   - Les insights sont regroupés par thème (redondances, relations, distributions, qualité des données) ; les noms de variables sont colorés selon leur type. Les liens entre variables sont classés par **niveau de preuve** (voir plus bas).

## Niveau de preuve des liens

Chaque paire reçoit un **niveau de preuve**, qui croise deux questions : le lien est-il **gros** (taille d'effet) et est-il **réel** (pas du hasard) ?

- **Taille d'effet** (conventions de Cohen) : petite / moyenne / grande à |r| ou ρ ≥ 0,1 / 0,3 / 0,5, η ≥ 0,10 / 0,24 / 0,37 (η² = 0,01 / 0,06 / 0,14), V de Cramér ≥ 0,1 / 0,3 / 0,5.
- **p-value ajustée** (Benjamini-Hochberg) : on teste toutes les paires à la fois ; sur 1 000 paires, une cinquantaine passent p < 0,05 par pur hasard. L'ajustement contrôle cette proportion de fausses découvertes. Les phrases et tableaux affichent la p-value ajustée (« adj. p »).

| Niveau | Règle | Lecture |
|---|---|---|
| **Fort** | effet grand et adj. p < 0,001 | lien net, très improbable par hasard |
| **Modéré** | effet au moins moyen et adj. p < 0,05 | lien réel, d'ampleur notable |
| **Faible** | effet petit mais adj. p < 0,05, ou effet au moins moyen mais adj. p ≥ 0,05 | réel mais mineur, ou peut-être du hasard (la phrase précise lequel) |
| aucun | effet négligeable, ou petit et non significatif | pas d'insight |

- Un sélecteur **« Show: Strong · Strong + moderate · All »** au-dessus des insights choisit les niveaux affichés (compte par niveau sur chaque option). Le choix est mémorisé pour toute l'application ; défaut : fort + modéré.
- Le sélecteur ne touche que les liens entre variables ; les insights de distribution et de qualité s'affichent toujours.
- Chaque phrase de lien porte une pastille de niveau ; le tableau des paires et le focus aussi (à la place de « n.s. »), triés par niveau puis par force.

## Règles

- Signal de **redondance** au-delà de |r| > 0,95.
- Les identifiants, le texte libre et les colonnes ignorées sont exclus par défaut.
- Au-delà de 200 000 lignes, calcul sur un échantillon reproductible de 200 000 lignes (signalé) ; résultat mis en cache. Les filtres globaux s'appliquent.
- Seuils des insights : asymétrie |skewness| > 2, modalité dominante > 70 %, manquants ≥ 20 %, redondance |r| ou V > 0,95 ; les autres liens suivent le niveau de preuve.
