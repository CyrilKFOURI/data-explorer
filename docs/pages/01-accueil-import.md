# Accueil / Import — `/`

## Rôle

Point d'entrée : importer un nouveau jeu de données ou reprendre un dataset existant.

## Contenu

1. **Zone d'import** (en haut, large)
   - Glisser-déposer un fichier : CSV, TSV, Parquet, Excel (.xlsx/.xlsm ; l'ancien .xls est refusé avec un message qui propose de l'enregistrer en .xlsx). Le fichier est envoyé au backend (copie interne dans le workspace)
   - Ou choisir un fichier ou un **dossier** dans le dossier monté (`/data` en Docker, voir [TRD.md](../TRD.md#distribution-validé--docker)) avec le bouton « Browse ». C'est la voie conseillée pour les gros fichiers et les dossiers. En natif, on peut aussi coller un chemin.
2. **Datasets récents** : liste avec le nom, la source, le nombre de lignes × colonnes, la date de dernière ouverture et un statut (prêt / source modifiée / erreur). Actions : ouvrir, renommer, réimporter, supprimer (supprime la copie, jamais la source).

## Déroulé d'un import

1. **Aperçu** (en moins d'une seconde, sur les premières lignes) :
   - Format détecté ; pour un CSV : séparateur, encodage, ligne d'en-tête et séparateur décimal, chacun modifiable
   - Excel : choix de la feuille, ou de plusieurs feuilles à empiler
   - Dossier : liste des fichiers trouvés (cochables), avertissement si les colonnes diffèrent entre fichiers (union ou intersection au choix)
   - Les 20 premières lignes
2. **Options** :
   - Colonnes à importer (toutes cochées par défaut, recherche)
   - Échantillon : 100 % par défaut, ou x % / N lignes (graine fixe, donc reproductible)
   - Nom du dataset (prérempli avec le nom du fichier ou du dossier)
3. **Importer** : barre de progression (fichiers lus, lignes). À la fin : conversion en Parquet, détection des types, puis redirection vers **Colonnes** (premier import) ou **Vue d'ensemble**.

## Petits plus

- Réimporter une source inchangée est instantané (empreinte identique → copie existante réutilisée).
- Un dossier dont le contenu change est signalé à la réouverture.
- **Jeux de démo** en un clic (« Try a sample dataset »), dans `samples/` :
  - classiques publics : Titanic, Iris, Palmer Penguins, California Housing
  - `typing_traps` : dataset synthétique plein de pièges de typage (dates en texte, `1 234,56`, entiers discrets 1–5, IDs, codes postaux, `N/A`, booléens oui/non…), qui sert aussi de test de détection
  - une série temporelle (prête pour le futur module)
  - gros volume : ~5 M lignes **générées par script** (`scripts/make_big_sample.py`), non commitées

## Cas limites

Fichier vide, encodage illisible, Excel protégé, CSV aux lignes irrégulières (lignes en erreur listées et ignorables), fichier trop gros pour l'aperçu complet (estimation du nombre de lignes affichée).

## Hors V1

Connexion à une base SQL, import depuis une URL, rafraîchissement automatique.
