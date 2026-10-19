# Builder KPI — `/d/:id/kpi`

> Module (Sprint 6). Jalon : [022](../features/022-kpi-builder/spec.md). Intention d'origine : [modules-futurs/kpi-builder.md](../modules-futurs/kpi-builder.md).

## Rôle

Obtenir en un clic un indicateur métier (tuiles, graphique, tableau croisé), puis le personnaliser et l'enregistrer. Le détail des règles automatiques est dans la spec 022 (sections 4, 5 et 9 bis).

## Principes UX

- **Automatique d'abord.** La page s'ouvre sur un KPI suggéré déjà calculé. Les autres suggestions sont des pastilles en haut ; « Split by » propose les meilleurs regroupements.
- **Builder en une ligne** : Measure · Over time · Split by · Period. Un changement de données active **Calculate** ; rien ne se recalcule à chaque réglage.
- **Customize** : chaque réglage affiche « Auto · choix » et sa raison. Une option impossible est grisée avec la raison. Un réglage modifié porte une pastille et « Reset to auto ». Les réglages d'affichage s'appliquent sans recalcul.
- **Why this view** : une ligne sous le graphique explique les choix automatiques.

## Disposition

```
┌ Saved ─────┐ ┌ Suggested: [Rows] [Total revenue] [Distinct customers] … ────────────────┐
│ KPI 1      │ │ Measure [Sum of revenue ▾] [+ Measure] [+ Ratio]                         │
│ KPI 2      │ │ Over time [order_date ▾] [Auto · month ▾]  Period [All ▾]  ☑ page filters│
│ + New      │ │ Split by [country ▾] [+]                         [Calculate] [Save]      │
│            │ ├──────────────────────────────────────────────────────────────────────────┤
│            │ │ Tuiles (une par mesure)                                                  │
│            │ │ Graphique(s) — un par mesure, axe x partagé           [Customize ▸]      │
│            │ │ Why this view · Split by: [country] [segment] [status]                   │
│            │ │ Tableau croisé                          [⇄] [Copy] [Download CSV]        │
└────────────┘ └──────────────────────────────────────────────────────────────────────────┘
```

Le panneau Customize s'ouvre à droite : sections Chart · Table · Values · Groups · Format.

## États

- **Aucune colonne utilisable** : « Needs at least one column to count or group by ».
- **Sans date** : la section « Over time » affiche « No date column — values over the whole data ».
- **0 ligne** : « No rows in this period » et le bouton « Use all dates ».
- **Colonne disparue** dans un KPI enregistré : message, et le champ à corriger mis en évidence.
- **Plafond dépassé** (5 000 points / 50 000 cellules) : message et grain plus grossier proposé en un clic.

## URL

`?kpi=<id>` pour un KPI enregistré ; sinon `?def=<définition encodée>`. Les filtres globaux s'appliquent si « Use the page filters » est coché.
