# 006 — Comparer

## Objectif

Croiser **2 variables** (ou 3 numériques en 3D), avec le bon graphique et le bon test statistique choisis selon les types, une taille d'effet et un verdict en une phrase. Les filtres globaux s'appliquent. Référence : [05-comparer.md](../../pages/05-comparer.md), [VISUALS.md](../../VISUALS.md).

## User stories

1. Sur `/d/:id/compare`, je choisis X et Y parmi les colonnes analysables ; en option une **Couleur** (catégorie) et, si X et Y sont numériques, un **Z** numérique pour la 3D. Un bouton inverse X et Y.
2. L'app choisit le visuel adapté aux types, et je peux basculer entre les vues compatibles.
3. Un panneau « Statistical test » affiche les tests adaptés : verdict, statistique, p-value, taille d'effet avec son ordre de grandeur, conditions d'application (« variances inégales → Welch-ANOVA »).
4. Depuis la fiche variable, « Compare with… » ouvre la page avec X prérempli.
5. Le choix (X, Y, Z, Couleur) est dans l'URL, avec les filtres.

## Combinaisons

| Types | Vues | Tests | Taille d'effet |
|---|---|---|---|
| num × num | Nuage (+ droite de régression), densité 2D | Pearson, Spearman, Kendall | r, ρ, τ ; R² |
| num × num × num | Nuage 3D (couleur optionnelle) | (ceux de X × Y) | — |
| num × cat, 2 groupes | Boîtes, violons, moyennes ± IC 95 % | t de Welch, Mann–Whitney | d de Cohen, r rang-bisérial |
| num × cat, ≥ 3 groupes | idem | ANOVA, Welch-ANOVA, Kruskal–Wallis, Levene (choix recommandé selon Levene) | η², ε² |
| cat × cat | Heatmap de contingence, barres empilées 100 % | χ² d'indépendance, Fisher exact (2 × 2, petits effectifs) | V de Cramér |
| date × num | Moyenne par période (pas auto), avec min–max | Spearman (tendance) | ρ |
| date × cat | Effectifs par période et catégorie (aire empilée) | — | — |

Numérique = continu ou discret ; catégorie = nominal, ordinal, booléen. Texte, identifiant et colonnes ignorées ne sont pas proposés.

## Critères d'acceptation

- **Exactitude** : statistiques calculées sur **toutes les lignes** quand c'est possible (Pearson, régression, t de Welch et ANOVA depuis les moyennes / variances par groupe, χ² sur la table complète) ; tests de rang (Spearman, Kendall, Mann–Whitney, Kruskal–Wallis, Levene) sur un échantillon reproductible de 5 000 lignes au plus, signalé. GIVEN des données de référence, THEN les résultats égalent scipy.
- **Volumes** : au plus 20 000 points dessinés (échantillon signalé) ; la densité 2D est calculée sur toutes les lignes. Catégories : 12 groupes au plus (les plus fréquents), le reste en « Others » ; contingence 15 × 15 au plus.
- **Lignes utilisées** : seules les lignes où X et Y (et Z, Couleur) sont renseignés ; leur nombre est affiché.
- **Effet** : ordre de grandeur (négligeable, faible, moyen, fort) selon les seuils de Cohen ; le verdict sépare significativité et importance (« significatif mais négligeable » avec n grand).
- **Erreurs** : colonne inconnue ou non comparable → 422 claire ; moins de 3 lignes utilisables → message, pas de test.
- **Couleurs** : palette catégorielle `--chart-1…8` dans l'ordre fixe, « Others » en gris.
- Performance : 5 M lignes, num × num et num × cat en moins de 3 s.

## Hors scope

Facettes (petits multiples), sélecteur d'intention, surface de densité 3D, clic sur un point pour filtrer, régression complète avec diagnostics (module ML).
