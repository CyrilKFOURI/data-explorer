# 002 — Détection des types

## Objectif

Chaque colonne d'un dataset reçoit un **type d'analyse** (et si possible un **rôle**) détecté automatiquement, expliqué et corrigeable. La donnée importée n'est jamais modifiée : chaque colonne a un **parseur** (comment lire la valeur brute dans son type), appliqué à la lecture. C'est la base de toutes les analyses suivantes. Références : [COLUMN_DETECTION.md](../../COLUMN_DETECTION.md), [02-colonnes.md](../../pages/02-colonnes.md).

## User stories

1. À la fin d'un import, les types sont détectés ; au premier import j'arrive sur la page **Columns**.
2. Pour chaque colonne je vois : type, rôle, confiance, raisons, quelques valeurs, une mini-distribution, % de manquants, nombre de valeurs distinctes.
3. Je corrige un type ou un rôle en un clic ; si la conversion rend des valeurs illisibles, je vois combien.
4. Je peux exclure une colonne, annuler une correction (Ctrl+Z), revenir à la détection, corriger plusieurs colonnes à la fois.
5. Je fixe l'ordre des modalités d'une variable ordinale.
6. Je valide les types ; je peux relancer la détection sans perdre mes corrections.

## Critères d'acceptation

**Détection** (jeu de référence `samples/typing_traps.csv` + `samples/sales_timeseries.csv`)
- GIVEN `typing_traps`, THEN 100 % des colonnes ont le type attendu (tableau dans `backend/tests/unit/test_typing.py`), dont :
  - `price_eur` « 79,50 » et `income` « 55 680,93 » / « N/A » → numérique continu, parseur décimale `,`, rôle montant ;
  - `discount` « 15% » → numérique (rôle pourcentage) ;
  - `satisfaction` 1–5, `nb_children` 0–5 → **numérique discret** ;
  - `is_active` oui/non → booléen ; `zip_code` « 07500 » → catégoriel (rôle code postal) ;
  - `segment` low/medium/high → **ordinal** avec l'ordre low < medium < high ;
  - `customer_id`, `email` → identifiant ; `comment` → texte libre ; `birth_year` → date (rôle année) ;
  - `source_system` (constante), `legacy_code` (97 % vide) → ignorée.
- GIVEN une colonne entière dont ≥ 95 % des valeurs se lisent comme des dates `jj/mm/aaaa`, THEN type date et parseur avec ce format ; si `jj/mm` et `mm/jj` sont tous deux possibles, confiance moyenne et raison « ambigu ».
- Chaque détection a une confiance (high / medium / low) et au moins une raison lisible.

**Corrections**
- WHEN je change le type d'une colonne, THEN un parseur adapté est choisi, le nombre de valeurs devenues invalides est renvoyé, `types_version` du dataset augmente, et la correction survit à un redémarrage et à une nouvelle détection.
- WHEN je reviens à la détection, THEN la correction est effacée.
- WHEN j'exclus une colonne, THEN elle est marquée exclue (les analyses l'ignoreront).
- WHEN je fixe l'ordre d'une ordinale, THEN il est enregistré et renvoyé.

**Page Columns**
- Colonnes à faible confiance en premier ; filtres « to review », par type, exclues ; recherche.
- Sélection multiple → changer le type / exclure / inclure.
- Bandeau explicatif tant que les types ne sont pas validés ; bouton « Validate types ».

## Hors scope

Seuils réglables dans l'interface (page Paramètres, 009) : constants dans le code pour l'instant. Assistant IA pour les noms cryptiques (module futur).
