# 004 — Fiche variable

## Objectif

L'analyse **approfondie** d'une variable : statistiques complètes, tests de normalité, ajustement de lois, transformations, valeurs aberrantes, QQ-plot. C'est la page où l'app montre sa profondeur statistique. Le **plein écran** de la Vue d'ensemble affiche aussi un résumé de ces détails (stats clés, verdict de normalité) avec un lien vers la fiche. Références : [04-fiche-variable.md](../../pages/04-fiche-variable.md), [VISUALS.md](../../VISUALS.md), [DATES.md](../../DATES.md).

## User stories

1. Depuis une carte ou le plein écran, j'ouvre la fiche d'une variable (`/d/:id/variable/:col`). Les flèches ←/→ passent à la variable précédente / suivante (colonnes exclues ignorées).
2. Pour une variable numérique, je vois toutes les statistiques descriptives, chacune avec une info-bulle qui l'explique.
3. Je choisis le visuel principal : histogramme (bins ajustables), KDE, ECDF, boîte, violon, QQ-plot.
4. L'onglet **Tests** me dit si la variable suit une loi normale : 5 tests, chacun avec un verdict en une phrase, la statistique, la p-value, le seuil α (réglable, 0,05 par défaut) et une explication dépliable. Une phrase de synthèse tient compte de la taille de l'échantillon.
5. L'onglet **Loi** classe les lois candidates (AIC / BIC / KS), superpose les 3 meilleures sur l'histogramme, et propose des transformations (log, racine, Box-Cox, Yeo-Johnson) avec un aperçu avant / après. La donnée n'est jamais modifiée.
6. L'onglet **Outliers** compte les valeurs aberrantes selon la méthode choisie (IQR 1,5 / 3, z-score, z-score robuste) et liste les lignes concernées.
7. Pour une catégorie : effectifs, % et % cumulé, entropie, concentration, modalités rares, alerte de déséquilibre, test d'uniformité.
8. Pour une date : plage, granularité, volume par période, heatmap calendrier, jour de semaine / mois / heure, trous dans la série.
9. Pour un texte : longueurs, mots fréquents, vides. Pour un identifiant : unicité, doublons listés, format (longueur, motif).
10. En plein écran depuis la Vue d'ensemble, je vois sous le graphique un panneau de détails adapté au type et un bouton « Open variable page ».

## Critères d'acceptation

**Statistiques (toutes les lignes, calculées par DuckDB)**
- Numérique : nombre, manquants, infinis, zéros, négatifs (avec %), distinctes, moyenne, écart-type, CV, min, P1, P5, P10, Q1, médiane, Q3, P90, P95, P99, max, IQR, MAD, asymétrie, aplatissement (excès), somme.
- GIVEN une colonne de valeurs connues, THEN chaque statistique est égale à celle de numpy / scipy (tolérance 1e-9 relative).

**Tests de normalité** (scipy, sur un échantillon reproductible, graine fixe)
- Shapiro–Wilk (échantillon ≤ 5 000), D'Agostino–Pearson K² (n ≥ 20), Anderson–Darling (valeurs critiques, verdict à 5 %), Jarque–Bera, Lilliefors (KS avec paramètres estimés).
- Les tests portent sur un échantillon de 5 000 valeurs au plus ; la taille de l'échantillon est affichée quand n est plus grand.
- GIVEN 5 000 tirages normaux, THEN aucun test ne rejette à 1 %. GIVEN 5 000 tirages log-normaux, THEN tous rejettent.
- Synthèse : « k tests sur m rejettent la normalité » ; au-delà de 5 000 lignes, rappel que de petits écarts suffisent à rejeter et invitation à regarder le QQ-plot.
- Moins de 8 valeurs ou variable constante : tests non applicables, avec la raison.

**Visuels**
- KDE (scipy `gaussian_kde`, règle de Scott) et ECDF (200 points de quantiles sur toutes les lignes) préparés côté backend.
- QQ-plot contre la normale par défaut, ou contre la loi choisie dans l'onglet Loi ; droite de référence.
- Violon et boîte dessinés à partir d'un échantillon de 5 000 valeurs au plus (mention affichée).

**Ajustement de lois** (sur un échantillon de 10 000 valeurs au plus)
- Continues : normale, log-normale, exponentielle, gamma, Weibull, bêta (si bornée dans [0, 1]), uniforme, Student-t, Pareto, logistique. Une loi n'est essayée que si son support convient (valeurs > 0 pour log-normale, gamma, Weibull, Pareto ; ≥ 0 pour exponentielle).
- Discrètes : Poisson, binomiale négative, géométrique (valeurs entières ≥ 0).
- Classement par AIC, avec BIC, statistique KS et paramètres estimés. GIVEN des tirages gamma, THEN gamma est dans le top 2.
- Transformations : log (si > 0), racine (si ≥ 0), Box-Cox (si > 0, λ estimé), Yeo-Johnson (λ estimé) ; pour chacune : asymétrie et p-value de Shapiro avant / après, histogramme après.

**Outliers**
- IQR ×1,5 et ×3, z-score (|z| > 3), z-score robuste (|0,6745·(x − médiane) / MAD| > 3,5). Bornes, nombre, %, et les 100 lignes les plus extrêmes (numéro de ligne + valeur).

**Catégoriel / booléen** : entropie (bits) et entropie normalisée, indice de Herfindahl, modalités < 1 % (nombre et liste), alerte si une modalité dépasse 80 %, test χ² d'uniformité.

**Date** : plage, granularité, heatmap calendrier (jours, si la plage ≤ 3 ans), trous = périodes vides au pas auto (nombre et 20 premières).

**Texte / identifiant** : distribution des longueurs, 20 mots les plus fréquents, vides ; identifiant : % unique, doublons (20 premiers avec effectif), longueurs min / max, motifs les plus fréquents (lettres → A, chiffres → 9).

**Plein écran (Vue d'ensemble)**
- Numérique : tableau de stats + verdict de normalité. Catégorie : graphique de hauteur bornée et tableau visible sans défiler. Date : plage, pas, trous. Bouton « Open variable page » partout.

**Performance** : fiche d'une colonne numérique de 5 M lignes en < 3 s (stats + tests + KDE) ; l'ajustement de lois, chargé à l'ouverture de l'onglet, en < 5 s.

## Hors scope

Filtre local et « filtrer ces lignes » depuis les outliers (005), « Comparer avec… » (006, bouton visible mais inactif), hétéroscédasticité / stationnarité (module séries temporelles), réglage global des niveaux d'explication (009 ; ici : verdict court + détail dépliable).
