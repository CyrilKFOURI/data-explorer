"""What a conversation costs (R-AG-B2), from the usage each response reports."""

from dataclasses import dataclass

from app.modules.agent.engine.provider import Usage


@dataclass(frozen=True)
class Price:
    """US dollars per million tokens."""

    input: float
    output: float
    cache_read: float

    @property
    def cache_write(self) -> float:  # 5-minute cache writes cost 1.25 × the input price
        return self.input * 1.25


# Anthropic first-party prices (2026-10).
PRICES: dict[str, Price] = {
    "claude-opus-5-5": Price(4.00, 20.00, 0.20),
    "claude-sonnet-5-5": Price(2.00, 10.00, 0.20),
    "claude-haiku-5-5": Price(0.10, 0.50, 0.01),
}
UNKNOWN = Price(4.00, 20.00, 0.40)  # an unlisted model is counted at the default model's price


def cost(usage: Usage) -> float:
    price = PRICES.get(usage.model, UNKNOWN)
    return (
        usage.input_tokens * price.input
        + usage.output_tokens * price.output
        + usage.cache_read_tokens * price.cache_read
        + usage.cache_write_tokens * price.cache_write
    ) / 1_000_000


@dataclass
class Budget:
    limit_usd: float
    spent_usd: float = 0.0

    def add(self, usage: Usage) -> float:
        spent = cost(usage)
        self.spent_usd += spent
        return spent

    @property
    def exceeded(self) -> bool:
        return self.spent_usd >= self.limit_usd
