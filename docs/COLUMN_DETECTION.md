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
5. **Règles de sous-type** (seuils réglables dans les Paramètres) :
   - 2 valeurs distinctes → **booléen**
   - Entiers avec ≤ 20 valeurs distinctes (ou distinctes / lignes ≤ 5 %) → **numérique discret**
   - Entiers entre 1900 et 2100, avec un nom qui évoque une année → **année** (temporel)
   - Valeurs distinctes / lignes ≥ 95 % et nom qui évoque un identifiant (ou chaîne courte unique) → **identifiant**
   - Texte avec longueur moyenne > 50 caractères ou forte cardinalité sans motif → **texte libre**
   - Catégoriel dont les valeurs sont dans un ordre connu de la base (S < M < L, jan < fév…) → **ordinal**
   - 1 seule valeur ou ≥ 95 % de nuls → **ignorée** (signalée, jamais supprimée)
6. **Score et confiance** : chaque candidat cumule des points (valeurs + nom + règles). On retient le meilleur score, avec une confiance **haute / moyenne / faible** et la **liste des raisons**, affichée dans l'interface.
7. **Correction par l'utilisateur** : enregistrée, prioritaire sur la détection, retrouvée à la réouverture du dataset, et annulable.

## Base de connaissances

Des fichiers YAML versionnés dans `backend/app/domain/typing/knowledge_base/`, un fichier par famille de rôles. Ajouter un rôle = ajouter une entrée, sans toucher au code.

```yaml
# knowledge_base/personne.yaml
- role: age
  noms: [age, âge, age_client, customer_age, years_old]   # motifs, après normalisation
  valeurs: { type: entier, min: 0, max: 120 }
  type_analyse: numerique_continu     # ou numerique_discret si peu de valeurs
  affichage: { unite: "ans" }
  visuels_preferes: [histogramme, boite]
  explication: "Le nom évoque un âge et les valeurs sont des entiers entre 0 et 120."
```

## Tests

Un jeu de fichiers de test (`backend/tests/fixtures/typing/`) avec, pour chaque colonne, le type attendu. Un taux de bonne détection se mesure à chaque modification des règles. Un piège corrigé devient un nouveau cas de test.
