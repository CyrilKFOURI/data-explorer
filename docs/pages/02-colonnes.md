# Colonnes — `/d/:id/columns`

## Rôle

Vérifier et corriger les **types** détectés, l'étape dont dépend tout le reste. La logique de détection est décrite dans [COLUMN_DETECTION.md](../COLUMN_DETECTION.md).

## Contenu

**Tableau des colonnes**, une ligne par colonne :

| Colonne | Contenu |
|---|---|
| Nom | En monospace, renommable pour l'affichage (le nom d'origine reste visible) |
| Type d'analyse | `TypeBadge` modifiable (menu déroulant) |
| Rôle | Âge, montant, pays… modifiable, ou « aucun » ; menu compact dont la liste défile (320 px max, jamais hors écran). Le menu des types se limite aussi à la hauteur disponible |
| Confiance | Haute / moyenne / faible, avec icône |
| Raisons | « Nom contient *age* · entiers 0–97 · 84 valeurs distinctes » |
| Aperçu | 5 valeurs exemples + mini-sparkline de la distribution |
| Qualité | % de manquants, nombre de distinctes |
| Inclure | Case à cocher (exclure une colonne de toutes les analyses) |

## Interactions

- Tri par défaut : **confiance faible en premier**, puis ordre du fichier.
- Filtres rapides : par type, « à vérifier » (confiance faible ou moyenne), « exclues ».
- Sélection multiple → changer le type de plusieurs colonnes à la fois.
- Changer un type montre tout de suite l'effet : l'aperçu se recalcule, et une alerte s'affiche si la conversion fait apparaître des valeurs invalides (« 3 % des valeurs ne sont pas des dates → elles deviendront vides »).
- « Revenir à la détection » par colonne, ou pour toutes ; Ctrl+Z.
- Bouton **« Valider les types »** → Vue d'ensemble. Au premier import, un bandeau explique l'étape. On peut toujours la passer.

## Petits plus

- Pour un numérique discret, rappel : « Affiché comme catégoriel (barres) car seulement 6 valeurs entières ».
- Suggestion quand une colonne ressemble à une autre (doublon de contenu) : « Identique à `client_id` — l'exclure ? ».
- Ordinal : glisser-déposer pour fixer l'ordre des modalités.

## Cas limites

Colonnes 100 % vides ou constantes : affichées, grisées, avec « ignorée » par défaut. Noms de colonnes en double dans la source : suffixés (`nom`, `nom_2`) avec un avertissement.
