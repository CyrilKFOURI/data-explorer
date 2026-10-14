# Paramètres — `/settings`

| Section | Réglages | Où c'est gardé |
|---|---|---|
| Apparence | Thème clair / sombre / système, densité (compacte / confortable), animations (système / réduites / complètes) | Navigateur |
| Valeurs par défaut de l'analyse | Top N par chart (10), cartes par page (12), α des tests de normalité (0,05) : valeurs de départ des datasets pas encore personnalisés | Navigateur |
| Détection des types | Nombre discret maximal (20), taux de conversion nombre / date (95 %), taux d'unicité d'un identifiant (95 %), taux de vides pour ignorer (95 %) ; « Save thresholds », « Back to defaults » | SQLite (`settings.detection`) |
| Stockage | Emplacement du workspace, espace total et par dataset, « Clear caches » (résultats calculés en mémoire) | — |
| À propos | Version, licence MIT | — |

- Chaque réglage du navigateur modifié affiche un bouton ↺ « Reset to default ».
- Les seuils de détection s'appliquent aux nouvelles détections (import, « Re-run detection » sur la page Columns) ; les types validés et les corrections manuelles sont conservés.
- Hors V1 : seuil d'échantillonnage des nuages, format des nombres, emplacement du workspace modifiable (variable `DATA_EXPLORER_HOME`), activation des modules.
