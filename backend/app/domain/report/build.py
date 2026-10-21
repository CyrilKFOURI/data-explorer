"""Assemble a report from what the app already computes (overview, profiles, charts, matrix)."""

import re
from dataclasses import dataclass
from datetime import datetime

from app.domain.charts.prepare import Chart
from app.domain.columns.service import ColumnView
from app.domain.correlations.service import Correlations
from app.domain.filters.model import Condition
from app.domain.profiling.overview import Overview
from app.domain.report.model import Fact, Missing, PairRow, Report, VariableCard
from app.domain.variable.analyze import VariableProfile
from app.domain.variable.outliers import OutlierRule

ALPHA = 0.05
TOP_PAIRS = 10

TYPE_LABELS = {
    "numeric_continuous": "Continuous",
    "numeric_discrete": "Discrete",
    "categorical_nominal": "Category",
    "categorical_ordinal": "Ordered category",
    "boolean": "Boolean",
    "datetime": "Date / time",
    "text": "Free text",
    "identifier": "Identifier",
    "ignored": "Ignored",
}
METRIC_LABELS = {
    "pearson": "Pearson r",
    "spearman": "Spearman ρ",
    "cramers_v": "Cramér's V",
    "eta": "η (correlation ratio)",
}
NO_CHART = ("identifier", "high_cardinality", "empty")  # R-REP-06, R-REP-11

METHODS = [
    Fact(
        "Normality tests",
        "Shapiro-Wilk, D'Agostino-Pearson, Anderson-Darling, Jarque-Bera and Lilliefors each ask "
        "whether the values could come from a normal distribution; p < α = 0.05 rejects it. With "
        "many values, tiny departures are detected: the histogram tells whether they matter.",
    ),
    Fact(
        "Outliers (IQR)",
        "Values below Q1 − 1.5 × IQR or above Q3 + 1.5 × IQR, where IQR = Q3 − Q1 "
        "(Tukey's fences).",
    ),
    Fact(
        "Pearson r / Spearman ρ",
        "Linear (r) or monotonic (ρ, on ranks) link between two numbers, from −1 to 1.",
    ),
    Fact(
        "Cramér's V",
        "Strength of the link between two categories, from 0 to 1, from the χ² test, corrected "
        "for small tables (Bergsma).",
    ),
    Fact(
        "η (correlation ratio)",
        "Share of a number's variation explained by a category, from 0 to 1 (√ of the ANOVA η²).",
    ),
    Fact(
        "q-value and evidence",
        "p-values adjusted over every pair (Benjamini-Hochberg). Evidence combines the size of the "
        "effect (Cohen's conventions) and the adjusted p: strong, moderate, weak or none.",
    ),
]


@dataclass
class ColumnResult:
    """What the service gathered for one column."""

    view: ColumnView
    profile: VariableProfile | None = None
    chart: Chart | None = None
    outliers: OutlierRule | None = None
    error: str | None = None


def fmt(value: float | int | None, digits: int = 4) -> str:
    """1234567 → "1,234,567"; 0.123456 → "0.1235"; None → "—"."""
    if value is None:
        return "—"
    if isinstance(value, int):
        return f"{value:,}"
    if value != value:  # NaN
        return "—"
    if value == int(value) and abs(value) < 1e15:
        return f"{int(value):,}"
    if 1e-3 <= abs(value) < 1e6:
        return f"{value:,.{digits}g}" if abs(value) >= 1 else f"{value:.{digits}g}"
    return f"{value:.3g}"


def pct(value: float) -> str:
    return f"{value:.1f} %" if value < 10 else f"{value:.0f} %"


