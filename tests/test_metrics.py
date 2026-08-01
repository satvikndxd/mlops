import numpy as np
import pandas as pd
import pytest

from metrics import (
    annualized_return,
    annualized_vol,
    bootstrap_ci,
    hit_rate,
    ic_stats,
    max_drawdown,
    rolling_beta,
    sharpe_ratio,
    subperiod_table,
)


def test_annualized_return_compounds_weekly():
    # 1% per week for 52 weeks -> (1.01)^52 - 1
    s = pd.Series([0.01] * 52)
    assert annualized_return(s) == pytest.approx(1.01**52 - 1)


def test_annualized_vol_scales_by_sqrt_periods():
    s = pd.Series([0.01, -0.01] * 50)
    assert annualized_vol(s) == pytest.approx(s.std() * np.sqrt(52))


def test_sharpe_sign_matches_return_sign():
    up = pd.Series([0.01, 0.02, 0.005] * 20)
    down = -up
    assert sharpe_ratio(up) > 0 > sharpe_ratio(down)


def test_max_drawdown_known_path():
    # 100 -> 120 -> 90: drawdown = 90/120 - 1 = -25%
    rets = pd.Series([0.20, -0.25])
    assert max_drawdown(rets) == pytest.approx(-0.25)


def test_hit_rate():
    s = pd.Series([0.01, -0.01, 0.02, 0.03])
    assert hit_rate(s) == pytest.approx(0.75)


def test_ic_stats_of_constant_positive_ic():
    ic = pd.Series([0.05, 0.03, 0.04, 0.06, 0.02])
    out = ic_stats(ic)
    assert out["mean_ic"] == pytest.approx(0.04)
    assert out["pct_positive"] == 1.0
    assert out["icir"] > 0


def test_bootstrap_ci_brackets_point_estimate_and_is_reproducible():
    rng = np.random.default_rng(0)
    s = pd.Series(rng.normal(0.002, 0.01, 300))
    a = bootstrap_ci(s, n_boot=500)
    b = bootstrap_ci(s, n_boot=500)
    assert a == b  # fixed seed -> reproducible
    lo, hi = a["ann_return_ci"]
    assert lo < annualized_return(s) < hi


def test_rolling_beta_recovers_true_beta():
    rng = np.random.default_rng(1)
    mkt = pd.Series(rng.normal(0, 0.02, 200))
    strat = 0.5 * mkt + rng.normal(0, 0.001, 200)
    beta = rolling_beta(strat, mkt, window=52).dropna()
    assert beta.iloc[-1] == pytest.approx(0.5, abs=0.05)


def test_subperiod_table_splits_sample():
    idx = pd.date_range("2019-01-04", periods=200, freq="W-FRI")
    df = pd.DataFrame(
        {
            "strategy_ret": 0.001,
            "strategy_ret_net": 0.0005,
            "ic": 0.02,
        },
        index=idx,
    )
    out = subperiod_table(df, [("2019", "2020"), ("2021", "2022")])
    assert len(out) == 2
    assert out["Weeks"].sum() == 200
