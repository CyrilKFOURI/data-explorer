# Détection des colonnes

Tout repose sur cette étape : le type d'une colonne décide des visuels proposés, des tests statistiques, des filtres et des insights. Elle doit être **juste, rapide, explicable et corrigeable**.

## Recommandation : règles + base de connaissances, agent IA en option

| Approche | Pour | Contre |
|---|---|---|
| **Règles écrites + base de connaissances** | Instantané, hors-ligne, déterministe (même fichier → même résultat), testable, explicable (« détecté comme âge car le nom contient *age* et les valeurs sont des entiers entre 0 et 120 ») | Ne devine pas un nom cryptique (`CD_PRD_X`) |
| Agent LLM | Comprend les noms cryptiques, peut rédiger une description | Lent, non déterministe, à tester difficilement ; un modèle local tient en 6 Go de VRAM mais reste limité ; une API distante envoie les données hors de la machine |

**Décision proposée** : la V1 utilise **uniquement des règles et une base de connaissances**. Un **Assistant IA** optionnel viendra plus tard ([modules-futurs/assistant-ia.md](modules-futurs/assistant-ia.md)). Il interviendra seulement sur les colonnes à faible confiance, et ne fera que *proposer*.

## Deux niveaux de typage

Chaque colonne reçoit **un type d'analyse** (obligatoire) et **un rôle sémantique** (optionnel).

### Type d'analyse : décide des visuels et des tests

| Type | Exemples | Visuel par défaut |
|---|---|---|
| Numérique continu | prix, température, revenu | Histogramme + boîte à moustaches |
| **Numérique discret** | nb d'enfants, note 1–5, nb de pièces | **Barres (comme un catégoriel)**, histogramme en option |
| Catégoriel nominal | pays, produit, couleur | Barres horizontales Top N |
| Catégoriel ordinal | taille S/M/L, « faible/moyen/élevé », niveau d'étude | Barres dans l'ordre naturel |
| Booléen | oui/non, 0/1, vrai/faux | Barre empilée à 100 % |
| Date / date-heure | date de commande, timestamp | Volume dans le temps |
| Texte libre | commentaire, description | Longueur des textes, mots fréquents (pas de barres) |
| Identifiant | id client, n° de commande | Aucun graphique : unicité et doublons seulement |
| Ignorée | colonne constante ou presque vide | Signalée, exclue des analyses |

### Rôle sémantique : affine le format, les contrôles et les visuels

Exemples de rôles : âge, montant / prix, pourcentage / taux, quantité, durée, année, mois, jour de la semaine, latitude, longitude, pays, ville, code postal, e-mail, téléphone, URL, sexe / genre, statut, identifiant, note / score.

Un rôle peut **forcer** un type d'analyse (année → date, code postal → catégoriel même s'il est numérique). Il peut aussi régler l'affichage (montant → format monétaire, pourcentage → axe en %, lat/lon → proposer une carte).

## Pipeline de détection

Elle tourne sur un échantillon d'environ 10 000 lignes, puis est confirmée sur la colonne entière pour les statistiques.

1. **Type de stockage** : le type lu dans le fichier (Parquet le fournit, CSV non).
2. **Nettoyage des valeurs** :
   - Valeurs nulles déguisées → nul : `""`, `NA`, `N/A`, `null`, `None`, `-`, `?`, `NaN`, `#N/A`.
   - Nombres écrits en texte → numérique : `1 234,56`, `12 %`, `45 €`, `1.2e3`. Séparateur décimal et séparateur de milliers détectés automatiquement.
   - Booléens écrits en texte : oui/non, yes/no, true/false, Y/N, O/N.
