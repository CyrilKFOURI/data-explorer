# 018 — Machine learning : prédire un nombre sous forme de classes

## Objectif

Transformer une cible numérique en **classes ordonnées** (prix bas / moyen / haut) en quelques secondes, pour la traiter comme une classification. L'interface doit être la plus simple possible : un nombre de classes, une façon de découper, un aperçu en direct. Référence : [11-machine-learning.md](../../pages/11-machine-learning.md).

## Pourquoi

Prédire une classe est souvent plus utile et plus robuste que prédire un nombre exact (« ce véhicule sera-t-il cher ? »), supporte mieux les valeurs extrêmes, et donne des résultats plus lisibles (matrice de confusion).

## User stories

1. Ma cible est `price` : sous le sélecteur de cible apparaît **Predict as  [ Number | Classes ]**. Je clique **Classes**.
2. Un panneau compact se déplie, déjà rempli : **3 classes, Equal counts**, nommées **Low · Medium · High**, avec l'histogramme de `price` et les limites tracées dessus. Le modèle se réentraîne en classification.
3. Je change le nombre de classes avec **[−] 3 [+]** (2 à 10) : limites, noms et effectifs se mettent à jour en direct.
4. Je change la façon de découper : **Equal counts · Equal width · Natural breaks · Custom**.
5. En **Custom**, je fais glisser les limites sur l'histogramme ou je tape leur valeur ; **Round values** arrondit les limites à des nombres « ronds » (12 500 plutôt que 12 487,33).
6. Je renomme une classe en cliquant sur son nom.
7. Un avertissement me prévient si une classe est trop petite, avec une action : « Very high has only 21 rows — models will struggle to learn it. [Use 4 classes] »
8. Les résultats tiennent compte de l'ordre des classes : en plus des métriques habituelles, « 94 % of predictions are right or off by one class ».

## Interface (dans la colonne Réglages, sous la cible)

```
Predict   [ price ▾ ]
          [ Number | Classes ]

Classes   [−]  3  [+]
Split by  Equal counts ▾                      Round values ☑
┌──────────────────────────────────────────────┐
│ ▁▂▅▇█▇▅▃▂▁▁  histogramme                      │
│      │         │          ← limites (glissables en Custom)
└──────────────────────────────────────────────┘
● Low      ≤ 12 500            1 640  33 %  ▇▇▇▇
● Medium   12 500 – 21 000     1 655  33 %  ▇▇▇▇
● High     > 21 000            1 705  34 %  ▇▇▇▇
```

- Pas de fenêtre ni d'étape séparée : tout reste dans la colonne de réglages, l'histogramme fait toute sa largeur (~120 px de haut).
- Chaque classe : pastille de couleur (séquentielle, une teinte du clair au foncé : l'ordre se voit), nom éditable, intervalle, effectif, %, barre proportionnelle.
- Le « Split by » explique chaque méthode en une ligne dans le menu :
  - **Equal counts** — same number of rows in each class (quantiles). *Défaut : classes équilibrées, le cas le plus simple à apprendre.*
  - **Equal width** — same price range for each class.
  - **Natural breaks** — limits placed where the data has gaps (Jenks).
  - **Custom** — set the limits yourself.

## Règles

- **Noms par défaut** : 2 → Low, High ; 3 → Low, Medium, High ; 4 → Low, Medium-low, Medium-high, High ; 5 → Very low, Low, Medium, High, Very high ; 6 à 10 → Class 1 … Class k. Un nom modifié est conservé si le nombre de classes change (tant que la classe existe).
- **Intervalles** : (a, b], la première classe inclut le minimum ; affichage « ≤ b », « a – b », « > a » dans l'unité et le format de la colonne.
- **Equal counts** : quantiles sur toutes les lignes filtrées ayant une cible. Avec beaucoup d'ex-aequo, des classes peuvent être inégales (une limite ne coupe jamais une même valeur en deux) ; l'app le dit (« many rows share the value 10 000, so classes are not exactly equal »). Si deux limites tombent sur la même valeur, la classe vide est fusionnée et le nombre de classes réel est affiché.
- **Equal width** : de min à max ; option **Ignore outliers** (activée par défaut) qui calcule la largeur entre les percentiles 1 et 99, les extrêmes allant dans la première / dernière classe.
- **Natural breaks** : Fisher–Jenks exact (programmation dynamique) sur un échantillon trié de 5 000 valeurs au plus.
- **Round values** : arrondi de chaque limite à 2 chiffres significatifs (puis 3 si deux limites se confondent).
- **Classes trop petites** : avertissement si une classe < 5 % des lignes ou < 30 lignes ; action proposée (moins de classes, ou Equal counts).
- **Fuite** : la colonne source (`price`) est automatiquement exclue des variables explicatives, ainsi que les colonnes de fuite suspectée vis-à-vis du nombre d'origine (017, R-SEL-01 et R-SEL-06).
- **Découpage calculé sur toutes les lignes** (il ne dépend que de la cible, pas des variables explicatives : pas de fuite), et enregistré dans l'expérience (limites, noms, méthode) pour que chaque run utilise exactement les mêmes classes.
- **Modèle** : classification multiclasse **ordonnée** ; mêmes modèles que la classification (Logistic par défaut). Métriques ajoutées : « exact or off by one » (part des prédictions à au plus une classe d'écart) et erreur moyenne en nombre de classes ; matrice de confusion dans l'ordre des classes.
- **Suggestion** : une cible numérique discrète à ≤ 10 valeurs (note 1–5) affiche « Predict as classes? » avec une classe par valeur.

## Critères d'acceptation

- GIVEN 3 000 valeurs uniformes WHEN 3 classes Equal counts THEN chaque classe compte 1 000 ± 1 lignes.
- GIVEN [1, 2, 3, 10, 11, 12, 30, 31] WHEN 3 classes Natural breaks THEN les limites séparent {1,2,3}, {10,11,12}, {30,31}.
- GIVEN 70 % des valeurs égales à 10 000 WHEN 4 classes Equal counts THEN aucune valeur n'est coupée en deux, le message d'ex-aequo s'affiche et les classes vides sont fusionnées.
- GIVEN des limites 12 487,33 et 20 912,8 WHEN Round values THEN 12 000 et 21 000.
- Le changement du nombre de classes ou de la méthode met l'aperçu à jour en moins de 100 ms (calcul dans le navigateur sur l'histogramme fin et l'échantillon trié fournis par l'API), puis relance l'entraînement (avec un délai de 600 ms après le dernier changement, pour ne pas entraîner à chaque clic).
- La colonne source n'apparaît jamais dans les variables explicatives.
- Accessibilité : limites glissables aussi au clavier (flèches, Maj + flèches = pas ×10), et éditables par saisie ; chaque classe a un nom textuel (pas seulement une couleur).

## Hors scope

Enregistrer la colonne discrétisée comme nouvelle colonne du dataset ; discrétiser les variables explicatives ; classes définies par des règles sur plusieurs colonnes.
