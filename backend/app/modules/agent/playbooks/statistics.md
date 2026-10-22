# Reading a statistical test

- **Effect before p-value.** Report the effect size and its reading (Cramér's V, Cohen's d, η, correlation) first. With thousands of rows, a negligible effect has a tiny p-value: say "significant but negligible in practice".
- **Usual scales.** Cohen's d: 0.2 small, 0.5 medium, 0.8 large. Cramér's V (and |r|): 0.1 small, 0.3 medium, 0.5 large. η² follows d's logic on its own scale; quote the app's reading when it gives one.
- **Conditions.** Check what the tool reports: normality, equal variances, expected counts in a contingency table (below 5 in many cells weakens a chi-square). The app picks a robust test when conditions fail (Welch, Mann-Whitney, Kruskal-Wallis); name the test it used.
- **Many tests.** Comparing many pairs makes a few look significant by chance. When you scan many relationships, keep only effects that are both clear and meaningful, and say the scan was broad.
- **No evidence is not evidence of absence.** A non-significant result on few rows says "we can't tell", not "there is no link".
- **Association is not causation.** Name plausible confounders (in Titanic: class and fare go together; age and family size too).
- **Filters.** A result on filtered rows holds for those rows only.

Write p-values as "p < 0.001" below that threshold, otherwise with two significant digits.
