import numpy as np
import pandas as pd
import pytest

from backtest import benchmark_weekly, compute_turnover, run_backtest


def w(**kwargs):
    return pd.Series(kwargs, dtype=float)


def test_first_rebalance_trades_full_gross():
    # from cash into a 1x-gross dollar-neutral book -> traded notional = 1.0
    weights = w(A=0.25, B=0.25, C=-0.25, D=-0.25)
    assert compute_turnover(pd.Series(dtype=float), weights) == pytest.approx(1.0)


def test_identical_book_has_zero_turnover():
    weights = w(A=0.5, B=-0.5)
    assert compute_turnover(weights, weights) == 0.0


def test_full_replacement_trades_twice_gross():
    old = w(A=0.5, B=-0.5)
    new = w(C=0.5, D=-0.5)
    # sell A, cover B, buy C, short D -> 2.0x traded
    assert compute_turnover(old, new) == pytest.approx(2.0)


def test_flipping_a_position_counts_both_legs():
    old = w(A=0.5, B=-0.5)
    new = w(A=-0.5, B=0.5)
    assert compute_turnover(old, new) == pytest.approx(2.0)


@pytest.fixture
def synthetic_market():
    """200 trading days, 120 stocks with mild idiosyncratic noise."""
    rng = np.random.default_rng(7)
    dates = pd.bdate_range("2023-01-02", periods=200)
    n = 120
    rets = rng.normal(0.0002, 0.015, size=(len(dates), n))
    px = pd.DataFrame(
        100 * np.exp(np.cumsum(rets, axis=0)),
        index=dates,
        columns=[f"S{i:03d}" for i in range(n)],
    )
    return px


CFG = {
    "name": "test",
    "signal": {"type": "reversal", "params": {"lookback": 5}},
    "filter": {"vol_window": 21, "vol_cut": 0.80},
    "portfolio": {"top_pct": 0.10, "gross_per_side": 0.5},
    "costs": {"bps_per_side": 5},
    "universe": {"min_history": 60, "min_names": 50},
}


def test_engine_costs_equal_turnover_times_fee(synthetic_market):
    df = run_backtest(synthetic_market, CFG)
    assert len(df) > 10
    expected = df["turnover"] * 5 / 1e4
    pd.testing.assert_series_equal(df["cost"], expected, check_names=False)
    # net = gross - cost, always
    pd.testing.assert_series_equal(
        df["strategy_ret_net"], df["strategy_ret"] - df["cost"], check_names=False
    )


def test_engine_first_week_cost_is_about_5bps(synthetic_market):
    df = run_backtest(synthetic_market, CFG)
    assert df["turnover"].iloc[0] == pytest.approx(1.0)
    assert df["cost"].iloc[0] == pytest.approx(0.0005)


def test_engine_is_dollar_neutral(synthetic_market):
    df = run_backtest(synthetic_market, CFG)
    assert (df["n_long"] == df["n_short"]).all()


def test_zero_cost_config_makes_net_equal_gross(synthetic_market):
    cfg = {**CFG, "costs": {"bps_per_side": 0}}
    df = run_backtest(synthetic_market, cfg)
    pd.testing.assert_series_equal(
        df["strategy_ret_net"], df["strategy_ret"], check_names=False
    )


def test_benchmark_uses_same_holding_windows(synthetic_market):
    df = run_backtest(synthetic_market, CFG)
    spy = synthetic_market.iloc[:, 0].rename("SPY")  # any price series works
    bench = benchmark_weekly(spy, df)
    t0, t1 = df["period_start"].iloc[0], df.index[0]
    assert bench.iloc[0] == pytest.approx(spy.loc[t1] / spy.loc[t0] - 1)
