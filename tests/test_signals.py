import numpy as np
import pandas as pd
import pytest

from signals import (
    SIGNALS,
    compute_signal,
    filter_cross_section,
    low_vol,
    momentum,
    realized_vol,
    reversal,
)


@pytest.fixture
def px():
    """30 days, 4 stocks: A rallies, B sells off, C flat, D flat-but-noisy."""
    dates = pd.bdate_range("2024-01-01", periods=30)
    n = len(dates)
    a = np.linspace(100, 130, n)          # steady winner
    b = np.linspace(100, 80, n)           # steady loser
    c = np.full(n, 100.0)                 # flat
    d = 100 + 15 * np.sign(np.sin(np.arange(n)))  # violent oscillation
    return pd.DataFrame({"A": a, "B": b, "C": c, "D": d}, index=dates)


def test_registry_contains_all_signals():
    assert {"reversal", "momentum", "low_vol"} <= set(SIGNALS)


def test_reversal_prefers_recent_losers(px):
    sig = reversal(px, lookback=5).iloc[-1]
    assert sig["B"] > sig["C"] > sig["A"]  # loser scores highest, winner lowest


def test_momentum_prefers_past_winners_and_skips_recent_window(px):
    sig = momentum(px, lookback=20, skip=5).iloc[-1]
    assert sig["A"] > sig["C"] > sig["B"]
    # skip window: signal uses P[t-skip]/P[t-lookback], not the latest price
    expected_a = px["A"].iloc[-6] / px["A"].iloc[-21] - 1
    assert sig["A"] == pytest.approx(expected_a)


def test_low_vol_prefers_quiet_names(px):
    sig = low_vol(px, window=20).iloc[-1]
    assert sig["C"] > sig["D"]  # flat stock scores above noisy stock


def test_compute_signal_dispatches_from_config(px):
    out = compute_signal(px, {"type": "reversal", "params": {"lookback": 5}})
    pd.testing.assert_frame_equal(out, reversal(px, lookback=5))


def test_vol_filter_removes_most_volatile_names(px):
    sig = reversal(px, 5).iloc[-1]
    vol = realized_vol(px, 20).iloc[-1]
    kept = filter_cross_section(sig, vol, vol_cut=0.70, min_names=2)
    assert "D" not in kept.index          # noisiest name filtered out
    assert {"A", "B", "C"} <= set(kept.index)


def test_filter_returns_none_below_min_names(px):
    sig = reversal(px, 5).iloc[-1]
    vol = realized_vol(px, 20).iloc[-1]
    assert filter_cross_section(sig, vol, min_names=100) is None


def test_filter_without_vol_screen_keeps_all_valid(px):
    sig = reversal(px, 5).iloc[-1]
    kept = filter_cross_section(sig, None, min_names=2)
    assert set(kept.index) == {"A", "B", "C", "D"}
