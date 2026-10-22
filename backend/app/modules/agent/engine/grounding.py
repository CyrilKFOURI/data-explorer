"""Does every figure of an answer come from the analyses? (spec 026, R-AG-G1)

Deterministic, no model call: each number written in the answer is looked for among the numbers of
the sources (tool results, the dataset schema, the notes, the user's words). A number is found when
a source rounds to it at the precision written, or a share does once multiplied by 100
(0.742 -> 74.2 %). Signs are ignored ("d = 0.55" for -0.547). Numbers that carry no claim are
skipped: small integers (list items, "2 next steps"), usual thresholds, years, and digits stuck to
letters ("3rd", "Q3", "x_17")."""

import math
import re
from bisect import bisect_left
from dataclasses import dataclass, field

# "3.71 × 10⁻⁵⁹", "3.71 x 10^-59": the power of ten is dropped, the mantissa is compared.
POWER = re.compile(r"\s*[×x*]\s*10\s*(?:\^|\*\*)?\s*[-−⁻]?[\d⁰¹²³⁴⁵⁶⁷⁸⁹]+")
NUMBER = re.compile(
    r"(?<![\w.,])[-−]?(?P<int>\d{1,3}(?:,\d{3})+|\d+)(?P<dec>\.\d+)?(?P<exp>[eE][-+]?\d+)?(?![\w])"
)
SOURCE_NUMBER = re.compile(r"-?\d+(?:\.\d+)?(?:[eE][-+]?\d+)?")
IGNORED = {0.05, 0.01, 0.001, 0.1, 95.0, 99.0, 90.0, 100.0}
MAX_REPORTED = 10


@dataclass
class Grounding:
    checked: int = 0
    unverified: list[str] = field(default_factory=list)  # as written in the answer


def check(answer: str, sources: list[str]) -> Grounding:
    known = _Known(sources)
    found = Grounding()
    for match in NUMBER.finditer(POWER.sub(" ", answer)):
        written = match.group(0).lstrip("-−")
        value, decimals = _value(match)
        if _ignored(value, decimals):
            continue
        found.checked += 1
        if not known.has(value, decimals) and written not in found.unverified:
            found.unverified.append(written)
    found.unverified = found.unverified[:MAX_REPORTED]
    return found


def _value(match: re.Match[str]) -> tuple[float, int]:
    decimals = len(match.group("dec") or ".") - 1
    value = float(match.group("int").replace(",", "") + (match.group("dec") or ""))
    return value, decimals  # an exponent written by the model is compared as a mantissa


def _ignored(value: float, decimals: int) -> bool:
    if decimals == 0 and (value <= 10 or 1900 <= value <= 2100):
        return True
    return value in IGNORED


class _Known:
    """The sources' numbers (absolute values), with shares as percentages and the mantissas of
    very small or large numbers, sorted for a quick nearest look-up."""

    def __init__(self, sources: list[str]) -> None:
        values: set[float] = set()
        for text in sources:
            for raw in SOURCE_NUMBER.findall(text):
                number = abs(float(raw))
                if not math.isfinite(number):
                    continue
                values.add(number)
                if number <= 1:
                    values.add(number * 100)
                if number and (number < 1e-3 or number >= 1e6):
                    values.add(number / 10 ** math.floor(math.log10(number)))
        self.values = sorted(values)

    def has(self, value: float, decimals: int) -> bool:
        tolerance = 0.5 * 10**-decimals + 1e-9
        i = bisect_left(self.values, value - tolerance)
        return i < len(self.values) and self.values[i] <= value + tolerance
