# Indicators over time

- **Start from the question.** "Revenue per month by country" fixes the measure, the aggregation, the time grain and the split. `suggest_kpis` proposes sensible ones from the columns; `compute_kpi` computes one.
- **Aggregation.** Sums for amounts and counts, means for levels (prices, scores), distinct counts for customers. A **ratio** is the ratio of sums (total revenue / total orders), never the mean of per-row ratios.
- **Time grain.** Choose it from the date range: days for a few weeks, weeks or months for a year, months or quarters beyond. The last period is often incomplete: say so before reading a drop.
- **Comparisons.** Period over period and year over year answer different questions; seasonal data needs year over year. Shares of a total show the mix, not the growth.
- **Splits.** Keep the few largest groups; small groups move a lot by chance.
- **Saving.** Offer `save_kpi` only when the user wants to keep the indicator; it asks them first.

Report the latest value, the change and its period, and the one movement worth attention.
