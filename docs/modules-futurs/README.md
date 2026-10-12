# Modules futurs — PAS POUR MAINTENANT

> **Rien de ce dossier ne doit être implémenté avant la release V1.** Ces documents fixent l'intention, pour que l'architecture V1 leur laisse la place (voir [ARCHITECTURE.md](../ARCHITECTURE.md), dossiers `modules/`).

Chaque module :
- se branche via les registres (`backend/app/modules/registry.py`, `frontend/src/modules/registry.ts`) et ajoute ses entrées dans la barre latérale ;
- déclare les types de colonnes dont il a besoin (ex. séries temporelles → au moins une date) et reste grisé sinon ;
- ajoute ses tables par migration ;
- passe par une spec (`docs/features/NNN-nom/`) au moment de son sprint, qui précise ce document.

| Module | Sprint prévu | Doc |
|---|---|---|
| Séries temporelles | Sprint 4 | [series-temporelles.md](series-temporelles.md) |
| Machine learning | Sprint 5 | [machine-learning.md](machine-learning.md) |
| Builder KPI | Sprint 6 | [kpi-builder.md](kpi-builder.md) |
| Données synthétiques | Sprint 7 | [donnees-synthetiques.md](donnees-synthetiques.md) |
| Assistant IA | À planifier | [assistant-ia.md](assistant-ia.md) |