3. **Détecteurs sur les valeurs** :
   - Taux de conversion en date ≥ 95 % → date. Formats reconnus : ISO, `jj/mm/aaaa`, `mm/jj/aaaa` (ambiguïté tranchée sur l'ensemble des valeurs), timestamps Unix dans une plage plausible.
   - Taux de conversion en nombre ≥ 95 % → numérique.
   - Motifs reconnus : e-mail, URL, téléphone, code postal, UUID.
4. **Détecteurs sur le nom** (base de connaissances) : le nom est normalisé (minuscules, sans accents, `camelCase` et `snake_case` découpés en mots), puis comparé aux motifs FR et EN de chaque rôle.
5. **Règles ordonnées** (implémentées dans `backend/app/domain/typing/engine.py`, seuils en constantes en attendant la page Paramètres). La première règle qui s'applique décide :
   - ≥ 95 % de vides ou une seule valeur → **ignorée** (signalée, jamais supprimée)
   - Nom évoquant du texte libre (comment, description…) → **texte libre**
   - Deux valeurs d'un même vocabulaire (oui/non, 0/1, true/false…) → **booléen**
   - Nom évoquant un code postal ou un téléphone → **catégoriel**, gardé en texte (zéros initiaux)
   - ≥ 95 % de valeurs lues comme des nombres → **numérique** ; entiers avec ≤ 20 valeurs distinctes → **discret**, sinon **continu** (un rôle comme âge, montant ou latitude impose continu)
   - Entiers entre 1800 et 2100 avec un nom évoquant une année → **date** (rôle année)
   - ≥ 95 % de valeurs lues comme des dates → **date** (si `jj/mm` et `mm/jj` marchent tous deux : confiance moyenne, raison « ambigu »)
   - Valeurs dans un ordre connu (low < medium < high, S < M < L, mois, jours…) → **ordinal**, avec l'ordre
   - ≥ 95 % d'e-mails, d'URL ou d'UUID → **identifiant** si les valeurs sont uniques, sinon catégoriel
   - Nom évoquant un identifiant : ≥ 90 % de valeurs uniques → **identifiant** ; sinon référence partagée (ex. `store_id`) → **catégoriel**
   - Valeurs longues (moyenne > 50 caractères, ou majoritairement des phrases uniques) → **texte libre**
   - ≥ 95 % de valeurs uniques, courtes et sans espaces → **identifiant**
   - Sinon → **catégoriel**
6. **Confiance et raisons** : chaque règle fixe une confiance **haute / moyenne / faible** et produit des raisons lisibles (« 100 % des valeurs lues comme des nombres · virgule décimale · le nom évoque un montant »), affichées dans l'interface.
7. **Correction par l'utilisateur** : enregistrée, prioritaire sur la détection, retrouvée à la réouverture du dataset, conservée si on relance la détection, et annulable.

## Parseurs : la donnée n'est jamais modifiée

La copie Parquet garde les valeurs telles qu'importées. Chaque colonne a un **parseur** (`raw`, `number` avec séparateur décimal, `date` avec format, `boolean` avec vocabulaire, `year`, `text`), traduit en expression SQL DuckDB (`backend/app/domain/typing/parsers.py`) et appliqué à la lecture. La détection évalue les candidats avec ce même SQL : détection et conversion ne peuvent pas diverger. Quand l'utilisateur change de type, le meilleur parseur mesuré pendant la détection est réutilisé. Les valeurs présentes mais illisibles dans le type choisi sont comptées et signalées.

## Base de connaissances

Des fichiers **TOML** (lus avec `tomllib`, sans dépendance) dans `backend/app/domain/typing/knowledge_base/` :

- `roles.toml` : les rôles (noms FR/EN, type imposé, plage plausible) ;
- `vocabulary.toml` : valeurs nulles, paires booléennes, ordres connus.

Ajouter un rôle = ajouter une entrée, sans toucher au code. En cas d'égalité, le nom le plus long l'emporte, puis celui qui finit le nom de colonne (dans `long_description`, c'est « description » qui compte, pas « long »).

```toml
[[role]]
id = "age"
label = "Age"
names = ["age", "ages", "years old", "age years"]
type = "numeric_continuous"
min = 0
max = 130
```

## Tests

`backend/tests/unit/test_typing.py` contient le tableau des réponses attendues pour `samples/typing_traps.csv` (21 colonnes pièges) et `samples/sales_timeseries.csv` : 100 % de bonnes réponses exigées. Un piège corrigé devient un nouveau cas de test.
