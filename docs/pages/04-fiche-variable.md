# Fiche variable — `/d/:id/variable/:col`

## Rôle

L'analyse **approfondie** d'une seule variable. C'est ici que l'app montre son niveau statistique.

## Contenu commun

- En-tête : nom, `TypeBadge`, rôle, flèches ←/→ (variable précédente / suivante, aussi Maj+←/→), « Comparer avec… »
- Grand graphique principal + sélecteur de visuel
- Filtre local rapide sur cette variable (s'ajoute aux filtres globaux)

## Variable numérique (continue ou discrète)

**Statistiques descriptives** (chacune avec une info-bulle d'explication) : nombre, manquants, infinis, zéros, négatifs (avec %), distinctes, moyenne, écart-type, coefficient de variation, min, Q1, médiane, Q3, max, P1 / P5 / P10 / P90 / P95 / P99, IQR, MAD, asymétrie (skewness), aplatissement (kurtosis), somme.

**Visuels** : histogramme (règle de bins Freedman–Diaconis, ajustable), KDE, ECDF, boîte, violon, **QQ-plot** contre la loi choisie.

**Normalité** (onglet « Tests ») : chaque test est affiché avec un `TestResult` (verdict, statistique, p-value, seuil α réglable à 0,05 par défaut, explication).
- Tous les tests portent sur un échantillon reproductible de 5 000 valeurs au plus (signalé)
- Shapiro–Wilk
- D'Agostino–Pearson K²
- Anderson–Darling (p-value interpolée des tables, bornée entre 0,01 et 0,15)
- Jarque–Bera
- Lilliefors (Kolmogorov–Smirnov à paramètres estimés, p-value par Monte Carlo)
- Synthèse en une phrase : « 4 tests sur 5 rejettent la normalité. Avec n = 120 000, même de petits écarts sont détectés : regardez le QQ-plot. »

**Ajustement de lois** (onglet « Loi ») :
- Lois candidates : normale, log-normale, exponentielle, gamma, Weibull, bêta (si bornée), uniforme, Student-t, Pareto, logistique. Discrètes : Poisson, binomiale négative, géométrique.
- Classement par AIC / BIC + statistique KS. Paramètres estimés affichés.
- Superposition des 3 meilleures densités sur l'histogramme ; QQ-plot de la meilleure.
- Phrase : « La loi log-normale décrit le mieux cette variable (AIC le plus bas) ; une transformation log la rendrait proche de la normale. »
- Suggestion de **transformations** (log, racine, Box-Cox, Yeo-Johnson) avec un aperçu avant / après. Simple aperçu : la donnée n'est pas modifiée.

**Valeurs aberrantes** (onglet « Outliers ») : méthodes IQR (1,5 et 3), z-score, z-score robuste (MAD), au choix ; nombre et % ; liste des lignes concernées, filtrable en un clic.

## Variable catégorielle / booléenne

Effectifs et % (Top N + « Autres » + manquants), tableau complet paginé avec % cumulé, entropie et indice de concentration, modalités rares (< 1 %), avertissement de déséquilibre (« "A" représente 87 % des lignes »). Test d'uniformité (χ² d'ajustement) en option.

## Variable date

Plage couverte, granularité détectée (jour, mois…), volume par période (pas automatique), heatmap calendrier, répartition par jour de la semaine, mois et heure, **trous** dans la série (périodes manquantes). L'analyse temporelle avancée vient avec le module [séries temporelles](../modules-futurs/series-temporelles.md).

## Variable texte libre / identifiant

Texte : longueur (distribution), mots les plus fréquents, valeurs vides. Identifiant : unicité, doublons (liste), format (longueur, motif).

## Hors V1

Hétéroscédasticité, stationnarité, autocorrélation : module séries temporelles (et régression dans le module ML).
