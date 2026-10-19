# Builder KPI — `/d/:id/kpi`

> Module (Sprint 6). Jalon : [022](../features/022-kpi-builder/spec.md). Intention d'origine : [modules-futurs/kpi-builder.md](../modules-futurs/kpi-builder.md).

## Rôle

Obtenir en un clic un indicateur métier (tuiles, graphique, tableau croisé), puis le personnaliser et l'enregistrer. Le détail des règles automatiques est dans la spec 022 (sections 4, 5 et 9 bis).

## Principes UX

- **Automatique d'abord.** La page s'ouvre sur un KPI suggéré déjà calculé. Les autres suggestions sont des pastilles en haut ; « Split by » propose les meilleurs regroupements.
- **Barre de réglages compacte** : Measure · Time · Split by, un libellé devant chaque menu. Un changement de données active **Calculate** ; rien ne se recalcule à chaque réglage.
- **Customize** : chaque réglage affiche « Auto · choix » et sa raison. Une option impossible est grisée avec la raison. Un réglage modifié porte une pastille et « Reset to auto ». Les réglages d'affichage s'appliquent sans recalcul.
- **Why this view** : une ligne sous le graphique explique les choix automatiques.

## Disposition (revue le 2026-10-19, 3e version)

Compacte et lisible d'un coup d'œil, sur le modèle de la barre de configuration de Séries temporelles : un libellé court devant chaque menu, pas de cartes.

```
KPI builder                                                  [Saved KPIs 3 ▾]  + New KPI
Try: Rows · Total revenue · Distinct customers · % churned
┌ barre collante ───────────────────────────────────────────────────────────────────────┐
│ Measure [Sum ▾][revenue ▾] + Measure + Ratio │ Time [date ▾][Month (auto) ▾][All dates ▾] │
│ ☑ Page filters │ Split by [country ▾] + Split                      [Calculate] [Save]  │
└───────────────────────────────────────────────────────────────────────────────────────┘
 Total revenue  1.2M  ~~~   │ Units  48.3K ~~~   │ Revenue per unit  18.6 ~~~
 Sep 2026 ↑ 4 % prev.       │ …                  │ …
Revenue by month by country                                                    Customize
[graphique 240 px]
Why this view: …   Split by: + country + segment
Table                                                      Swap  Copy  Download CSV
```

- **Barre de réglages** : collante en haut au défilement ; groupes Measure · Time · Split by séparés par un filet vertical ; menus de 28 px ; Calculate (actif seulement s'il y a des changements, avec « Not applied yet ») et Save à droite.
- **Chiffres clés** : une bande compacte entre deux filets, une colonne par mesure.
- **Customize** : colonne à droite des résultats, séparée par un filet.

## États

- **Aucune colonne utilisable** : « Needs at least one column to count or group by ».
- **Sans date** : la section « Over time » affiche « No date column — values over the whole data ».
- **0 ligne** : « No rows in this period » et le bouton « Use all dates ».
- **Colonne disparue** dans un KPI enregistré : message, et le champ à corriger mis en évidence.
- **Plafond dépassé** (5 000 points / 50 000 cellules) : message et grain plus grossier proposé en un clic.

## URL

`?kpi=<id>` pour un KPI enregistré ; sinon `?def=<définition encodée>`. Les filtres globaux s'appliquent si « Use the page filters » est coché.
