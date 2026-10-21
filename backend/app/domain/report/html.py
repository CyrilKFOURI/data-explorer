"""Render a report as one self-contained HTML page (R-REP-01): inline CSS, no script, no link out,
light and dark themes from the system, a print style sheet."""

from html import escape

from app.domain.report import svg
from app.domain.report.model import Fact, Report, VariableCard

# The app's tokens (frontend/src/styles/tokens.css), light then dark.
CSS = """
:root {
  color-scheme: light dark;
  --surface-0: #f7f5f2; --surface-1: #fffdfa; --surface-2: #efebe5;
  --ink-1: #24201b; --ink-2: #5c544a; --ink-3: #71695f; --line: #e2dcd3;
  --accent: #ad4a27; --warn: #8f5b00; --chart-1: #2a78d6; --chart-8: #e34948;
}
@media (prefers-color-scheme: dark) {
  :root {
    --surface-0: #14120f; --surface-1: #1d1a16; --surface-2: #27231e;
    --ink-1: #ede8e1; --ink-2: #b5aca0; --ink-3: #988f83; --line: #332e28;
    --accent: #e07a50; --warn: #e0a23a; --chart-1: #3987e5; --chart-8: #e66767;
  }
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--surface-0); color: var(--ink-1);
  font: 14px/1.5 system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
}
main { max-width: 1120px; margin: 0 auto; padding: 32px 24px 64px; }
h1 { font-size: 28px; line-height: 1.2; margin: 0 0 4px; letter-spacing: -0.01em; }
h2 { font-size: 20px; margin: 48px 0 12px; padding-top: 12px; border-top: 1px solid var(--line); }
h3 { font-size: 15px; margin: 0; overflow-wrap: anywhere; }
p { margin: 0 0 8px; }
.muted { color: var(--ink-3); }
.small { font-size: 12px; }
a { color: var(--accent); text-decoration: none; }
a:hover { text-decoration: underline; }
.filters { margin-top: 8px; color: var(--ink-2); }
.toc {
  display: flex; flex-wrap: wrap; gap: 4px 16px; margin: 20px 0 0; padding: 0; list-style: none;
}
.band { display: flex; flex-wrap: wrap; margin: 16px 0; border-block: 1px solid var(--line); }
.band div { flex: 1 1 140px; padding: 10px 16px; }
.band div + div { border-left: 1px solid var(--line); }
.band dt { font-size: 12px; color: var(--ink-3); }
.band dd { margin: 0; font-size: 20px; font-weight: 600; font-variant-numeric: tabular-nums; }
ul.alerts { margin: 8px 0; padding-left: 18px; color: var(--ink-2); }
ul.alerts li::marker { color: var(--warn); }
.cards {
  display: grid; gap: 16px;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 500px), 1fr));
}
.card {
  background: var(--surface-1); border: 1px solid var(--line); border-radius: 8px; padding: 16px;
  break-inside: avoid;
}
.card header {
  display: flex; align-items: baseline; justify-content: space-between; gap: 8px;
  margin-bottom: 8px;
}
.tag { font-size: 12px; color: var(--ink-3); white-space: nowrap; }
dl.facts {
  display: grid; grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); gap: 4px 12px;
  margin: 0 0 8px;
}
dl.facts dt { font-size: 11px; color: var(--ink-3); }
dl.facts dd { margin: 0; font-variant-numeric: tabular-nums; overflow-wrap: anywhere; }
.notes { margin: 8px 0 0; padding-left: 18px; color: var(--ink-2); font-size: 13px; }
.chart { display: block; max-width: 100%; height: auto; margin-top: 8px; overflow: visible; }
.chart text { font-size: 11px; fill: var(--ink-2); }
.chart text.value { fill: var(--ink-3); }
.chart text.cell { fill: var(--ink-1); font-size: 10px; }
.chart text.cell.strong { fill: #fff; }
.chart .bar { fill: var(--chart-1); }
.chart .bar.others { fill: var(--ink-3); }
.chart .track { fill: var(--surface-2); }
.chart .axis { stroke: var(--line); }
.scroll { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; font-variant-numeric: tabular-nums; }
th, td { text-align: left; padding: 6px 10px; border-bottom: 1px solid var(--line); }
th { font-size: 12px; font-weight: 500; color: var(--ink-3); }
td.num { text-align: right; }
dl.methods dt { font-weight: 600; margin-top: 10px; }
dl.methods dd { margin: 0; color: var(--ink-2); }
footer { margin-top: 48px; color: var(--ink-3); font-size: 12px; }
@media print {
  :root {
    --surface-0: #fff; --surface-1: #fff; --surface-2: #efebe5;
    --ink-1: #24201b; --ink-2: #5c544a; --ink-3: #71695f; --line: #e2dcd3;
    --accent: #ad4a27; --chart-1: #2a78d6; --chart-8: #e34948;
  }
  main { max-width: none; padding: 0; }
  .toc { display: none; }
  h2 { break-after: avoid; }
}
"""


def _facts(facts: list[Fact], css: str) -> str:
    items = "".join(
        f"<div><dt>{escape(f.label)}</dt><dd>{escape(f.value)}</dd></div>" for f in facts
    )
    return f'<dl class="{css}">{items}</dl>'


