# 004 — Fiche variable : tâches

## Backend
- [x] Dépendance `scipy` (accordée)
- [x] `domain/variable/source.py` : colonne typée + échantillon reproductible (hash du n° de ligne)
- [x] `domain/variable/numeric.py` : statistiques descriptives complètes (DuckDB, toutes les lignes), 5 tests de normalité, KDE, ECDF, QQ-plot
- [x] `domain/variable/fitting.py` : lois continues et discrètes (AIC/BIC/KS), transformations
- [x] `domain/variable/outliers.py` : 4 méthodes, lignes extrêmes
- [x] `domain/variable/profiles.py` : profils catégorie, date (trous, calendrier), texte (mots), identifiant (doublons, motifs) ; `analyze.py` + `service.py`
- [x] API : `GET /datasets/{id}/variable?column=` (profil, cache mémoire), `GET .../variable/fit`, `GET .../variable/outliers?method=`
- [x] Tests : stats vs numpy/scipy, tests de normalité (normal / log-normal), ajustement (gamma), outliers, profils catégorie / date / texte, API, perf 5 M lignes (courbes ECDF/QQ : t-digest au-delà de 200 000 valeurs)

## Frontend
- [x] Route `/d/$datasetId/variable/$column`, précédente / suivante (boutons + Maj+←/→), position « n sur N », colonnes exclues ignorées
- [x] `ui/Tabs`, `ui/InfoTip` ; `StatTable` (info-bulle par ligne), `TestResult` (verdict, stat, p bornée selon la méthode, α, détail dépliable)
- [x] Visuels : histogramme (bins réglables ; barres par valeur pour un discret), KDE, ECDF, boîte (quartiles exacts), violon, QQ-plot, 3 meilleures densités superposées, QQ contre la loi choisie, calendrier ; param `bins` ajouté à l'API des graphiques
- [x] Onglets numériques : Summary, Normality (α 0,01 / 0,05 / 0,1 mémorisé), Distribution (lois + transformations), Outliers (+ Categories pour un discret)
- [x] Sections catégorie, date, texte, identifiant
- [x] Plein écran : panneau de détails par type + « Open variable page », graphique catégoriel borné à 420 px (défile) pour garder le tableau visible ; bouton fiche actif sur la carte
- [x] Tests : page numérique (stats, tests, α), lois, outliers, catégorie, navigation, colonne inconnue, plein écran, lien des cartes (43 tests frontend)

## Vérification
- [x] Navigateur : `typing_traps`, une variable de chaque type (continu, discret, catégorie, booléen, date, texte, identifiant) ; onglets Normality / Distribution / Outliers
- [ ] Plein écran vérifié à l'œil (panneau navigateur masqué pendant la session : couvert par les tests)
