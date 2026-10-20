# Données synthétiques — `/d/:id/synthetic`

> Module (Sprint 7). Jalon : [023](../features/023-donnees-synthetiques/spec.md). Intention d'origine : [modules-futurs/donnees-synthetiques.md](../modules-futurs/donnees-synthetiques.md).

## Rôle

Générer un jeu artificiel qui ressemble au dataset, dire à quel point il est fidèle et à quel point il protège les lignes réelles, puis l'enregistrer comme nouveau dataset. Les formules sont dans la spec 023 (sections 3 à 7).

## Principes UX

- **Automatique d'abord.** La page s'ouvre prête à générer : traitement de chaque colonne avec sa règle et sa raison, méthode recommandée, autant de lignes que l'original. Un clic : **Generate**.
- **Même grammaire que le builder KPI** : une barre de réglages compacte et collante, un libellé court devant chaque menu, pas de cartes. Les groupes sont séparés par des filets.
- **Réel et synthétique ont chacun une couleur fixe sur toute la page** :
  - réel : gris foncé plein ;
  - synthétique : couleur d'accent avec contour, pour ne pas dépendre de la couleur.
- **Chaque chiffre a son verdict en une phrase**, et chaque détail se consulte en un clic.

## Disposition

```
Synthetic data                                              [Runs 3 ▾]  Compare
┌ barre collante ──────────────────────────────────────────────────────────────────┐
│ Method [Sequential CART ★ ▾] │ Rows [5 000] │ Seed [42] │ ☐ Smooth numbers        │
│ 12 of 14 columns modelled · Edit columns                              [Generate] │
└──────────────────────────────────────────────────────────────────────────────────┘
CART: best fidelity on mixed columns.

Columns (dépliable ; ouvert tant qu'aucun run n'existe)
 customer_id   identifier   Keep unique ▾   R-SYN-05  New identifiers in the same format
 revenue       continuous   Model ▾         R-SYN-01  Bounds 0 – 9 840, 2 decimals
 comment       text         Leave out ▾     R-SYN-06  Free text could leak real content

── Après génération ──────────────────────────────────────────────────────────────
 Diagnostic   100 %  │ Quality   88 %     │ Detection   71 %          │ Privacy   96 %
 All values valid    │ Very close         │ Hard to tell apart        │ No copied rows
Columns · Links · Checks · Privacy · Utility · Overview · Data
```

- **Bande des 4 chiffres** : grands nombres tabulaires entre deux filets, verdict en dessous ; pas de cartes.
- **Columns** : une ligne compacte par colonne, de la plus abîmée à la moins abîmée : nom, type, score (KS ou TV), mini-histogramme superposé, plus grosse différence en clair. Un clic déplie le détail : bande de base, histogramme ou ECDF superposés, statistiques appariées avec Δ, valeurs fréquentes et extrêmes croisées (nombres) ; tableau aligné et barres appariées (catégories). « Overlay a target » en tête de l'onglet.
- **Links** : trois matrices (réel, synthétique, |écart| plafonné à 0,3), les 5 paires les plus abîmées ; un clic sur une case ou une paire ouvre la paire côte à côte.
- **Checks** : détail du Diagnostic (un contrôle par ligne, colonnes en défaut nommées), propriétés Column shapes et Column pair trends (« Meets threshold »), couverture et vides.
- **Privacy** : les mesures avec leur lecture, distributions des DCR superposées, valeurs rares reproduites, CAP en option (colonnes connues + colonne sensible → Run). Rappel : pas de confidentialité différentielle.
- **Utility** : choisir une cible → Run ; deux scores côte à côte (entraîné sur réel / sur synthétique, testés sur les mêmes lignes réelles) et leur rapport.
- **Overview** : nuage moyenne / écart-type (log) et PCA ajustée sur le réel ; colonnes laissées de côté avec leur raison.
- **Data** : aperçu des 100 premières lignes ; **Save as dataset**, Download CSV, Download Parquet.
- **Progression** : à la place de la bande des chiffres, les étapes (Loading · Learning & generating · Evaluating · Saving) et **Cancel** ; pour CTGAN et TVAE, une barre suit les époques (« Epoch 120 / 300 · loss … »).
- **Méthodes profondes (023b)** : CTGAN et TVAE dans le menu Method, avec le badge « Deep · GPU » ou « Deep · CPU (slow) ». Sans PyTorch, elles sont grisées avec la raison. Quand l'une d'elles est choisie, la barre ajoute **Epochs** (Auto, avec la valeur prévue) et une pastille **GPU · <carte>** ou **CPU** qu'un clic bascule pour ce run ; sans carte prête, elle reste sur CPU avec la raison. L'appareil utilisé, les époques et un éventuel repli sur le CPU s'affichent avec le run (Overview, Runs, comparaison).
- **Runs** : menu en haut à droite (méthode, lignes, Quality, date) ; cocher 2 à 5 runs → **Compare** : tableau côte à côte, meilleur score marqué, barres groupées par propriété.

## États

- **Moins de 50 lignes** ou **aucune colonne modélisable** : message et lien vers Columns.
- **Run en échec** : message de l'erreur, réglages conservés.
- **Annulé** : « Stopped: nothing was saved. »
- **Dataset créé** : bandeau « Saved as <nom> » avec le lien vers son Overview ; l'en-tête du nouveau dataset affiche « Synthetic, from <source> ».

## Paramètres › Compute

- « Use the GPU when available » (On / Off), avec la mention « Used by the deep models (CTGAN, TVAE, TimeGAN), coming next ».
- État détecté via `nvidia-smi` : carte, mémoire, pilote, ou « No GPU found » ; bouton **Check again**.

## URL

`?run=<id>` ouvre un run ; `&tab=columns|links|checks|privacy|utility|overview|data`.
