"""Static LLM pricing table and cost computation.

Prices are USD per 1,000 tokens. Cost tracking needs no live provider API keys:
the platform ingests token-usage metadata and prices it locally. Keep this table
versioned and update as providers change pricing.
"""

from __future__ import annotations

from decimal import Decimal

# provider -> model -> (input_per_1k, output_per_1k) in USD.
PRICING: dict[str, dict[str, tuple[str, str]]] = {
    "openai": {
        "gpt-4o": ("0.0025", "0.01"),
        "gpt-4o-mini": ("0.00015", "0.0006"),
        "gpt-4-turbo": ("0.01", "0.03"),
        "gpt-3.5-turbo": ("0.0005", "0.0015"),
        "o1": ("0.015", "0.06"),
        "o1-mini": ("0.0011", "0.0044"),
    },
    "anthropic": {
        "claude-3-5-sonnet": ("0.003", "0.015"),
        "claude-3-5-haiku": ("0.0008", "0.004"),
        "claude-3-opus": ("0.015", "0.075"),
        "claude-3-haiku": ("0.00025", "0.00125"),
    },
    "gemini": {
        "gemini-1.5-pro": ("0.00125", "0.005"),
        "gemini-1.5-flash": ("0.000075", "0.0003"),
        "gemini-2.0-flash": ("0.0001", "0.0004"),
    },
    "deepseek": {
        "deepseek-chat": ("0.00027", "0.0011"),
        "deepseek-reasoner": ("0.00055", "0.00219"),
    },
}

# Used when a model is unknown so cost is never silently zero.
_FALLBACK = (Decimal("0.001"), Decimal("0.002"))

# Heuristic mapping from model-name prefixes to providers when the SDK omits it.
_PROVIDER_HINTS = {
    "gpt": "openai",
    "o1": "openai",
    "claude": "anthropic",
    "gemini": "gemini",
    "deepseek": "deepseek",
}


def infer_provider(model: str | None, provider: str | None = None) -> str:
    if provider:
        return provider.lower()
    name = (model or "").lower()
    for prefix, prov in _PROVIDER_HINTS.items():
        if name.startswith(prefix):
            return prov
    return "unknown"


def _rates(provider: str, model: str | None) -> tuple[Decimal, Decimal]:
    name = (model or "").lower()
    table = PRICING.get(provider, {})
    if name in table:
        inp, out = table[name]
        return Decimal(inp), Decimal(out)
    # Try a prefix match (e.g. "gpt-4o-2024-08-06" -> "gpt-4o").
    for key, (inp, out) in table.items():
        if name.startswith(key):
            return Decimal(inp), Decimal(out)
    return _FALLBACK


def compute_cost(
    provider: str | None,
    model: str | None,
    input_tokens: int,
    output_tokens: int,
) -> Decimal:
    """Return the USD cost for a single priced call, quantized to 6 decimals."""
    prov = infer_provider(model, provider)
    in_rate, out_rate = _rates(prov, model)
    cost = (Decimal(input_tokens) / 1000) * in_rate + (Decimal(output_tokens) / 1000) * out_rate
    return cost.quantize(Decimal("0.000001"))
