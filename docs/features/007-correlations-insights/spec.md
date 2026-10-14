# 007 — Corrélations & insights

## Objectif

Trouver **automatiquement** les liens entre toutes les variables, quels que soient leurs types, et résumer ce qui mérite l'attention en phrases. Les filtres globaux s'appliquent. Référence : [06-correlations.md](../../pages/06-correlations.md).

## User stories

1. Sur `/d/:id/correlations`, je vois une **matrice d'association** de toutes les variables numériques et catégorielles, chaque paire mesurée avec la bonne métrique.
2. Je choisis Pearson ou Spearman pour les paires numériques, je réordonne la matrice par **clustering**, je limite les colonnes.
3. Un clic sur une case ouvre **Compare** prérempli ; le survol donne valeur, métrique et n.
4. Je choisis une **variable cible** : les variables les plus liées à elle s'affichent en barres triées.
5. Un tableau classe les **paires les plus fortes** (métrique, valeur, p-value, n, bouton « View »).
6. Des **insights** en phrases (règles, pas de LLM) signalent asymétries, déséquilibres, valeurs manquantes, corrélations fortes, redondances, différences entre groupes et associations ; chacun a un lien « View » vers le graphique qui le justifie et peut être masqué (mémorisé pour ce dataset).

## Métriques

| Paire | Métrique | Échelle | p-value |
|---|---|---|---|
| num × num | Pearson r ou Spearman ρ | −1 … 1 | t de Student |
| cat × cat | V de Cramér corrigé du biais (Bergsma) | 0 … 1 | χ² |
| num × cat | rapport de corrélation η | 0 … 1 | F de l'ANOVA |

Numérique = continu ou discret ; catégorie = nominal, ordinal, booléen (30 modalités au plus, le reste regroupé). Dates, texte, identifiants, colonnes ignorées et catégories quasi uniques (plus de modalités que la moitié des lignes) sont exclus (listés avec la raison). Les insights de colonne (manquants, asymétrie, modalité dominante) sont calculés sur les mêmes lignes que la matrice.

## Critères d'acceptation

- Paires calculées sur les lignes où les deux valeurs existent (n par paire). Au-delà de 200 000 lignes, la matrice est calculée sur un **échantillon reproductible de 200 000 lignes**, signalé ; Spearman utilise les rangs de chaque colonne.
- GIVEN des colonnes de référence, THEN r, ρ, η et V égalent leur calcul direct (scipy / formules).
- Au plus 60 colonnes (les premières dans l'ordre du fichier, modifiable) ; au-delà, un message.
- Clustering hiérarchique (lien moyen sur 1 − |association|) : ordre des variables renvoyé avec la matrice.
- Insights, seuils :
  - asymétrie |skewness| > 2 ; modalité dominante > 70 % ; manquants ≥ 20 % ;
  - corrélation forte |r| ou |ρ| ≥ 0,7 ; **redondance** |r| > 0,95 ou V > 0,95 (remplace « forte » / « associées ») ;
  - différence entre groupes η ≥ 0,4 ; association V ≥ 0,3 ;
  - triés par importance, 30 au plus ; identifiant stable pour masquer.
- Performance : 60 colonnes × 5 M lignes en moins de 10 s ; résultat mis en cache par (dataset, types, filtres, colonnes, méthode).

## Hors scope

Calcul en tâche de fond avec progression (le calcul synchrone sur échantillon suffit aux volumes visés), insights rédigés par un LLM (module Assistant IA).
