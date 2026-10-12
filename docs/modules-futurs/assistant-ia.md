# Module Assistant IA

> **Statut : futur (à planifier). Ne pas implémenter avant la V1.**

Un agent LLM **optionnel et désactivé par défaut**, qui complète le moteur de règles sans le remplacer.

- **Types ambigus** : pour les colonnes à confiance faible (noms cryptiques comme `CD_PRD_X`), propose un type, un rôle et une description à partir du nom et d'un échantillon de valeurs. L'utilisateur accepte ou refuse.
- **Descriptions de colonnes** : génère un dictionnaire de données lisible.
- **Insights rédigés** : reformule et hiérarchise les insights calculés par les règles. Il ne calcule jamais de statistiques lui-même.
- **Questions en langage naturel** (plus tard) : « Montre la répartition du revenu par région » → page Comparer préremplie.

## Principes

- Par défaut, **modèle local** (Ollama, 7–8B quantifié, tient dans 6 Go de VRAM). Une API distante seulement si l'utilisateur l'active, avec un avertissement : un échantillon de données sortirait alors de la machine.
- L'agent **propose**, l'utilisateur **décide**. Toute suggestion est marquée comme venant de l'IA.
- Sans l'assistant, l'app fonctionne à 100 %.
