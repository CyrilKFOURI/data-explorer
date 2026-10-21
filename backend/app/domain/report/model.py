"""What a dataset report holds (spec 025): plain data, rendered to HTML by `html.render`."""

from dataclasses import dataclass, field

from app.domain.charts.prepare import Chart
from app.domain.correlations.matrix import Matrix


@dataclass
class Fact:
    label: str
    value: str


@dataclass
class VariableCard:
    """One column (R-REP-05): key figures, verdicts, alerts and its chart."""

    name: str
    anchor: str  # id of the card in the page
    type: str
    type_label: str
    role: str | None
    facts: list[Fact] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)  # verdicts: normality, outliers
    alerts: list[str] = field(default_factory=list)
    chart: Chart | None = None  # None for identifiers and free text (R-REP-06)


@dataclass
class PairRow:
    a: str
    b: str
    metric: str  # "Pearson r", "Cramér's V"…
    value: float
    q_value: float | None
    evidence: str


@dataclass
class Missing:
    name: str
    pct: float  # 0..100


@dataclass
class Report:
    title: str
    source: str
    generated_at: str
    version: str
    rows: int
    total_rows: int
    columns: int
    filters: list[str]  # active filters, in words (R-REP-03)
    summary: list[Fact]
    types: list[Fact]  # columns per type
    alerts: list[str]
    variables: list[VariableCard]
    excluded: list[str]  # columns left out of the analysis (R-REP-10)
    matrix: Matrix | None
    pairs: list[PairRow]
    insights: list[str]
    missing: list[Missing]  # columns with missing values, most first
    complete: int  # columns without any missing value
    methods: list[Fact]  # R-REP-09
