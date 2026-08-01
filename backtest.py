"""Config-driven weekly long/short backtest engine.

Any registered signal (signals.SIGNALS) runs through the same engine:

- Rebalance on the last trading day of each week, using only information
  available up to and including that day.
- Optional realized-volatility screen (drop the most volatile quantile).
- Long the top `top_pct` of the signal, short the bottom `top_pct`,
  equal-weighted, `gross_per_side` per side (default 0.5 -> ~1x gross,
  dollar-neutral).
- Hold until the next rebalance date (~5 trading days); holding periods
  tile the sample exactly, so weekly returns are non-overlapping.
- Costs charged on actual traded notional: cost_t = sum_i |dw_i| * bps.
- Weekly cross-sectional Spearman IC of the signal vs realized forward
  returns on the filtered universe.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import yaml
from scipy.stats import spearmanr

from signals import compute_signal, filter_cross_section, realized_vol

DEFAULTS = {
    "filter": {"vol_window": 21, "vol_cut": 0.80},
    "portfolio": {"top_pct": 0.10, "gross_per_side": 0.5},
    "costs": {"bps_per_side": 5},
    "universe": {"min_history": 60, "min_names": 100},
}


def load_config(path: str) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def compute_turnover(prev_weights: pd.Series, weights: pd.Series) -> float:
    """Total traded notional (in units of NAV) between two weight vectors."""
    idx = weights.index.union(prev_weights.index)
    new = weights.reindex(idx, fill_value=0.0)
    old = prev_weights.reindex(idx, fill_value=0.0)
    return float((new - old).abs().sum())


def rebalance_dates(px: pd.DataFrame) -> pd.DatetimeIndex:
    """Last trading day of each calendar week present in the price index."""
    idx = px.index.to_series()
    return pd.DatetimeIndex(idx.groupby(idx.dt.to_period("W")).max().values)


def run_backtest(px: pd.DataFrame, cfg: dict) -> pd.DataFrame:
    filt_cfg = cfg.get("filter", DEFAULTS["filter"])
    port_cfg = {**DEFAULTS["portfolio"], **cfg.get("portfolio", {})}
    cost_cfg = {**DEFAULTS["costs"], **cfg.get("costs", {})}
    uni_cfg = {**DEFAULTS["universe"], **cfg.get("universe", {})}

    cost_per_side = cost_cfg["bps_per_side"] / 1e4
    top_pct = port_cfg["top_pct"]
    gross_side = port_cfg["gross_per_side"]

    sig_panel = compute_signal(px, cfg["signal"])
    vol_panel = (
        realized_vol(px, filt_cfg["vol_window"]) if filt_cfg is not None else None
    )
    dates = rebalance_dates(px)

    prev_weights = pd.Series(dtype=float)
    rows = []

    for t, t_next in zip(dates[:-1], dates[1:]):
        if px.index.get_loc(t) < uni_cfg["min_history"]:
            continue

        signal = filter_cross_section(
            sig_panel.loc[t],
            vol_panel.loc[t] if vol_panel is not None else None,
            vol_cut=filt_cfg["vol_cut"] if filt_cfg else 0.80,
            min_names=uni_cfg["min_names"],
        )
        if signal is None:
            continue

        n_side = max(int(top_pct * len(signal)), 1)
        longs = signal.nlargest(n_side).index
        shorts = signal.nsmallest(n_side).index

        weights = pd.Series(0.0, index=signal.index)
        weights[longs] = gross_side / n_side
        weights[shorts] = -gross_side / n_side

        # realized forward return over the holding period (t -> next rebalance)
        fwd = px.loc[t_next] / px.loc[t] - 1
        long_ret = fwd[longs].mean()
        short_ret = fwd[shorts].mean()
        gross_ret = gross_side * (long_ret - short_ret)

        traded_notional = compute_turnover(prev_weights, weights)
        cost = traded_notional * cost_per_side
        prev_weights = weights

        fwd_universe = fwd[signal.index]
        mask = fwd_universe.notna()
        ic = spearmanr(signal[mask], fwd_universe[mask])[0] if mask.sum() > 10 else np.nan

        rows.append(
            {
                "date": t_next,  # return is realized at the end of the period
                "period_start": t,
                "long_ret": long_ret,
                "short_ret": short_ret,
                "strategy_ret": gross_ret,
                "turnover": traded_notional,
                "cost": cost,
                "strategy_ret_net": gross_ret - cost,
                "ic": ic,
                "n_long": len(longs),
                "n_short": len(shorts),
                "universe_size": len(signal),
            }
        )

    return pd.DataFrame(rows).set_index("date")


def benchmark_weekly(spy: pd.Series, strat: pd.DataFrame) -> pd.Series:
    """SPY returns over the exact same holding windows as the strategy."""
    spy = spy.sort_index().ffill()
    start = spy.reindex(pd.DatetimeIndex(strat["period_start"]), method="ffill")
    end = spy.reindex(strat.index, method="ffill")
    ret = end.values / start.values - 1
    return pd.Series(ret, index=strat.index, name="spy_ret")
