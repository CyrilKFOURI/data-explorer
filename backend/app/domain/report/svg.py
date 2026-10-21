"""Small SVG charts for the report (R-REP-06): no script, colours from the page's CSS tokens,
one native tooltip (<title>) per mark. Every text from the data is escaped (R-REP-12)."""

from html import escape

from app.domain.charts.prepare import Chart
from app.domain.correlations.matrix import Matrix
from app.domain.report.model import Missing

WIDTH = 360
LABEL = 11  # font size
GAP = 2  # surface gap between adjacent fills


def _n(value: float) -> str:
    return f"{value:.1f}".rstrip("0").rstrip(".")


def _short(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[: limit - 1] + "…"


def _svg(width: float, height: float, body: list[str], label: str) -> str:
    return (
        f'<svg class="chart" viewBox="0 0 {_n(width)} {_n(height)}" width="{_n(width)}" '
        f'height="{_n(height)}" role="img" aria-label="{escape(label)}">' + "".join(body) + "</svg>"
    )


def _rect(css: str, x: float, y: float, w: float, h: float, tip: str | None, rx: int = 0) -> str:
    title = f"<title>{escape(tip)}</title>" if tip else ""
    corner = f' rx="{rx}"' if rx else ""
    return (
        f'<rect class="{css}" x="{_n(x)}" y="{_n(y)}" width="{_n(w)}" height="{_n(h)}"{corner}>'
        f"{title}</rect>"
    )


def _tick(value: float) -> str:
    if value == int(value) and abs(value) < 1e9:
        return f"{int(value):,}"
    return f"{value:.3g}"


def histogram(chart: Chart, label: str, height: int = 150) -> str:
    bins = chart.bins
    if not bins:
        return ""
    top = max(b["count"] for b in bins) or 1
    plot = height - 22
    step = WIDTH / len(bins)
    body = []
    for i, b in enumerate(bins):
        h = plot * b["count"] / top
        x = i * step
        tip = f"{_tick(b['start'])} – {_tick(b['end'])}: {b['count']:,} rows"
        body.append(_rect("bar", x + GAP / 2, plot - h, max(step - GAP, 1), max(h, 0), tip))
    body.append(f'<line class="axis" x1="0" x2="{WIDTH}" y1="{_n(plot)}" y2="{_n(plot)}"/>')
    first, last = bins[0]["start"], bins[-1]["end"]
    body.append(f'<text x="0" y="{height - 6}">{escape(_tick(first))}</text>')
    body.append(
        f'<text x="{WIDTH}" y="{height - 6}" text-anchor="end">{escape(_tick(last))}</text>'
    )
    return _svg(WIDTH, height, body, label)


def bars(chart: Chart, label: str) -> str:
    """Categories as horizontal bars, most frequent first (or in their order), "Others" last."""
    rows: list[tuple[str, int, bool]] = [(b["label"], b["count"], False) for b in chart.bars]
    if chart.others:
        rows.append((f"Others ({chart.others['categories']:,})", chart.others["count"], True))
    if not rows:
        return ""
    total = sum(count for _, count, _ in rows) or 1
    top = max(count for _, count, _ in rows) or 1
    line = 20
    label_width, value_width = 110, 70
    room = WIDTH - label_width - value_width
    body = []
    for i, (name, count, others) in enumerate(rows):
        y = i * line
        w = room * count / top
        share = 100 * count / total
        tip = f"{name}: {count:,} rows ({share:.1f} %)"
        body.append(
            f'<text x="{label_width - 6}" y="{y + 14}" text-anchor="end">'
            f"{escape(_short(name, 16))}</text>"
        )
        css = "bar others" if others else "bar"
        body.append(_rect(css, label_width, y + 3, max(w, 1), line - 6, tip, rx=2))
        body.append(
            f'<text class="value" x="{_n(label_width + w + 6)}" y="{y + 14}">'
            f"{count:,} · {share:.0f} %</text>"
        )
    return _svg(WIDTH, line * len(rows), body, label)


def timeline(chart: Chart, label: str, height: int = 150) -> str:
    """Rows per period, as columns; first and last period written below."""
    periods = chart.bars
    if not periods:
        return ""
    top = max(b["count"] for b in periods) or 1
    plot = height - 22
    step = WIDTH / len(periods)
    gap = GAP if step > 4 else 0
    body = []
    for i, b in enumerate(periods):
        h = plot * b["count"] / top
        tip = f"{b['label']}: {b['count']:,} rows"
        body.append(_rect("bar", i * step + gap / 2, plot - h, max(step - gap, 0.5), h, tip))
    body.append(f'<line class="axis" x1="0" x2="{WIDTH}" y1="{_n(plot)}" y2="{_n(plot)}"/>')
    body.append(f'<text x="0" y="{height - 6}">{escape(periods[0]["label"])}</text>')
    last = escape(periods[-1]["label"])
    body.append(f'<text x="{WIDTH}" y="{height - 6}" text-anchor="end">{last}</text>')
    return _svg(WIDTH, height, body, label)


def chart_svg(chart: Chart, label: str) -> str:
    if chart.kind == "histogram":
        return histogram(chart, label)
    if chart.kind == "timeline":
        return timeline(chart, label)
    if chart.kind == "bars":
        return bars(chart, label)
    return ""


def _cell_style(value: float | None) -> str:
    """Diverging: −1 red (chart-8), 0 the line colour, +1 blue (chart-1); 0..1 measures go blue."""
    if value is None:
        return "fill: var(--surface-2)"
    share = min(abs(value), 1.0) * 100
    pole = "var(--chart-1)" if value >= 0 else "var(--chart-8)"
    return f"fill: color-mix(in oklab, {pole} {share:.0f}%, var(--line))"


def heatmap(matrix: Matrix) -> str:
    order = matrix.clustered or list(range(len(matrix.columns)))
    names = [matrix.columns[i].name for i in order]
    n = len(names)
    cell = max(14, min(32, 560 // max(n, 1)))
    left = top = min(150, 8 + 7 * max(len(_short(name, 20)) for name in names))
    size = cell * n
    body = []
    for row, i in enumerate(order):
        y = top + row * cell
        body.append(
            f'<text x="{left - 6}" y="{_n(y + cell / 2 + 4)}" text-anchor="end">'
            f"{escape(_short(names[row], 20))}</text>"
        )
        for col, j in enumerate(order):
            value = matrix.values[i][j]
            metric = matrix.metrics[i][j]
            x = left + col * cell
            tip = f"{names[row]} × {names[col]}"
            if value is not None:
                tip += f": {value:.2f}" + (f" ({metric})" if metric else "")
            body.append(
                f'<rect x="{x}" y="{y}" width="{cell - 1}" height="{cell - 1}" '
                f'style="{_cell_style(value)}"><title>{escape(tip)}</title></rect>'
            )
            if value is not None and cell >= 28 and i != j:
                strong = abs(value) >= 0.6
                body.append(
                    f'<text class="{"cell strong" if strong else "cell"}" '
                    f'x="{_n(x + cell / 2)}" y="{_n(y + cell / 2 + 4)}" text-anchor="middle">'
                    f"{value:.2f}</text>"
                )
    for col in range(n):
        x = left + col * cell + cell / 2
        body.append(
            f'<text x="{_n(x)}" y="{top - 6}" transform="rotate(-50 {_n(x)} {top - 6})">'
            f"{escape(_short(names[col], 20))}</text>"
        )
    return _svg(left + size + 4, top + size + 4, body, "Association matrix")


def missing_bars(missing: list[Missing]) -> str:
    if not missing:
        return ""
    line = 20
    label_width, value_width = 150, 60
    room = 560 - label_width - value_width
    body = []
    for i, m in enumerate(missing):
        y = i * line
        w = room * m.pct / 100
        body.append(
            f'<text x="{label_width - 6}" y="{y + 14}" text-anchor="end">'
            f"{escape(_short(m.name, 22))}</text>"
        )
        body.append(_rect("track", label_width, y + 3, room, line - 6, None, rx=2))
        tip = f"{m.name}: {m.pct:.2f} % missing"
        body.append(_rect("bar", label_width, y + 3, max(w, 1), line - 6, tip, rx=2))
        body.append(
            f'<text class="value" x="{label_width + room + 6}" y="{y + 14}">{m.pct:.1f} %</text>'
        )
    return _svg(560, line * len(missing), body, "Missing values by column")
