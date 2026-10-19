# 019b — Tâches (le reste de la 019)

Spec : [spec.md](spec.md). Fait après la 021, avec les paquets désormais installés.

## Choix de réalisation

- **Annulation** : `DELETE /modules/ml/jobs/{id}` ; l'entraînement s'arrête au prochain point de contrôle (avant l'ajustement, entre deux plis de validation croisée, avant l'enregistrement) — un ajustement en cours n'est pas interrompu ; statut « cancelled », rien n'est enregistré.
- **Durée estimée** : `GET …/estimate` ajuste le pipeline sur 500 puis 2 000 lignes, mesure, et extrapole t = a·nᵇ (b borné entre 1 et 3) au nombre de lignes d'apprentissage × nombre d'ajustements (plis) ; affiché pour les modèles marqués lents ou au-delà de 50 000 lignes.
- **Courbe d'apprentissage** des modèles itératifs, lue sur le modèle final : HistGB (score d'apprentissage / validation interne), gradient boosting (perte), MLP (perte, score de validation), XGBoost / LightGBM (métrique sur la part tenue à l'écart) ; itération retenue par l'arrêt anticipé marquée.
- **Contraintes monotones** (HistGB, XGBoost, LightGBM) : réglage avancé texte « size:+1, mileage:-1 » sur les colonnes numériques d'origine (qui passent telles quelles dans la préparation) ; le pipeline est ajusté en deux temps (préparation, puis modèle avec le vecteur de contraintes aligné sur les entrées produites).
- **Seuil de décision** (deux classes, split simple ou temporel) : option de validation « 0.5 · best F1 · best balanced accuracy » ; le seuil est choisi sur des prédictions hors-pli des lignes d'apprentissage (3 plis), puis appliqué une fois au test ; le run le garde (le curseur de seuil part de là). Refusé avec la validation croisée (il serait choisi sur les lignes mêmes qui le jugent).
- **Radius neighbours** (rayon par défaut √(nombre de colonnes) sur entrées standardisées ; régression : la moyenne d'apprentissage quand aucun voisin) et **Categorical NB** (entrées discrétisées en 10 intervalles de quantiles avant le modèle).

## Tâches

- [x] T1 — Annulation (service, API, train entre les étapes et les plis).
- [x] T2 — Estimation de durée (API).
- [x] T3 — Courbe d'apprentissage dans le run.
- [x] T4 — Contraintes monotones.
- [x] T5 — Seuil de décision.
- [x] T6 — Radius neighbours, Categorical NB.
- [x] T7 — Tests.
- [x] T8 — UI (Cancel, Estimate, courbe d'apprentissage, seuil dans Validation, seuil retenu dans les résultats).
- [x] T9 — Docs, vérifications, navigateur, commit.

## Découvertes

- Tous les tests de la 019b sont passés du premier coup ; le navigateur a montré deux finitions : la courbe de HistGB affichait des scores négatifs (−110 M, la perte au signe inversé de scikit-learn) → affichée comme une perte positive ; un verdict « explains 0 % … 1 % better » → « does no better than the average » sous 1 % de R².
- L'optimisation (021) ignore les contraintes monotones dans ses plis (le modèle final les applique).
