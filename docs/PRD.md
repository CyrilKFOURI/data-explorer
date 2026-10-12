# PRD — Product Requirements

> Statut : validé (interview du 2026-10-12).

## Problème

Les outils d'EDA automatique (pandas-profiling / ydata-profiling, sweetviz…) donnent des statistiques descriptives mais restent **superficiels** : peu ou pas de vrais tests, aucune vérification de leurs conditions d'application, aucune aide pour interpréter. Faire une analyse rigoureuse demande d'écrire un notebook à chaque nouveau dataset.

**Proposition de valeur** : un explorateur local qui apporte la **profondeur statistique** d'un notebook écrit par un statisticien (tests de normalité, ajustement de lois, tests bivariés avec taille d'effet et conditions vérifiées), sans écrire de code, avec une interface soignée et des résultats expliqués.

Projet **public / portfolio** : il doit être impressionnant à montrer, facile à installer et irréprochable sur la justesse des calculs.

## Utilisateurs cibles

Deux profils, servis par **deux niveaux d'explication** sur chaque résultat :

| Profil | Ce qu'il attend | Ce qu'il voit |
|---|---|---|
| Data scientist / analyste | Aller vite, chiffres exacts, vocabulaire technique | Verdict + statistique + p-value + taille d'effet, tout de suite |
| Étudiant en stats / data | Comprendre ce qu'il fait | Panneau dépliable « Understand this test » : hypothèses, conditions, comment lire le résultat, quand utiliser un autre test |

Les visiteurs du portfolio découvrent l'app par une **vidéo/GIF dans le README** et l'installent en local. Pas de démo hébergée.

## Fonctionnalités MVP

La V1 est un **explorateur de données tabulaires** local, très soigné, qui sert de socle à des modules avancés ajoutés ensuite (voir [modules-futurs/](modules-futurs/README.md)).

### Principes produit (valables pour toute l'app)

1. **Zéro configuration** : on donne un fichier ou un dossier, l'app comprend le reste.
2. **Les types de colonnes d'abord** : tout (visuels, tests, filtres) dépend du type détecté. La détection est donc soignée, explicable, et corrigeable en un clic (voir [COLUMN_DETECTION.md](COLUMN_DETECTION.md)).
3. **L'app explique, à deux niveaux** : chaque type proposé, chaque statistique, chaque test a un verdict en une phrase claire (« p = 0.003 → probably not normally distributed ») et une explication détaillée dépliable.
4. **Suggérer, jamais imposer** : toute décision automatique peut être annulée ou modifiée.
5. **Toujours lisible** : des règles d'affichage empêchent un graphique d'« exploser » (catégories nombreuses, millions de points…). Voir [VISUALS.md](VISUALS.md).
6. **Local et hors-ligne** : aucune donnée ne quitte la machine, aucune connexion requise.
7. **Modulaire** : chaque nouvelle page ou analyse s'ajoute sans casser l'existant (voir [ARCHITECTURE.md](ARCHITECTURE.md)).

### Fonctionnalités V1

| # | Fonctionnalité | Page | Détail |
|---|---|---|---|
| 1 | Import fichier / dossier (CSV, Parquet, Excel), datasets récents | Accueil | [pages/01-accueil-import.md](pages/01-accueil-import.md) |
| 2 | Détection des types + rôles sémantiques, revue et correction | Colonnes | [pages/02-colonnes.md](pages/02-colonnes.md) |
| 3 | Bandeau de résumé et grille de toutes les variables (3 par ligne, paginée) | Vue d'ensemble | [pages/03-vue-ensemble.md](pages/03-vue-ensemble.md) |
| 4 | Analyse avancée d'une variable : stats, ajustement de lois, tests de normalité, valeurs aberrantes | Fiche variable | [pages/04-fiche-variable.md](pages/04-fiche-variable.md) |
| 5 | Croisement de 2 ou 3 variables, tests statistiques, visuels 3D | Comparer | [pages/05-comparer.md](pages/05-comparer.md) |
| 6 | Corrélations entre types mixtes + insights rédigés | Corrélations | [pages/06-correlations.md](pages/06-correlations.md) |
| 7 | Table de données filtrée, exports | Données | [pages/07-donnees.md](pages/07-donnees.md) |
| 8 | Filtres globaux ET/OU, palette de commandes, préférences | Transverse | [pages/00-transverse.md](pages/00-transverse.md) |

## Hors scope

**Prévu, mais pas dans la V1** (un module par sprint après la V1, documenté dans [modules-futurs/](modules-futurs/README.md)) :

- Analyse de séries temporelles (stationnarité, hétéroscédasticité, saisonnalité, prévisions)
- Machine learning (entraînement, évaluation, explicabilité)
- Builder KPI (agrégations dans le temps, tableaux croisés)
- Génération de données synthétiques (CTGAN, TimeGAN, VAE…)
- Assistant IA (agent LLM pour les types ambigus et les insights)

**Non prévu pour l'instant** : multi-utilisateur, comptes et authentification, hébergement cloud, modification des fichiers sources, connexion directe à des bases SQL distantes.

## Critères de succès

La V1 est réussie quand les quatre critères sont remplis :

1. **Détection des types ≥ 95 %** de bonnes réponses, colonne par colonne, sur un jeu de test d'au moins 15 datasets variés (`backend/tests/fixtures/typing/`), mesurée en CI.
2. **Vitesse** : Vue d'ensemble affichée en < 2 s sur 1 M lignes × 50 colonnes (cache froid) ; < 300 ms pour un réglage d'affichage (Top N, visuel) ; jeux jusqu'à **~5 M lignes** utilisables de façon fluide.
3. **Rigueur statistique** : chaque test et chaque ajustement de loi est validé par des tests automatiques contre scipy / statsmodels sur des données de référence ; ses conditions d'application sont vérifiées et affichées.
4. **Prêt pour le portfolio** : installation en une commande, jeux de démo inclus, README en anglais avec captures et GIF/vidéo de démo.
