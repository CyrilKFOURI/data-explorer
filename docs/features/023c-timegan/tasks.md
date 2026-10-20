# 023c — Tâches

Spec : [spec.md](spec.md). Page : [13-donnees-synthetiques.md](../../pages/13-donnees-synthetiques.md).

## Choix de réalisation

- **`domain/synthetic/sequences.py`** (numpy, sans PyTorch) :
  - plan R-SEQ (temps, entité, pas, longueur, nombre) ;
  - fenêtres glissantes et leur retour aux lignes ;
  - séparation des historiques réels (entités entières, ou fin de la série) ;
  - autocorrélations, séquences d'exemple.
- **`deep/timegan.py`** : les cinq GRU et les trois phases de l'article, plus les deux GRU des scores (discriminant, prédictif). **`methods/timegan.py`** : fenêtres, entraînement, dates et identifiants des nouvelles séquences.
- **Une branche à part dans `generate.py`** : le temps et l'entité ne sont pas modélisés comme des colonnes. L'entité est régénérée, une valeur par séquence ; les dates suivent le pas réel.
- **Service** : pour TimeGAN, les lignes réelles sont lues dans l'ordre du fichier, puis séparées par historiques entiers. Le rapport reçoit `sequences`.

## Tâches

- [x] T1 — Spec, doc de page (groupe Sequences, onglet Sequences).
- [x] T2 — Domaine séquences : plan, fenêtres, aller-retour, séparation, autocorrélation — tests.
- [x] T3 — TimeGAN et scores de l'article ; intégration dans `generate.py` et le plan (disponibilité, pas Auto) — tests (CPU), test lent GPU.
- [x] T4 — Service et API : requête `sequence`, plan des séquences, séparation par historiques, rapport — tests API.
- [x] T5 — Frontend : groupe Sequences dans la barre, avertissement, progression par phase, onglet Sequences.
- [x] T6 — Docs, vérifications, navigateur (GPU réel), commit.

## Découvertes

- **`sales_timeseries` compte 3 magasins sur 1 095 jours**, pas 5 sur 657 comme l'écrivait la spec (corrigée).
- **L'évaluation mélangeait les séquences synthétiques.** Sans entité, elles partaient de dates tirées au hasard, et le tri par date les entremêlait : l'autocorrélation semblait ratée (69 %) alors que le modèle l'avait apprise. Deux corrections :
  - les séquences synthétiques sont relues par blocs, dans l'ordre où TimeGAN les écrit ;
  - sans entité, elles sont chaînées bout à bout (une seule série, comme l'original), et repartent du début si elles dépassent la période réelle.

  Résultat sur une sinusoïde bruitée, 1 000 pas par phase (130 s, GPU) :
  - autocorrélation 96 % (retard 6 : −0,71 contre −0,74 dans le réel) ;
  - le classifieur ne reconnaît les fenêtres synthétiques que 60 % du temps ;
  - les séquences gardent 85 % du pouvoir prédictif du réel.
- **Le score d'autocorrélation était trop indulgent.** Avec 1 − écart / 2, il donnait 84 % à une dynamique ratée ; il vaut maintenant 1 − écart moyen.
- **Les petits GRU vont 5 fois plus vite sur le GPU** (44 ms par pas contre 220 ms sur le CPU, quel que soit le nombre de cœurs). Le budget Auto est donc de 1 000 pas par phase sur le GPU et de 150 sur le CPU, avec une note qui prévient que le résultat sera grossier. Les scores d'évaluation utilisent 200 pas.
- **Dates répétées sans entité.** Dans l'espace de travail de l'utilisateur, `store` avait été retypée en nombre illisible : la page avertit maintenant que les lignes d'une même date se suivent dans l'ordre du fichier, et invite à choisir une entité.
- **Test « fenêtres recopiées »** : recopier le réel en blocs alignés tous les 14 jours alignait aussi le cycle hebdomadaire, et le classifieur le repérait. Le test recopie maintenant des fenêtres à des débuts tirés au hasard, comme TimeGAN les produit.
- **Performance** : trois magasins sur trois ans, budget Auto, en 132 s sur la RTX 4050 (test lent, limite 180 s).
- **Un import circulaire** est apparu entre le plan, les séquences et l'encodage : les constantes de types (`NUMERIC`, `CATEGORICAL`, `RARE`) sont passées dans `encode.py`.
