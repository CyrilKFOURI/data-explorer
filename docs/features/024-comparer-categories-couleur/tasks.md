# 024 — Tâches

Spec : [spec.md](spec.md). Page : [05-comparer.md](../../pages/05-comparer.md).

## Tâches

- [x] T1 — Doc de page 05.
- [x] T2 — Backend : lecture d'un nombre discret en catégorie (R-CMP-01/02), couleur sur les groupes (R-CMP-03 à 06), paramètre `numbers`, `categories` et `Group.color` — tests.
- [x] T3 — Frontend : rôles d'après le nombre de valeurs, « As numbers », couleur permise sur les groupes et grisée au-delà de 6 valeurs, figures groupées (boîtes, violons, moyennes) — tests.
- [x] T4 — Guide utilisateur, vérifications, navigateur (Titanic), commit.

## Découvertes

- Sur Titanic, Survived est détecté comme booléen, donc déjà une catégorie : le vrai manque était la couleur sur les groupes. La règle R-CMP-01 sert à Pclass, SibSp et Parch.
- Le nombre de valeurs vient du résumé des colonnes (`distinct_count`) : aucune requête de plus.
- Avec une couleur, les tests portent sur les groupes, toutes couleurs confondues : leurs p-values sont identiques à celles sans couleur (vérifié en test).
