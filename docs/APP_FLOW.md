# App Flow

## Liste des écrans

### V1

| Écran | Route | Rôle | Doc |
|---|---|---|---|
| Accueil / Import | `/` | Importer un fichier ou dossier, rouvrir un dataset récent | [pages/01-accueil-import.md](pages/01-accueil-import.md) |
| Colonnes | `/d/:id/columns` | Vérifier et corriger les types détectés | [pages/02-colonnes.md](pages/02-colonnes.md) |
| Vue d'ensemble | `/d/:id/overview` | Résumé + grille de toutes les variables | [pages/03-vue-ensemble.md](pages/03-vue-ensemble.md) |
| Fiche variable | `/d/:id/variable/:col` | Analyse approfondie d'une variable | [pages/04-fiche-variable.md](pages/04-fiche-variable.md) |
| Comparer | `/d/:id/compare` | Croiser 2–3 variables, tests, 3D | [pages/05-comparer.md](pages/05-comparer.md) |
| Corrélations | `/d/:id/correlations` | Liens entre toutes les variables + insights | [pages/06-correlations.md](pages/06-correlations.md) |
| Données | `/d/:id/data` | Table filtrée, exports | [pages/07-donnees.md](pages/07-donnees.md) |
| Paramètres | `/settings` | Seuils de détection, affichage, cache, thème | [pages/08-parametres.md](pages/08-parametres.md) |

Éléments présents sur tous les écrans d'un dataset (barre latérale, bandeau de résumé, barre de filtres, palette de commandes) : [pages/00-transverse.md](pages/00-transverse.md).

### Modules futurs (pas pour maintenant)

Routes réservées, chacune ajoutée par son module : `/d/:id/timeseries`, `/d/:id/ml`, `/d/:id/kpi`, `/d/:id/synthetic`. Voir [modules-futurs/](modules-futurs/README.md).

## Parcours principal

```
Accueil ──import──▶ Colonnes ──« Valider les types »──▶ Vue d'ensemble ──clic sur une carte──▶ Fiche variable
                     (1ʳᵉ ouverture                        │                                      │
                      seulement)                           └── « Comparer avec… » ───────────────▶ Comparer
```

1. **Import** : glisser-déposer un fichier, ou coller le chemin d'un dossier → aperçu (colonnes, nombre de lignes estimé) → options (colonnes à garder, échantillon %) → « Importer ». La progression s'affiche.
2. **Colonnes** (proposé automatiquement au premier import) : tableau des colonnes avec type détecté, confiance et raisons. Les colonnes à faible confiance sont en tête. L'utilisateur corrige ce qui est faux, puis « Valider ». Il peut passer cette étape et y revenir à tout moment.
3. **Vue d'ensemble** : bandeau de résumé, alertes qualité (colonnes vides, doublons, types douteux), puis grille de toutes les variables, 3 par ligne, paginée.
4. **Fiche variable** : statistiques complètes, lois ajustées, tests de normalité, valeurs aberrantes. ←/→ pour passer à la variable suivante.
5. **Comparer / Corrélations** : depuis une fiche (« Comparer avec… ») ou depuis un insight (« Voir le graphique »).

## Parcours secondaires

- **Rouvrir un dataset** : Accueil → dataset récent → retour directement à la dernière page consultée, avec ses filtres. Si la source a changé : bandeau « La source a été modifiée — Réimporter ? ».
- **Filtrer** : depuis la barre de filtres (n'importe quelle page) ou depuis un graphique (clic sur une barre → « Filtrer sur cette valeur »). Le filtre s'applique à toutes les pages.
- **Corriger un type en cours de route** : clic sur un badge de type, n'importe où → menu → nouveau type. Les graphiques concernés se recalculent ; « Annuler » reste disponible.
- **Voir toutes les modalités** : carte catégorielle → plein écran.
- **Explorer à partir d'un insight** : Corrélations → phrase d'insight → « Voir » → Comparer, pré-rempli.
- **Exporter** : un graphique (PNG/SVG), les données d'un graphique (CSV), le sous-ensemble filtré (CSV/Parquet) depuis Données.
- **Changer de dataset** : sélecteur dans la barre du haut, ou ⌘K.
