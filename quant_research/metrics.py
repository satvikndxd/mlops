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


def bootstrap_ci(
    series: pd.Series,
    n_boot: int = 2000,
    seed: int = 42,
    ppy: int = PERIODS_PER_YEAR,
    ci: float = 0.95,
) -> dict:
    """IID bootstrap 95% confidence intervals for annualized return and Sharpe.

    Resamples weekly returns with replacement; a fixed seed keeps the study
    reproducible. (An IID bootstrap understates uncertainty if returns are
    autocorrelated — acceptable here given weekly, non-overlapping periods.)
    """
    x = series.dropna().to_numpy()
    rng = np.random.default_rng(seed)
    idx = rng.integers(0, len(x), size=(n_boot, len(x)))
    samples = x[idx]

    ann_ret = (1 + samples).prod(axis=1) ** (ppy / len(x)) - 1
    mu, sd = samples.mean(axis=1), samples.std(axis=1, ddof=1)
    sharpe = np.where(sd > 0, mu / sd * np.sqrt(ppy), np.nan)

    lo, hi = (1 - ci) / 2 * 100, (1 + ci) / 2 * 100
    return {
        "ann_return_ci": tuple(np.percentile(ann_ret, [lo, hi])),
        "sharpe_ci": tuple(np.nanpercentile(sharpe, [lo, hi])),
        "n_boot": n_boot,
    }


def rolling_sharpe(series: pd.Series, window: int = 52, ppy: int = PERIODS_PER_YEAR) -> pd.Series:
    mu = series.rolling(window).mean()
    sd = series.rolling(window).std()
    return (mu / sd) * np.sqrt(ppy)


def rolling_beta(strategy: pd.Series, market: pd.Series, window: int = 52) -> pd.Series:
    cov = strategy.rolling(window).cov(market)
    var = market.rolling(window).var()
    return cov / var


def subperiod_table(df: pd.DataFrame, periods: list[tuple[str, str]]) -> pd.DataFrame:
    """Per-sub-period performance: did the effect survive across regimes?"""
    rows = {}
    for start, end in periods:
        sub = df.loc[start:end]
        if len(sub) < 10:
            continue
        rows[f"{start}–{end}"] = {
            "Weeks": len(sub),
            "Gross ann.": annualized_return(sub["strategy_ret"]),
            "Net ann.": annualized_return(sub["strategy_ret_net"]),
            "Net Sharpe": sharpe_ratio(sub["strategy_ret_net"]),
            "Mean IC": float(sub["ic"].mean()),
        }
    return pd.DataFrame(rows).T


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
