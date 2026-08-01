"""Signal library and cross-sectional filtering.

Each signal is a function (px, **params) -> DataFrame of scores
(dates x tickers), registered by name so the backtest engine can be
driven entirely from a YAML config. Higher score = more attractive
(candidate for the long leg).
"""

from __future__ import annotations

from typing import Callable

import pandas as pd

SIGNALS: dict[str, Callable] = {}


def register(name: str):
    def wrap(fn):
        SIGNALS[name] = fn
        return fn

    return wrap


@register("reversal")
def reversal(px: pd.DataFrame, lookback: int = 5) -> pd.DataFrame:
    """Short-term reversal: buy recent losers, sell recent winners."""
    return -(px / px.shift(lookback) - 1)


@register("momentum")
def momentum(px: pd.DataFrame, lookback: int = 126, skip: int = 21) -> pd.DataFrame:
    """Intermediate momentum (e.g. 6-1): past `lookback`-day return,
    skipping the most recent `skip` days to avoid reversal contamination."""
    return px.shift(skip) / px.shift(lookback) - 1


@register("low_vol")
def low_vol(px: pd.DataFrame, window: int = 63) -> pd.DataFrame:
    """Low-volatility: long the least volatile names, short the most volatile."""
    return -px.pct_change().rolling(window).std()


def compute_signal(px: pd.DataFrame, signal_cfg: dict) -> pd.DataFrame:
    """Build the full signal panel from a config block {type, params}."""
    fn = SIGNALS[signal_cfg["type"]]
    return fn(px, **signal_cfg.get("params", {}))


def realized_vol(px: pd.DataFrame, window: int = 21) -> pd.DataFrame:
    """Trailing `window`-day standard deviation of daily returns."""
    return px.pct_change().rolling(window).std()


def filter_cross_section(
    signal: pd.Series,
    vol: pd.Series | None,
    vol_cut: float = 0.80,
    min_names: int = 100,
) -> pd.Series | None:
    """One rebalance date's cross-section.

    Keeps stocks with valid signal (and, if `vol` is given, drops names above
    the `vol_cut` cross-sectional volatility quantile). Returns None if fewer
    than `min_names` remain before filtering.
    """
    signal = signal.dropna()
    if vol is not None:
        valid = signal.index.intersection(vol.dropna().index)
        if len(valid) < min_names:
            return None
        signal, vol = signal[valid], vol[valid]
        signal = signal[vol <= vol.quantile(vol_cut)]
        return signal
    return signal if len(signal) >= min_names else None
