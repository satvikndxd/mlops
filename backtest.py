"""Weekly long/short reversal backtest with turnover-based transaction costs.

Methodology
-----------
- Rebalance on the last trading day of each week.
- On each rebalance date t, using only data up to and including t:
    * past 5-day return r5, trailing 21-day volatility vol21
    * drop the top 20% most volatile names
    * signal = -r5; long the top decile, short the bottom decile (equal weight,
      0.5 gross per side -> ~1x gross, dollar-neutral)
- Hold until the next rebalance date (~5 trading days). Holding periods tile
  the sample exactly, so weekly returns are non-overlapping.
- Costs: 5 bps per side, charged on actual traded notional
  cost_t = sum_i |w_{i,t} - w_{i,t-1}| * 5 bps
  (first week trades the full 1x gross book -> ~5 bps).
- IC: Spearman rank correlation between the signal and realized forward
  returns on the filtered universe, each week.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from signals import past_return, realized_vol, reversal_signal

COST_PER_SIDE = 0.0005  # 5 bps
VOL_CUT = 0.80          # drop top 20% most volatile
TOP_PCT = 0.10          # decile long/short
MIN_HISTORY = 60        # trading days of history before trading
MIN_NAMES = 100         # minimum cross-section size


def rebalance_dates(px: pd.DataFrame) -> pd.DatetimeIndex:
    """Last trading day of each calendar week present in the price index."""
    idx = px.index.to_series()
    return pd.DatetimeIndex(idx.groupby(idx.dt.to_period("W")).max().values)


def run_backtest(px: pd.DataFrame) -> pd.DataFrame:
    r5_all = past_return(px, 5)
    vol_all = realized_vol(px, 21)
    dates = rebalance_dates(px)

    prev_weights = pd.Series(dtype=float)
    rows = []

    for t, t_next in zip(dates[:-1], dates[1:]):
        # information set: data up to and including t only
        if px.index.get_loc(t) < MIN_HISTORY:
            continue

        signal = reversal_signal(
            r5_all.loc[t], vol_all.loc[t], vol_cut=VOL_CUT, min_names=MIN_NAMES
        )
        if signal is None:
            continue

        n_side = max(int(TOP_PCT * len(signal)), 1)
        longs = signal.nlargest(n_side).index
        shorts = signal.nsmallest(n_side).index

        # equal-weight, dollar-neutral, ~1x gross
        weights = pd.Series(0.0, index=signal.index)
        weights[longs] = 0.5 / n_side
        weights[shorts] = -0.5 / n_side

        # realized forward return over the holding period (t -> next rebalance)
        fwd = px.loc[t_next] / px.loc[t] - 1
        long_ret = fwd[longs].mean()
        short_ret = fwd[shorts].mean()
        gross_ret = 0.5 * (long_ret - short_ret)

        # turnover-based cost on traded notional
        combined = weights.reindex(weights.index.union(prev_weights.index), fill_value=0.0)
        prev = prev_weights.reindex(combined.index, fill_value=0.0)
        traded_notional = (combined - prev).abs().sum()
        cost = traded_notional * COST_PER_SIDE
        prev_weights = weights

        # weekly cross-sectional IC on the filtered universe
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
