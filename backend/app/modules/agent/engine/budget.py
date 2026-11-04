"""What a conversation costs (R-AG-B2), from the usage each response reports.

Prices are known for Claude only; they are never guessed for other vendors' models. For those,
the budget is a number of tokens instead, and the panel shows tokens rather than dollars."""

from dataclasses import dataclass

from app.modules.agent.engine.provider import Usage

TOKEN_LIMIT = 2_000_000  # per conversation, when the model's price is unknown


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


def cost(usage: Usage) -> float | None:
    """US dollars, or None when the model's price is unknown."""
    price = PRICES.get(usage.model)
    if price is None:
        return None
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
    tokens: int = 0
    token_limit: int = TOKEN_LIMIT
    priced: bool = True  # False once a response came from a model without a known price

    def add(self, usage: Usage) -> float:
        """Counts a response; returns its cost in dollars (0 when unknown)."""
        self.tokens += usage.total
        spent = cost(usage)
        if spent is None:
            self.priced = False
            return 0.0
        self.spent_usd += spent
        return spent

    @property
    def exceeded(self) -> bool:
        return self.spent_usd >= self.limit_usd or self.tokens >= self.token_limit
