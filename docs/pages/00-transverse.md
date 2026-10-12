# Éléments transverses

Présents sur toutes les pages d'un dataset (`/d/:id/...`).

## Barre latérale (gauche, repliable)

- **Dataset** : Colonnes · Vue d'ensemble · Comparer · Corrélations · Données
- **Modules** : vide en V1 ; les modules activés s'y ajoutent automatiquement (Séries temporelles, ML…)
- En bas : Paramètres, bascule clair / sombre

## Barre du haut

- Nom du dataset (renommable) + sélecteur pour changer de dataset
- Recherche / palette de commandes (⌘K ou Ctrl+K) : aller à une variable, une page, une action (« Exporter », « Effacer les filtres »)

## Bandeau de résumé

Toujours visible, et il tient compte des filtres actifs.

| Indicateur | Détail au survol |
|---|---|
| Lignes | Après filtres / total |
| Colonnes | Dont ignorées |
| Manquants | % de cellules vides ; clic → colonnes triées par % de manquants |
| Lignes dupliquées | Nombre et % |
| Colonnes dupliquées | Colonnes identiques en contenu (pas seulement en nom) |
| Mémoire | Taille totale, moyenne par ligne |
| Types | Mini-barre de répartition : numérique / catégoriel / date / booléen / texte / identifiant |

## Barre de filtres globaux

- Filtres actifs affichés en puces : `pays ∈ {FR, BE}` · `âge ≥ 18` · bouton ✕ sur chaque puce
- **+ Filtre** : colonne → opérateur → valeur. Le formulaire s'adapte au type de la colonne :
  - numérique : =, ≠, >, ≥, <, ≤, entre, est vide
  - date : avant, après, entre, période relative (« 12 derniers mois »)
  - catégoriel : est parmi (multi-sélection avec recherche et « tout sélectionner »), contient, commence par, est vide
  - booléen : vrai / faux / vide
- Logique **ET / OU** entre les règles
- Toujours visible : « 12 340 lignes sur 1 200 000 », « Tout effacer »
- Filtres **enregistrables** sous un nom et réutilisables
- Raccourci : depuis un graphique, clic sur une barre ou une zone → « Filtrer sur cette valeur » ou « Exclure »

## Comportements communs

- L'URL contient la page, la variable et les filtres : partageable, rechargeable.
- Squelettes de chargement à la forme du contenu ; erreurs expliquées (« Ce fichier Excel est protégé par mot de passe »).
- Notifications discrètes en bas à droite pour les tâches longues (import, recalcul).
