# Comparer — `/d/:id/compare`

## Rôle

Croiser **2 ou 3 variables** (+ une couleur), voir le bon graphique et le bon test statistique.

## Contenu

- **Sélecteurs** : X, Y, Z (optionnel, pour la 3D), Couleur (optionnel), bouton « Inverser X/Y »
- **Visuel** : le plus adapté aux types est présélectionné ; bascule entre les vues compatibles (voir [006 spec](../features/006-comparer/spec.md))
- Ligne « n lignes utilisées » (lignes où toutes les variables choisies sont renseignées) et mention d'échantillon le cas échéant
- **Graphique** (grand), avec les options propres au visuel : droite de régression / LOWESS, échelle log, normalisation %, Top N
- **Panneau « Test statistique »** à droite, choisi automatiquement selon les types :

| Combinaison | Tests | Taille d'effet |
|---|---|---|
| num × num | Pearson, Spearman, Kendall | r, ρ, τ, R² |
| num × cat (2 groupes) | t de Welch, Mann–Whitney | d de Cohen |
| num × cat (≥ 3 groupes) | ANOVA, Welch-ANOVA, Kruskal–Wallis (+ test de Levene pour l'égalité des variances) | η², ε² |
| cat × cat | χ² d'indépendance, test exact de Fisher (petits effectifs) | V de Cramér |
| date × num | Mann-Kendall (une valeur par période) + pente de Sen et IC 95 % | τ de Kendall |

Chaque test est présenté avec un `TestResult` et ses conditions d'application (« Les variances sont inégales (Levene p < 0,01) → Welch-ANOVA utilisée »).

- **Table des données utilisées** sous le graphique (repliable), exportable.

## Vue temporelle (date × num) — [011](../features/011-vue-temporelle/spec.md)

Agrégation par période (Auto : pas typique des dates, relevé au-delà de 400 périodes ; Sum pour les rôles `amount`/`quantity`, Mean sinon), moyenne et écart-type glissants (fenêtre Auto selon la période, arrière ou centrée), bande ± 1σ (série unique), une courbe par groupe avec Couleur. Barre d'options (Period, Aggregate, Window, alignement, tracés) dans l'URL ; libellé résumé ; périodes incomplètes au début / à la fin signalées et exclues du test (Sum, Count) ; avertissement d'autocorrélation ; table « Data used » ; lien « Analyze as time series → » (actif avec 012).

## 3D

Disponible dès que 3 numériques sont choisies (ou 2 numériques + Z) : **nuage 3D** coloré par la variable Couleur, **surface de densité 3D**, rotation et zoom, bouton « vue de dessus / de face ». Échantillonnage automatique au-delà de 20 000 points (signalé).

## Petits plus

- « Inverser X/Y » en un clic.
- Préremplie depuis une fiche variable (« Comparer avec… ») ou un insight.
- Clic sur un point ou une barre → filtrer sur cette sélection.
- Combinaisons récentes mémorisées.

## Hors V1

Facettes (petits multiples), sélecteur d'intention, surface de densité 3D, clic sur un point pour filtrer.


Modèles de régression complets (diagnostics, résidus, hétéroscédasticité) : module ML.
