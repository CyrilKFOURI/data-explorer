# Preparing and judging a model

1. **Target first** (`list_ml_targets`). Check the task (classification or regression) and, for classification, the class balance. Strong imbalance changes the metric: use balanced accuracy, F1 or ROC AUC, never plain accuracy.
2. **Leakage.** Before training, look for columns that give the answer away: identifiers, columns filled after the outcome (a "survived_date", a "refund_amount" to predict churn), near copies of the target. A suspiciously perfect score (AUC ≥ 0.99) almost always means leakage: say so and name the suspect.
3. **Baseline.** Every score is read against the baseline the app reports (majority class, mean). A model that barely beats it has learned little.
4. **Train** (`train_model`) with the app's recommended model first; `compare_models` only if the user wants the best one. Validation is cross-validated: quote the mean and the spread.
5. **Tune** (`tune_model`) only after a reasonable first model, and say how much it gained. A gain inside the spread is noise.
6. **Explain** (`explain_model`). Importance says what the model uses, not what causes the outcome. Read SHAP directions in plain words ("higher Fare pushes towards survival").
7. **Limits.** Sample size, missing values imputed, columns excluded, and that the model reflects this data only.

Training takes time: say what you are doing while it runs, and do not retrain without a reason.
