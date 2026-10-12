# Comparer — `/d/:id/compare`

## Rôle

Croiser **2 ou 3 variables** (+ une couleur), voir le bon graphique et le bon test statistique.

## Contenu

- **Sélecteurs** : X, Y, Z (optionnel, pour la 3D), Couleur (optionnel), Facette (optionnel : petits multiples par modalité)
- **Intention** (optionnel) : Distribution · Comparer des groupes · Relation · Composition · Profils. Elle réduit la liste des visuels proposés. Voir [VISUALS.md](../VISUALS.md).
- **Visuel** : liste des visuels compatibles avec les types choisis, le plus adapté présélectionné
- **Graphique** (grand), avec les options propres au visuel : droite de régression / LOWESS, échelle log, normalisation %, Top N
- **Panneau « Test statistique »** à droite, choisi automatiquement selon les types :

| Combinaison | Tests | Taille d'effet |
|---|---|---|
| num × num | Pearson, Spearman, Kendall | r, ρ, τ, R² |
| num × cat (2 groupes) | t de Welch, Mann–Whitney | d de Cohen |
| num × cat (≥ 3 groupes) | ANOVA, Welch-ANOVA, Kruskal–Wallis (+ test de Levene pour l'égalité des variances) | η², ε² |
| cat × cat | χ² d'indépendance, test exact de Fisher (petits effectifs) | V de Cramér |

Chaque test est présenté avec un `TestResult` et ses conditions d'application (« Les variances sont inégales (Levene p < 0,01) → Welch-ANOVA utilisée »).

- **Table des données utilisées** sous le graphique (repliable), exportable.

## 3D

Disponible dès que 3 numériques sont choisies (ou 2 numériques + Z) : **nuage 3D** coloré par la variable Couleur, **surface de densité 3D**, rotation et zoom, bouton « vue de dessus / de face ». Échantillonnage automatique au-delà de 20 000 points (signalé).

## Petits plus

- « Inverser X/Y » en un clic.
- Préremplie depuis une fiche variable (« Comparer avec… ») ou un insight.
- Clic sur un point ou une barre → filtrer sur cette sélection.
- Combinaisons récentes mémorisées.

## Hors V1

Modèles de régression complets (diagnostics, résidus, hétéroscédasticité) : module ML.
