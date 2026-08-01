"""Signal construction: short-term reversal with a realized-volatility screen."""

from __future__ import annotations

import pandas as pd


def past_return(px: pd.DataFrame, lookback: int = 5) -> pd.DataFrame:
    """Trailing `lookback`-day simple return for every stock, every day."""
    return px / px.shift(lookback) - 1


def realized_vol(px: pd.DataFrame, window: int = 21) -> pd.DataFrame:
    """Trailing `window`-day standard deviation of daily returns."""
    rets = px.pct_change()
    return rets.rolling(window).std()


def reversal_signal(
    r5: pd.Series,
    vol21: pd.Series,
    vol_cut: float = 0.80,
    min_names: int = 100,
) -> pd.Series | None:
    """Cross-sectional reversal signal on one rebalance date.

    signal = -past 5-day return, computed only on stocks whose trailing
    21-day volatility is at or below the `vol_cut` cross-sectional quantile
    (i.e. the top (1 - vol_cut) most volatile names are excluded).

    Returns None if fewer than `min_names` stocks have valid data.
    """
    valid = r5.dropna().index.intersection(vol21.dropna().index)
    if len(valid) < min_names:
        return None

    r5, vol21 = r5[valid], vol21[valid]
    keep = vol21 <= vol21.quantile(vol_cut)
    return -r5[keep]
