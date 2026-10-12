# Module Données synthétiques — `/d/:id/synthetic`

> **Statut : futur (Sprint 7). Ne pas implémenter avant la V1.**

Générer un jeu de données artificiel qui reproduit les propriétés statistiques du dataset d'origine.

## Méthodes

| Méthode | Pour |
|---|---|
| Gaussian Copula | Rapide, base de comparaison |
| **CTGAN** | Tabulaire mixte (numérique + catégoriel) |
| TVAE / **VAE** | Tabulaire, souvent plus stable que CTGAN |
| **TimeGAN** | Séries temporelles (dépend du module séries temporelles) |
| (Plus tard) Modèles de diffusion tabulaires | Si besoin |

## Parcours

1. Choix des colonnes, de la méthode, du nombre de lignes à générer ; contraintes (bornes, colonnes à garder uniques).
2. Entraînement en tâche de fond (GPU si disponible), progression et courbe de perte.
3. **Évaluation de la fidélité** : distributions comparées colonne par colonne (superposition réel / synthétique), écart des matrices de corrélation, score global, test « réel ou synthétique ? » (un classifieur doit échouer à les distinguer).
4. **Confidentialité** : distance au plus proche enregistrement réel (aucune ligne copiée), avertissements.
5. Le résultat devient un **nouveau dataset** (lien vers la source dans `synthetic_runs`), explorable avec toutes les pages V1.

## Dépendances pressenties

SDV (CTGAN, TVAE, Gaussian Copula), PyTorch (CUDA) ; une implémentation de TimeGAN à choisir. Lourd : prévenir avant l'installation (espace disque).
