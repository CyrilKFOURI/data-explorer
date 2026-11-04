# Synthetic data

- **Purpose first.** Sharing a dataset safely, testing a pipeline, or adding rows for a demo: it decides the method and how much privacy matters.
- **Plan** (`plan_synthetic`): the app recommends a method from the size and the column types. Identifiers and free text are dropped or regenerated, never copied.
- **Generate** (`generate_synthetic`), then read the two reports together:
  - **Fidelity**: distributions and pairwise relationships compared with the original. High fidelity on the columns that matter to the purpose is the goal, not a perfect overall score.
  - **Privacy**: the distance to the closest real record (DCR) and the share of near copies. Near copies of real rows mean the data must not be published, whatever the fidelity.
- **Trade-off.** More fidelity usually means less privacy. Say which way the run leans.
- **Save** (`save_synthetic_dataset`) only if the user wants to keep it; it asks them first, and the copy appears as a new dataset.

Never call synthetic data anonymous on fidelity alone: quote the privacy verdict.