def _card(card: VariableCard) -> str:
    same = card.role and card.role.lower() == card.type_label.lower()
    role = f" · {escape(card.role)}" if card.role and not same else ""
    parts = [
        f'<article class="card" id="{card.anchor}">',
        f"<header><h3>{escape(card.name)}</h3>"
        f'<span class="tag">{escape(card.type_label)}{role}</span></header>',
        _facts(card.facts, "facts"),
    ]
    notes = card.notes + card.alerts
    if notes:
        parts.append(
            '<ul class="notes">' + "".join(f"<li>{escape(n)}</li>" for n in notes) + "</ul>"
        )
    if card.chart is not None:
        parts.append(svg.chart_svg(card.chart, f"Distribution of {card.name}"))
    parts.append("</article>")
    return "".join(parts)


def _correlations(report: Report) -> str:
    if report.matrix is None:
        return '<p class="muted">Fewer than two columns can be compared.</p>'
    matrix = report.matrix
    parts = []
    note = f"Computed on {matrix.rows:,} rows"
    if matrix.sampled:
        note += f" (a reproducible sample of the {matrix.total:,})"
    if matrix.truncated:
        note += f"; {matrix.truncated} more columns left out (at most {len(matrix.columns)})"
    parts.append(f'<p class="muted small">{escape(note)}.</p>')
    parts.append(f'<div class="scroll">{svg.heatmap(matrix)}</div>')
    if report.pairs:
        rows = "".join(
            f"<tr><td>{escape(p.a)} × {escape(p.b)}</td><td>{escape(p.metric)}</td>"
            f'<td class="num">{p.value:.3f}</td>'
            f'<td class="num">{"—" if p.q_value is None else f"{p.q_value:.2g}"}</td>'
            f"<td>{escape(p.evidence.capitalize())}</td></tr>"
            for p in report.pairs
        )
        parts.append(
            "<h3 style='margin-top:20px'>Strongest links</h3>"
            '<div class="scroll"><table><thead><tr><th>Pair</th><th>Measure</th>'
            '<th class="num">Value</th><th class="num">q-value</th><th>Evidence</th></tr></thead>'
            f"<tbody>{rows}</tbody></table></div>"
        )
    if report.insights:
        parts.append(
            "<h3 style='margin-top:20px'>Insights</h3><ul class='alerts'>"
            + "".join(f"<li>{escape(text)}</li>" for text in report.insights)
            + "</ul>"
        )
    return "".join(parts)


def render(report: Report) -> str:
    title = escape(report.title)
    filters = (
        '<p class="filters">Filtered: ' + escape(" · ".join(report.filters)) + "</p>"
        if report.filters
        else ""
    )
    toc = "".join(
        f'<li><a href="#{key}">{label}</a></li>'
        for key, label in (
            ("summary", "Summary"),
            ("variables", "Variables"),
            ("correlations", "Correlations"),
            ("missing", "Missing values"),
            ("methods", "Methods"),
        )
    )
    variables_toc = " · ".join(
        f'<a href="#{c.anchor}">{escape(c.name)}</a>' for c in report.variables
    )
    excluded = (
        '<p class="muted small">Left out of the analysis: '
        f"{escape(', '.join(report.excluded))}.</p>"
        if report.excluded
        else ""
    )
    alerts = (
        "<ul class='alerts'>" + "".join(f"<li>{escape(a)}</li>" for a in report.alerts) + "</ul>"
        if report.alerts
        else '<p class="muted">No quality alert.</p>'
    )
    missing = (
        svg.missing_bars(report.missing)
        + (
            f'<p class="muted small">{report.complete:,} columns have no missing value.</p>'
            if report.complete
            else ""
        )
        if report.missing
        else '<p class="muted">No column has missing values.</p>'
    )
    summary = _facts(report.summary, "band")
    types = escape(" · ".join(f"{f.label} {f.value}" for f in report.types))
    after = " (after the filters)" if report.filters else ""
    methods = "".join(
        f"<dt>{escape(m.label)}</dt><dd>{escape(m.value)}</dd>" for m in report.methods
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title} · Data report</title>
<style>{CSS}</style>
</head>
<body>
<main>
<header>
<p class="muted small">Data report</p>
<h1>{title}</h1>
<p class="muted">{escape(report.source)}</p>
{filters}
<ul class="toc">{toc}</ul>
</header>

<section id="summary">
<h2>Summary</h2>
{summary}
<p class="muted small">Columns by type: {types}</p>
<h3 style="margin-top:16px">Quality alerts</h3>
{alerts}
</section>

<section id="variables">
<h2>Variables</h2>
<p class="small">{variables_toc}</p>
{excluded}
<div class="cards">{"".join(_card(c) for c in report.variables)}</div>
</section>

<section id="correlations">
<h2>Correlations</h2>
{_correlations(report)}
</section>

<section id="missing">
<h2>Missing values</h2>
{missing}
</section>

<section id="methods">
<h2>Methods</h2>
<dl class="methods">{methods}</dl>
</section>

<footer>Generated on {escape(report.generated_at)} by Data Explorer {escape(report.version)}.
Every figure is computed on the rows above{after}; the report holds counts, statistics and the
most frequent values, never whole rows.</footer>
</main>
</body>
</html>
"""
