"""Performance and signal-quality metrics."""

from __future__ import annotations

import numpy as np
import pandas as pd

PERIODS_PER_YEAR = 52  # weekly rebalance


def annualized_return(series: pd.Series, ppy: int = PERIODS_PER_YEAR) -> float:
    series = series.dropna()
    return float((1 + series).prod() ** (ppy / len(series)) - 1)


def annualized_vol(series: pd.Series, ppy: int = PERIODS_PER_YEAR) -> float:
    return float(series.dropna().std() * np.sqrt(ppy))


def sharpe_ratio(series: pd.Series, ppy: int = PERIODS_PER_YEAR) -> float:
    vol = annualized_vol(series, ppy)
    return float("nan") if vol == 0 else annualized_return(series, ppy) / vol


def max_drawdown(series: pd.Series) -> float:
    cum = (1 + series.dropna()).cumprod()
    return float((cum / cum.cummax() - 1).min())


def drawdown_series(series: pd.Series) -> pd.Series:
    cum = (1 + series.dropna()).cumprod()
    return cum / cum.cummax() - 1


def hit_rate(series: pd.Series) -> float:
    series = series.dropna()
    return float((series > 0).mean())


def ic_stats(ic: pd.Series) -> dict:
    """Mean IC, IC volatility, ICIR, and t-stat of the mean IC."""
    ic = ic.dropna()
    mean, std = ic.mean(), ic.std()
    return {
        "mean_ic": float(mean),
        "ic_std": float(std),
        "icir": float(mean / std) if std > 0 else float("nan"),
        "ic_tstat": float(mean / std * np.sqrt(len(ic))) if std > 0 else float("nan"),
        "pct_positive": float((ic > 0).mean()),
        "n_periods": int(len(ic)),
    }


def summary_table(gross: pd.Series, net: pd.Series) -> pd.DataFrame:
    rows = {}
    for name, s in [("Gross", gross), ("Net of costs", net)]:
        rows[name] = {
            "Ann. return": annualized_return(s),
            "Ann. vol": annualized_vol(s),
            "Sharpe": sharpe_ratio(s),
            "Max drawdown": max_drawdown(s),
            "Hit rate": hit_rate(s),
        }
    return pd.DataFrame(rows).T