def size(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if n < 1024 or unit == "GB":
            return f"{n:.0f} {unit}" if unit == "B" else f"{n:.1f} {unit}"
        n /= 1024  # type: ignore[assignment]
    return f"{n} B"


def anchor(name: str, used: set[str]) -> str:
    base = "v-" + (re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "column")
    found, i = base, 2
    while found in used:
        found, i = f"{base}-{i}", i + 1
    used.add(found)
    return found


def _value(value: str | float | None) -> str:
    return fmt(value) if isinstance(value, float | int) else str(value)


def describe_condition(condition: Condition) -> str:
    """A filter in words: "Sex is female", "Age between 20 and 40"."""
    c, op = condition.column, condition.op
    no = condition.negate
    if op == "eq":
        text = f"{c} {'is not' if no else 'is'} {_value(condition.value)}"
    elif op == "in":
        text = f"{c} {'is not' if no else 'is'} {', '.join(condition.values)}"
    elif op in ("gt", "gte", "lt", "lte"):
        sign = {"gt": ">", "gte": "≥", "lt": "<", "lte": "≤"}[op]
        text = f"{'not ' if no else ''}{c} {sign} {_value(condition.value)}"
    elif op == "between":
        word = "not between" if no else "between"
        text = f"{c} {word} {_value(condition.low)} and {_value(condition.high)}"
    elif op == "contains":
        text = f"{c} {'does not contain' if no else 'contains'} “{condition.value}”"
    elif op == "starts_with":
        text = f"{c} {'does not start' if no else 'starts'} with “{condition.value}”"
    elif op == "is_null":
        text = f"{c} {'is not empty' if no else 'is empty'}"
    elif op == "part_in":
        part = (condition.part or "part").replace("_", " ")
        text = f"{part} of {c} {'is not' if no else 'is'} {', '.join(condition.values)}"
    elif op == "unique":
        keys = ", ".join([c, *condition.columns])
        text = f"one row per {keys} (the {condition.keep})"
    else:  # duplicated
        keys = ", ".join([c, *condition.columns])
        text = f"rows whose {keys} appear{' once' if no else ' more than once'}"
    return text


def normality_note(profile: VariableProfile) -> str | None:
    numeric = profile.numeric
    if numeric is None:
        return None
    normality = numeric.normality
    ran = [t for t in normality.tests if t.p_value is not None]
    if not ran:
        return f"Normality tests don't apply. {normality.reason or ''}".strip()
    rejected = sum(1 for t in ran if (t.p_value or 0) < ALPHA)
    if rejected:
        verdict = (
            f"{rejected} of {len(ran)} tests reject normality at α = {ALPHA}: probably not normal."
        )
    else:
        verdict = (
            f"No test rejects normality at α = {ALPHA}: consistent with a normal distribution."
        )
    if normality.sample < normality.n:
        verdict += f" Tests ran on a sample of {normality.sample:,} of the {normality.n:,} values."
    return verdict


def card(
    result: ColumnResult, alerts: list[str], missing_pct: float, used: set[str]
) -> VariableCard:
    view, profile = result.view, result.profile
    found = VariableCard(
        name=view.name,
        anchor=anchor(view.name, used),
        type=view.type,
        type_label=TYPE_LABELS.get(view.type, view.type),
        role=view.role,
        alerts=alerts,
    )
    facts = found.facts
    if result.error:
        found.notes.append(f"Could not be analysed: {result.error}")
    if profile and profile.numeric:
        d = profile.numeric.describe
        facts += [
            Fact("Missing", f"{d.missing:,} ({pct(missing_pct)})"),
            Fact("Distinct", fmt(d.distinct)),
            Fact("Mean", fmt(d.mean)),
            Fact("Std", fmt(d.std)),
            Fact("Min", fmt(d.min)),
            Fact("Q1", fmt(d.q1)),
            Fact("Median", fmt(d.median)),
            Fact("Q3", fmt(d.q3)),
            Fact("Max", fmt(d.max)),
            Fact("Skewness", fmt(d.skewness, 3)),
            Fact("Zeros", fmt(d.zeros)),
        ]
        if note := normality_note(profile):
            found.notes.append(note)
        if result.outliers is not None:
            o = result.outliers
            found.notes.append(
                f"{o.count:,} outliers by the IQR rule ({pct(o.pct)}), outside "
                f"[{fmt(o.low)}, {fmt(o.high)}]."
            )
    elif profile and profile.categorical:
        p = profile.categorical
        facts += [
            Fact("Missing", f"{p.missing:,} ({pct(missing_pct)})"),
            Fact("Distinct", fmt(p.distinct)),
        ]
        if p.top is not None and p.top_share is not None:
            facts.append(Fact("Most frequent", f"{p.top['label']} ({pct(p.top_share * 100)})"))
        if p.normalized_entropy is not None:
            facts.append(Fact("Evenness", fmt(p.normalized_entropy, 2)))
        if p.imbalanced:
            found.notes.append("Imbalanced: one category holds more than 80 % of the rows.")
        if p.rare_count:
            found.notes.append(f"{p.rare_count:,} rare categories (under 1 % of the rows each).")
    elif profile and profile.date:
        p = profile.date
        facts += [
            Fact("Missing", f"{p.missing:,} ({pct(missing_pct)})"),
            Fact("Distinct", fmt(p.distinct)),
            Fact("From", p.min or "—"),
            Fact("To", p.max or "—"),
            Fact("Step", p.step or p.granularity),
        ]
        if p.gap_count:
            found.notes.append(f"{p.gap_count:,} empty periods between the first and last date.")
    elif profile and profile.identifier:
        p = profile.identifier
        facts += [
            Fact("Missing", f"{p.missing:,} ({pct(missing_pct)})"),
            Fact("Distinct", fmt(p.distinct)),
            Fact("Unique", pct(p.unique_pct)),
            Fact("Duplicated values", fmt(p.duplicated_values)),
        ]
    elif profile and profile.text:
        p = profile.text
        facts += [
            Fact("Missing", f"{p.missing:,} ({pct(missing_pct)})"),
            Fact("Distinct", fmt(p.distinct)),
            Fact("Length", f"{fmt(p.min_length)} – {fmt(p.max_length)}"),
            Fact("Mean length", fmt(p.mean_length, 3)),
        ]
    else:
        facts.append(Fact("Missing", pct(missing_pct)))
    if result.chart is not None and result.chart.kind not in NO_CHART and view.type != "text":
        found.chart = result.chart
    return found


def build_report(
    *,
    title: str,
    source: str,
    version: str,
    overview: Overview,
    results: list[ColumnResult],
    excluded: list[str],
    correlations: Correlations | None,
    conditions: list[Condition],
    now: datetime,
) -> Report:
    by_column: dict[str, list[str]] = {}
    for alert in overview.alerts:
        for name in alert.columns:
            by_column.setdefault(name, []).append(alert.message)
    used: set[str] = set()
    variables = [
        card(
            r,
            by_column.get(r.view.name, []),
            overview.column_stats[r.view.name].missing_pct
            if r.view.name in overview.column_stats
            else 0.0,
            used,
        )
        for r in results
    ]
    duplicate_columns = sum(len(group) for group in overview.duplicate_columns)
    summary = [
        Fact(
            "Rows",
            f"{overview.rows:,}"
            + (f" of {overview.total_rows:,}" if overview.rows != overview.total_rows else ""),
        ),
        Fact(
            "Columns",
            f"{overview.used_columns:,}"
            + (f" of {overview.columns:,}" if overview.used_columns != overview.columns else ""),
        ),
        Fact("Missing cells", f"{overview.missing_cells:,} ({pct(overview.missing_pct)})"),
        Fact("Duplicate rows", f"{overview.duplicate_rows:,}"),
        Fact("Duplicate columns", f"{duplicate_columns:,}"),
        Fact("Size", size(overview.size_bytes)),
    ]
    types = [
        Fact(TYPE_LABELS.get(kind, kind), f"{count:,}")
        for kind, count in sorted(overview.types.items(), key=lambda item: -item[1])
    ]
    missing = sorted(
        (
            Missing(r.view.name, overview.column_stats[r.view.name].missing_pct)
            for r in results
            if r.view.name in overview.column_stats
            and overview.column_stats[r.view.name].missing_pct > 0
        ),
        key=lambda m: -m.pct,
    )
    pairs: list[PairRow] = []
    insights: list[str] = []
    matrix = None
    if correlations is not None and len(correlations.matrix.columns) >= 2:
        matrix = correlations.matrix
        pairs = [
            PairRow(p.a, p.b, METRIC_LABELS.get(p.metric, p.metric), p.value, p.q_value, p.evidence)
            for p in matrix.pairs[:TOP_PAIRS]
        ]
        insights = [i.text for i in sorted(correlations.insights, key=lambda i: -i.score)]
    return Report(
        title=title,
        source=source,
        generated_at=now.strftime("%Y-%m-%d %H:%M"),
        version=version,
        rows=overview.rows,
        total_rows=overview.total_rows,
        columns=overview.used_columns,
        filters=[describe_condition(c) for c in conditions],
        summary=summary,
        types=types,
        alerts=[a.message for a in overview.alerts],
        variables=variables,
        excluded=excluded,
        matrix=matrix,
        pairs=pairs,
        insights=insights,
        missing=missing,
        complete=len(results) - len(missing),
        methods=METHODS,
    )


def file_name(title: str) -> str:
    """R-REP-13: "<dataset>-report.html", without characters a file system refuses."""
    safe = re.sub(r'[\\/:*?"<>|\x00-\x1f]+', "_", title).strip(" .") or "dataset"
    return f"{safe[:120]}-report.html"
