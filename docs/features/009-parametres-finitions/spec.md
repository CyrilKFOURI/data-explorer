# 009 — Paramètres & finitions

## Objectif

Rendre l'app autonome et agréable : un **guide** intégré qui explique tout, une page **Paramètres** utile, une **palette de commandes** et des **raccourcis**, puis une revue design et accessibilité. Références : [08-parametres.md](../../pages/08-parametres.md), [09-aide.md](../../pages/09-aide.md).

## User stories

1. Je lis dans l'app (page **Guide**) comment utiliser chaque page, tout ce que je peux faire, et ce que veut dire chaque métrique. Le même texte est dans `docs/USER_GUIDE.md`.
2. Dans **Settings**, je règle l'apparence (thème, densité, animations réduites), les valeurs par défaut de l'analyse (Top N, cartes par page, α des tests de normalité), les seuils de détection des types, et je vois l'espace occupé par chaque dataset, avec « Clear caches » et les informations « About ».
3. **Ctrl+K** ouvre une palette : aller à une page, une variable ou un dataset, lancer une action (filtres, effacer les filtres, thème, guide, paramètres).
4. **?** affiche la liste des raccourcis.
5. L'interface passe une revue design et accessibilité (contraste, focus visible, libellés, navigation au clavier).

## Critères d'acceptation

- Guide :
  - `docs/USER_GUIDE.md` est la source unique ; la page `/help` l'affiche (rendu Markdown maison : titres, paragraphes, listes, tableaux, gras, italique, code ; pas de dépendance), avec un sommaire cliquable des sections ;
  - lien **Guide** dans la barre latérale, au-dessus de Settings ; l'image Docker embarque le guide.
- Paramètres :
  - apparence et valeurs par défaut de l'analyse : préférences du navigateur (`localStorage`), appliquées immédiatement ; chaque réglage modifié propose « Reset » ;
  - seuils de détection : `GET / PUT /api/v1/settings` (table SQLite `settings`), validés (bornes) ; ils s'appliquent aux **nouvelles détections** (import, « Re-run detection »), sans toucher aux types déjà validés ni aux corrections manuelles ;
    - nombre discret maximal (20), taux de lecture pour convertir en nombre / date (95 %), taux d'unicité d'un identifiant (95 %), taux de vides pour ignorer (95 %) ;
  - stockage : `GET /api/v1/storage` → emplacement du workspace, taille par dataset et totale ; `POST /api/v1/storage/clear-caches` vide les caches en mémoire (vue d'ensemble, fiches, comparaisons, corrélations, comptes de lignes) ;
  - About : version, emplacement du workspace, licence MIT.
- Palette (Ctrl+K ou ⌘K) : champ de recherche, résultats groupés (pages, variables du dataset ouvert, datasets, actions), navigation flèches + Entrée, Échap ferme ; ne s'ouvre pas pendant la saisie dans un champ, sauf Ctrl+K.
- `?` : fenêtre listant les raccourcis (F, Ctrl+K, ?, Ctrl+Z, Échap).
- Animations réduites : réglage « System / On / Off » ; « On » ou `prefers-reduced-motion` coupent les transitions.
- Revue : audit avec les skills d'audit, corrections des problèmes majeurs (contraste AA, focus visible, rôles et libellés), tests verts.

## Hors scope

Seuil d'échantillonnage des nuages et format des nombres (valeurs fixes en V1), emplacement du workspace modifiable depuis l'app (variable d'environnement), activation des modules (aucun en V1), langue de l'interface.
