from app.modules.agent.engine.grounding import check

RESULT = (
    '{"rows": 891, "female": {"survived": 233, "of": 314, "share": 0.7420382}, '
    '"cramers_v": 0.5433, "p": 3.71e-59, "mean_fare": 48.3954, "d": -0.547}'
)


def test_figures_found_in_tool_results_are_grounded() -> None:
    answer = (
        "**Sex** matters most: 74.2% of women survived (233 of 314), Cramér's V = 0.543, "
        "p = 3.71 × 10⁻⁵⁹. Survivors paid 48.40 on average (d = -0.55), over 891 rows."  # noqa: RUF001
    )

    found = check(answer, [RESULT])

    assert found.unverified == []
    assert found.checked == 8


def test_figures_the_model_made_up_or_computed_are_reported() -> None:
    answer = "Women survived at 74.2%, a 55.3 point gap, and 12,400 passengers were aboard."

    found = check(answer, [RESULT])

    assert found.unverified == ["55.3", "12,400"]


def test_list_numbers_thresholds_years_and_names_are_ignored() -> None:
    answer = (
        "1. Check p < 0.05 for the 3rd class in Q3 2024.\n"
        "2. Train 2 models with a 95% interval, see column x_17."
    )

    found = check(answer, [RESULT])

    assert found.checked == 0 and found.unverified == []


def test_other_sources_count_too() -> None:
    found = check(
        "The file has 12 columns and Age is 19.9% missing.",
        ["", '"missing_pct": 19.87', "12 columns"],
    )

    assert found.unverified == []
