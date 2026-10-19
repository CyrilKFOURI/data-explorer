# Builder KPI — `/d/:id/kpi`

> Module (Sprint 6). Jalon : [022](../features/022-kpi-builder/spec.md). Intention d'origine : [modules-futurs/kpi-builder.md](../modules-futurs/kpi-builder.md).

## Rôle

Obtenir en un clic un indicateur métier (tuiles, graphique, tableau croisé), puis le personnaliser et l'enregistrer. Le détail des règles automatiques est dans la spec 022 (sections 4, 5 et 9 bis).

## Principes UX

- **Automatique d'abord.** La page s'ouvre sur un KPI suggéré déjà calculé. Les autres suggestions sont des pastilles en haut ; « Split by » propose les meilleurs regroupements.
- **Builder en trois colonnes** : Measure · Over time (date, grain, période) · Split by. Un changement de données active **Calculate** ; rien ne se recalcule à chaque réglage.
- **Customize** : chaque réglage affiche « Auto · choix » et sa raison. Une option impossible est grisée avec la raison. Un réglage modifié porte une pastille et « Reset to auto ». Les réglages d'affichage s'appliquent sans recalcul.
- **Why this view** : une ligne sous le graphique explique les choix automatiques.

## Disposition (revue le 2026-10-19)

Toute la largeur sert au KPI : pas de colonne latérale vide.

```
┌ KPI builder ── description ─────────────────────────── [Saved KPIs · 3 ▾] [+ New KPI] ┐
│ ✦ Suggested: [Rows] [Total revenue] [Distinct customers] [% churned] …                 │
├ Builder (3 colonnes, une par question) ────────────────────────────────────────────────┤
│ MEASURE                  │ OVER TIME                     │ SPLIT BY                    │
│ [Sum of ▾][revenue ▾] ×  │ [order_date            ▾]     │ [country ▾] ×               │
│ + Measure  + Ratio       │ [Auto · Month ▾][All dates ▾] │ then [segment ▾] ×          │
│                          │ ☑ Use the page filters        │ + Split                     │
│ ── Changes not applied yet ─────────────────────────────── [Calculate] [Save] ─────────│
├ Tuiles : toute la largeur (une seule tuile = une bande large, mini-courbe étirée) ──────┤
│ Graphique(s) ─────────────────────────────────────────────────── [Customize]           │
│ Why this view · Split by: [country] [segment]                                          │
│ Tableau croisé ───────────────────────────────── [Swap] [Copy] [Download CSV]          │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

- **Saved KPIs** : menu dans l'en-tête (compteur), avec ouvrir, renommer, dupliquer, supprimer.
- **Builder** : trois colonnes de largeur égale sur grand écran, empilées sur petit écran ; contrôles pleine largeur de leur colonne ; pied avec l'état (« Changes not applied yet ») et les boutons.
- Le panneau Customize s'ouvre à droite des résultats : sections Chart · Values · Table · Groups · Format.

## États

- **Aucune colonne utilisable** : « Needs at least one column to count or group by ».
- **Sans date** : la section « Over time » affiche « No date column — values over the whole data ».
- **0 ligne** : « No rows in this period » et le bouton « Use all dates ».
- **Colonne disparue** dans un KPI enregistré : message, et le champ à corriger mis en évidence.
- **Plafond dépassé** (5 000 points / 50 000 cellules) : message et grain plus grossier proposé en un clic.

## URL

`?kpi=<id>` pour un KPI enregistré ; sinon `?def=<définition encodée>`. Les filtres globaux s'appliquent si « Use the page filters » est coché.
