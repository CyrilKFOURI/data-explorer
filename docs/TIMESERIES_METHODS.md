# Séries temporelles — catalogue des méthodes

Référence de la page [10-series-temporelles.md](pages/10-series-temporelles.md) et des jalons 012 à 015. **Toutes les méthodes existantes pour une question sont proposées** ; quelques-unes, les plus fiables, sont cochées par défaut pour que la page reste rapide et lisible.

## Règle d'interface : « Methods »

Chaque section commence par une rangée de méthodes :

```
Stationarity                                                     ● Not stationary
Methods  [ADF ✓] [KPSS ✓] [Phillips–Perron ✓]  + Add method ▾        ⚙ Options
```

- Les méthodes cochées par défaut sont calculées d'office ; **+ Add method** ouvre la liste complète de la section, groupée, chaque méthode avec une phrase et son hypothèse nulle (« H0: the series has a unit root »). Cocher l'ajoute au calcul et au tableau.
- **⚙ Options** de chaque méthode (retards, type de régression, critère d'information…) : petit panneau avec des défauts justifiés, comme les réglages ML.
- Le **verdict de la section** se fonde sur les méthodes cochées ; il cite celles qui concordent et signale les désaccords (« ADF and PP reject a unit root, KPSS rejects stationarity: likely trend-stationary »).
- Le choix des méthodes est mémorisé (préférence du navigateur) et vaut pour toutes les séries.
- Un tableau unique par section : méthode, statistique, p-value, valeurs critiques, hypothèse nulle, conclusion au seuil α (réglable dans Settings, défaut 0,05).

## Catalogue

Légende : ★ = coché par défaut.

### Tendance (011, 012)

| Méthode | Question / H0 | Implémentation |
|---|---|---|
| ★ Mann-Kendall | H0 : pas de tendance monotone | maison (numpy) |
| ★ Pente de Sen | ampleur de la tendance (unités / période) + IC | maison |
| Mann-Kendall modifié (Hamed–Rao) | idem, corrigé de l'autocorrélation | maison |
| Mann-Kendall saisonnier | tendance sans confondre la saisonnalité | maison |
| Cox–Stuart | H0 : pas de tendance (test des signes) | maison |
| ρ de Spearman avec le temps | corrélation de rang avec le temps | scipy |
| Régression linéaire sur le temps | pente, t-test, R² | statsmodels |

### Saisonnalité (012)

| Méthode | Question / H0 | Implémentation |
|---|---|---|
| ★ Kruskal–Wallis entre sous-périodes | H0 : même niveau pour chaque mois / jour… | scipy |
| Friedman | idem, appariement par cycle | scipy |
| Test QS | H0 : pas d'autocorrélation saisonnière | maison |
| ★ Périodogramme (pic spectral) | période dominante | scipy.signal |
| Test g de Fisher | H0 : pas de périodicité (bruit blanc) | maison |
| ACF au retard saisonnier | autocorrélation au retard de la période | statsmodels |

### Décomposition (012)

| Méthode | Notes | Implémentation |
|---|---|---|
| ★ STL robuste | une saisonnalité ; lissage saisonnier constant sous 7 cycles, version ordinaire si la robuste dégénère | statsmodels |
| MSTL | plusieurs saisonnalités (jour + semaine + année) | statsmodels |
| Classique additive / multiplicative | moyennes mobiles | statsmodels |
| Forces de tendance et de saisonnalité | Hyndman, 0–1 | maison |

### Stationnarité (013)

| Méthode | H0 | Implémentation |
|---|---|---|
| ★ ADF (Dickey–Fuller augmenté) | racine unitaire | statsmodels |
| ★ KPSS (niveau / tendance) | stationnaire | statsmodels |
| ★ Phillips–Perron | racine unitaire (robuste) | maison (Newey–West, p-values MacKinnon) |
| DF-GLS (Elliott–Rothenberg–Stock) | racine unitaire, plus puissant | maison (constante, retards par BIC) |
| Zivot–Andrews | racine unitaire, avec une rupture inconnue | statsmodels |
| Ratio de variance (Lo–MacKinlay) | marche aléatoire | maison (robuste, q = 4) |
| Range unit root (RUR) | stationnaire (H0 selon statsmodels), non paramétrique | statsmodels |
| OCSB / Canova–Hansen | racine unitaire **saisonnière** | pas encore (la différence saisonnière est proposée et testée) |

### Autocorrélation (013)

| Méthode | H0 / rôle | Implémentation |
|---|---|---|
| ★ ACF · ★ PACF | profils (PACF : Yule-Walker, OLS, Burg au choix) | statsmodels |
| ★ Modèle AR(p) | p choisi par l'AIC ou par l'utilisateur ; coefficients, AIC / BIC de chaque ordre, Ljung–Box des résidus | statsmodels |
| ★ Ljung–Box | pas d'autocorrélation jusqu'au retard k | statsmodels |
| Box–Pierce | idem (version d'origine) | statsmodels |
| ★ Durbin–Watson | autocorrélation d'ordre 1 des résidus | statsmodels |
| Breusch–Godfrey | autocorrélation d'ordre p des résidus | statsmodels |
| Runs test (Wald–Wolfowitz) | caractère aléatoire de la séquence | statsmodels |
| Test des points de retournement | caractère aléatoire | maison |
| Test de rang de Bartels | caractère aléatoire | maison |
| Lag plot | visualisation y(t) vs y(t−k) | — |

### Volatilité / hétéroscédasticité (014)

| Méthode | H0 | Implémentation |
|---|---|---|
| ★ Variance glissante | visualisation | DuckDB / numpy |
| ★ Breusch–Pagan | variance constante dans le temps | statsmodels |
| White | idem, forme quadratique | statsmodels |
| Goldfeld–Quandt | début et fin de même variance | statsmodels |
| ★ ARCH-LM (Engle) | pas d'effet ARCH | statsmodels |
| McLeod–Li | pas d'autocorrélation des carrés | statsmodels (Ljung–Box sur les carrés) |
| Levene · Brown–Forsythe · Bartlett · Fligner–Killeen | variances égales entre fenêtres | scipy |

### Normalité et loi des résidus (014)

| Méthode | Implémentation |
|---|---|
| ★ Shapiro–Wilk · ★ D'Agostino K² · Jarque–Bera · Anderson–Darling · Lilliefors · Kolmogorov–Smirnov · Cramér–von Mises | scipy / statsmodels (mêmes `TestResult` que la fiche variable) |
| ★ QQ-plot | — |
| Ajustement de lois (série, rendements ou résidus) | `domain/stats/distribution_fit.py` |

### Ruptures et homogénéité (014)

| Méthode | Rôle | Implémentation |
|---|---|---|
| ★ PELT | plusieurs ruptures (moyenne, ou moyenne + variance) | maison |
| Segmentation binaire | alternative de recherche | maison |
| Coût « tendance par segments » | ruptures de pente (choisi automatiquement si la série a une tendance) | maison |
| Bottom-up · Fenêtre glissante | alternatives de recherche | pas encore |
| Test de Chow | rupture à une date donnée | statsmodels (OLS) |
| CUSUM des résidus OLS | stabilité des paramètres | statsmodels |
| Pettitt | une rupture de niveau (non paramétrique) | maison |
| Buishand (range) · SNHT | homogénéité | maison |

### Anomalies (014)

| Méthode | Implémentation |
|---|---|
| ★ z-score robuste sur résidus (MAD) | maison |
| IQR sur résidus | maison |
| z-score glissant | maison |
| Filtre de Hampel | maison |
| Test ESD généralisé (Rosner, α = 5 %) | maison |
| Isolation forest (fenêtres glissantes) | scikit-learn |
| Local outlier factor (fenêtres glissantes) | scikit-learn |
| Autoencodeur masqué (MLP : chaque période reconstruite à partir de ses voisines) | scikit-learn |
| LSTM-autoencoder | non retenu : PyTorch (1 à 2 Go dans l'image), lent sur CPU, rarement meilleur sur une série courte |

### Prévision (015)

| Méthode | Implémentation |
|---|---|
| ★ Naive · ★ Seasonal naive · Drift · Mean | maison |
| SES · Holt · Holt-Winters | statsmodels |
| ★ ETS automatique (AICc ; multiplicatif seulement si valeurs > 0) | statsmodels |
| Theta | statsmodels |
| ★ ARIMA automatique · SARIMA (ordres manuels) | statsmodels |
| Régression linéaire : tendance + indicatrices de saison (TSLM) | statsmodels |
| Gradient boosting sur les retards (tendance retirée, récursif) | scikit-learn |
| Réseau de neurones MLP sur les retards | scikit-learn |
| RNN / LSTM | non retenus : PyTorch, et sur une série isolée et courte ils font en général moins bien qu'ETS / ARIMA (compétition M4) |

Métriques de prévision (toutes affichables, ★ par défaut) : ★ MAE, ★ RMSE, ★ MASE, MAPE, sMAPE, RMSSE, biais (ME), couverture des intervalles, score d'intervalle (Winkler).

## Dépendances

- `statsmodels` : l'essentiel.
- `arch` : non ajouté (pas validé). Phillips–Perron, DF-GLS et le ratio de variance sont écrits à la main ; Phillips–Perron sans retard est vérifié égal au Dickey-Fuller de statsmodels. Passer à `arch` reste possible sans changer l'interface.
- « maison » = numpy / scipy dans `domain/timeseries/`, chaque méthode testée contre une référence publiée ou une bibliothèque de référence utilisée seulement en test.
