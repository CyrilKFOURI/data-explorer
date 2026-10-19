# Builder KPI — `/d/:id/kpi`

> Module (Sprint 6). Jalon : [022](../features/022-kpi-builder/spec.md). Intention d'origine : [modules-futurs/kpi-builder.md](../modules-futurs/kpi-builder.md).

## Rôle

Obtenir en un clic un indicateur métier (tuiles, graphique, tableau croisé), puis le personnaliser et l'enregistrer. Le détail des règles automatiques est dans la spec 022 (sections 4, 5 et 9 bis).

## Principes UX

- **Automatique d'abord.** La page s'ouvre sur un KPI suggéré déjà calculé. Les autres suggestions sont des pastilles en haut ; « Split by » propose les meilleurs regroupements.
- **Builder en phrase** : « Show Sum of revenue per month of order_date over all dates, split by country ». Un changement de données active **Calculate** ; rien ne se recalcule à chaque réglage.
- **Customize** : chaque réglage affiche « Auto · choix » et sa raison. Une option impossible est grisée avec la raison. Un réglage modifié porte une pastille et « Reset to auto ». Les réglages d'affichage s'appliquent sans recalcul.
- **Why this view** : une ligne sous le graphique explique les choix automatiques.

## Disposition (revue le 2026-10-19, 2e version)

Pas de cartes : la page se lit comme un rapport. Les groupes sont séparés par des filets et de l'espace, jamais par des blocs arrondis.

```
KPI builder                                                   [Saved KPIs 3 ▾]  + New KPI
Try  Rows   Total revenue   Distinct customers   % churned

Show  Sum̲ ̲o̲f̲ ̲r̲e̲v̲e̲n̲u̲e̲ ▾  + measure
per  Auto (month) ▾  of  order_date ▾  over  all dates ▾   ☑ page filters
split by  country ▾  then  segment ▾  + split
─────────────────────────────────────────────────────────── Changes not applied  [Calculate] [Save]

 Total revenue          │ Orders               │ Revenue per order
 1.2M  Sep 2026  ~~~~~  │ 8,412  Sep 2026 ~~~  │ 142.6  Sep 2026 ~~~
 ↑ 4 % vs previous      │ ↑ 2 % vs previous    │ ↑ 1.9 % vs previous
──────────────────────────────────────────────────────────────────────────────────────────
Revenue by month by country                                                    Customize
[graphique, posé sur la page]
Why this view: …      Split by: + country  + segment
Table                                                     Swap  Copy  Download CSV
[tableau : filets horizontaux seulement]
```

- **Builder en phrase** : chaque choix est un mot souligné (menu natif, largeur ajustée au texte) ; les ajouts (+ measure, + ratio, + split) sont des liens dans la phrase ; sans date, la phrase dit « over the whole data ».
- **Chiffres clés** : une bande entre deux filets, une colonne par mesure séparée par un filet vertical ; une seule mesure occupe toute la bande, mini-courbe étirée.
- **Saved KPIs** : menu dans l'en-tête.
- **Customize** : colonne à droite des résultats, séparée par un filet vertical (pas de carte).

## États

- **Aucune colonne utilisable** : « Needs at least one column to count or group by ».
- **Sans date** : la section « Over time » affiche « No date column — values over the whole data ».
- **0 ligne** : « No rows in this period » et le bouton « Use all dates ».
- **Colonne disparue** dans un KPI enregistré : message, et le champ à corriger mis en évidence.
- **Plafond dépassé** (5 000 points / 50 000 cellules) : message et grain plus grossier proposé en un clic.

## URL

`?kpi=<id>` pour un KPI enregistré ; sinon `?def=<définition encodée>`. Les filtres globaux s'appliquent si « Use the page filters » est coché.
