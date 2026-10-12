# UI / UX

> Statut : validé (interview du 2026-10-12). Les valeurs exactes des couleurs seront ajustées sur maquette au Sprint 0 (contrastes vérifiés). Avant tout travail d'interface, utiliser les skills listés dans `CLAUDE.md`.

## Style général

**« Instrument de laboratoire, ton éditorial »** : un outil d'analyste précis, dense mais calme, où les données sont la seule chose qui attire l'œil. Il est réchauffé par une palette chaude et une dataviz soignée, à la manière d'**Observable** et de **Datawrapper** : titres de graphiques informatifs, annotations directes plutôt que légendes lointaines, axes discrets, beaucoup de soin sur la typographie des graphiques. Pas une landing page.

Principes :
- **Les données d'abord** : l'interface est neutre, la couleur est réservée aux graphiques, aux types de colonnes et aux alertes.
- **Densité maîtrisée** : beaucoup d'informations par écran, mais alignées sur une grille stricte, avec des espacements réguliers (échelle de 4 px).
- **Hiérarchie par la typographie** (taille, graisse, couleur d'encre) plutôt que par des boîtes, des ombres et des couleurs.
- **Bordures fines (1 px)** et fonds légèrement différenciés pour séparer ; rayons discrets (4–6 px) ; ombres seulement sur les éléments flottants (menus, dialogues).
- **Mouvement sobre** : 150–200 ms, uniquement pour expliquer un changement (ouverture, réordonnancement). Désactivé si le système demande moins d'animations.
- **Clair et sombre** dès la V1, à égalité. **Par défaut, le thème suit celui du système.**
- **Densité compacte par défaut**, option « confortable » dans les Paramètres (deux jeux d'espacements en tokens).
- **Icônes : Lucide**, utilisées avec retenue pour ne pas faire « template » : trait de 1,5 px partout, 16 px dans l'interface, seulement là où une icône aide à agir (jamais décorative à côté d'un titre), toujours avec un libellé ou une info-bulle.

**Interdits anti-« AI slop »** : dégradés violet/bleu, glassmorphism, émojis en guise d'icônes, grosses cartes très arrondies avec ombre portée partout, titres héroïques, texte gris clair illisible, icône décorative sur chaque titre, compteurs animés, « ✨ Insights IA ✨ ».

## Couleurs

Direction retenue : **neutre chaud + accent terracotta**. Tout passe par des **tokens sémantiques** dans `frontend/src/styles/tokens.css`, redéfinis pour le thème sombre, et jamais par des couleurs Tailwind par défaut.

| Token | Clair | Sombre |
|---|---|---|
| `--surface-0` (fond) | `#F7F5F2` | `#14120F` |
| `--surface-1` (panneaux) | `#FFFDFA` | `#1D1A16` |
| `--ink-1` (texte) | `#24201B` | `#EDE8E1` |
| `--accent` (terracotta) | `#C2562F` | à éclaircir pour le contraste AA (≈ `#E07A50`) |

Valeurs de départ, à affiner sur maquette. La terracotta est réservée aux **actions** (bouton principal, sélection, focus). Dans les graphiques, la palette catégorielle validée par `dataviz` doit rester distinguable de l'accent et ne pas le contredire.

| Token | Usage |
|---|---|
| `--surface-0/1/2` | Fond de l'app, panneaux, éléments surélevés |
| `--ink-1/2/3` | Texte principal, secondaire, désactivé |
| `--line` | Bordures et séparateurs |
| `--accent` | Une seule couleur d'action (sélection, focus, bouton principal) |
| `--type-numeric`, `--type-categorical`, `--type-date`, `--type-bool`, `--type-text`, `--type-id` | Badges de type, toujours les mêmes partout |
| `--ok`, `--warn`, `--bad` | Résultats de tests, qualité des données |
| `--chart-1…8`, séquentielle, divergente | Palettes Plotly, validées avec le skill `dataviz` (contraste, daltonisme) |

## Typographie

- **IBM Plex Sans** pour l'interface et les graphiques, **IBM Plex Mono** pour les noms de colonnes, les valeurs brutes et le code. Les deux sont embarquées localement (pas de Google Fonts : hors-ligne).
- **Chiffres tabulaires** (`font-variant-numeric: tabular-nums`) partout où il y a des nombres ; nombres alignés à droite dans les tableaux.
- Échelle courte : 12 / 13 / 14 (corps) / 16 / 20 / 24. Pas de titres géants.

## Composants clés

| Composant | Rôle |
|---|---|
| **Shell** | Barre latérale gauche repliable (pages du dataset, puis modules), barre du haut (nom du dataset, sélecteur de dataset, recherche ⌘K) |
| **SummaryStrip** | Bandeau de résumé : lignes, colonnes, % de manquants, doublons, mémoire, répartition des types |
| **FilterBar** | Filtres actifs sous forme de puces, « + Filtre », « Tout effacer », nombre de lignes restantes |
| **TypeBadge** | Badge coloré du type + rôle ; clic → menu de correction avec la confiance et les raisons de la détection |
| **ChartCard** | Carte graphique standard : en-tête, graphique, mini-stats, actions (plein écran, changer de visuel, exporter) |
| **VariableGrid** | Grille 3 par ligne, paginée, triable, filtrable par type ou par alerte |
| **StatTable** | Tableau de statistiques avec info-bulle d'explication sur chaque ligne |
| **TestResult** | Verdict lisible (« Probablement pas normale »), statistique, p-value, seuil, phrase d'explication |
| **FullscreenChart** | Dialogue plein écran : toutes les modalités, recherche, tableau détaillé |
| **CommandPalette** | ⌘K / Ctrl+K : aller à une variable, une page, une action |
| **DataTable** | Table virtualisée, tri, redimensionnement des colonnes |
| **EmptyState / Skeleton** | États vides explicatifs, squelettes de chargement à la forme du contenu |

## Ergonomie et petits plus

- **Tout est réversible** : une correction de type peut être annulée (Ctrl+Z et bouton « Revenir à la détection »).
- **L'URL décrit l'écran** (dataset, page, variable, filtres) : retour arrière du navigateur fiable, état retrouvé après rechargement.
- **L'app se souvient** de la dernière page, de la pagination, du Top N et des filtres de chaque dataset.
- **Raccourcis** : ⌘K, ←/→ pour la variable précédente ou suivante dans la fiche, `F` pour le plein écran, `Échap` pour fermer.
- **Info-bulles pédagogiques** sur chaque statistique et chaque test : ce que c'est, comment lire le résultat.
- **Indication honnête** quand un calcul porte sur un échantillon.
- Accessibilité : contraste AA, navigation au clavier complète, focus visible, couleur jamais seule porteuse de sens (le type a aussi une icône et un libellé).

## Références visuelles

- **Observable** (observablehq.com, Observable Plot) : graphiques sobres et précis, notebooks lisibles, mélange texte + visuel.
- **Datawrapper** : titres de graphiques qui disent la conclusion, annotations directes, palettes accessibles, axes et grilles discrets.

Ce qu'on en reprend : la **typographie des graphiques** (titre, sous-titre, source), les **annotations sur le graphique** (médiane, seuil, valeur aberrante nommée), une grille légère, et des **phrases de conclusion** au-dessus des visuels (« Revenue is right-skewed: the mean is 40% above the median »).
