"""Chart generation for the research note.

Styling follows a small validated palette (CVD-safe, fixed slot order):
blue #2a78d6 (strategy / slot 1), aqua #1baf7a (slot 2), red #e34948 (slot 6).
Grid and axes are recessive; series are identified by direct labels + legend.
"""

from __future__ import annotations

import os

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

# palette / chrome
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK2 = "#52514e"
MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
BLUE = "#2a78d6"
AQUA = "#1baf7a"
RED = "#e34948"

CHART_DIR = "charts"

plt.rcParams.update(
    {
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "font.family": "sans-serif",
        "text.color": INK,
        "axes.labelcolor": INK2,
        "axes.edgecolor": BASELINE,
        "xtick.color": MUTED,
        "ytick.color": MUTED,
        "axes.grid": True,
        "grid.color": GRID,
        "grid.linewidth": 0.8,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.titlecolor": INK,
        "axes.titlesize": 12,
        "axes.titleweight": "bold",
        "axes.titlelocation": "left",
        "legend.frameon": False,
    }
)


def _save(fig, name: str) -> str:
    os.makedirs(CHART_DIR, exist_ok=True)
    path = os.path.join(CHART_DIR, name)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def cumulative_returns(df: pd.DataFrame) -> str:
    """Growth of $1: gross vs net of transaction costs."""
    cum_gross = (1 + df["strategy_ret"]).cumprod()
    cum_net = (1 + df["strategy_ret_net"]).cumprod()

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(cum_gross.index, cum_gross.values, color=AQUA, lw=2, label="Gross")
    ax.plot(cum_net.index, cum_net.values, color=BLUE, lw=2, label="Net of costs")
    ax.axhline(1.0, color=BASELINE, lw=1, zorder=0)

    # direct labels at line ends (relief rule for the sub-3:1 aqua)
    ax.annotate(f"Gross  {cum_gross.iloc[-1]:.2f}", (cum_gross.index[-1], cum_gross.iloc[-1]),
                xytext=(8, 0), textcoords="offset points", color=INK2, fontsize=9, va="center")
    ax.annotate(f"Net  {cum_net.iloc[-1]:.2f}", (cum_net.index[-1], cum_net.iloc[-1]),
                xytext=(8, 0), textcoords="offset points", color=INK2, fontsize=9, va="center")

    ax.set_title("Volatility-filtered short-term reversal — growth of $1")
    ax.set_ylabel("Growth of $1")
    ax.legend(loc="upper left")
    ax.margins(x=0.02)
    fig.subplots_adjust(right=0.88)
    return _save(fig, "cumulative_returns.png")


def drawdown(dd: pd.Series) -> str:
    fig, ax = plt.subplots(figsize=(10, 3.5))
    ax.fill_between(dd.index, dd.values, 0, color=BLUE, alpha=0.25, lw=0)
    ax.plot(dd.index, dd.values, color=BLUE, lw=1.5)
    ax.axhline(0, color=BASELINE, lw=1)

    trough = dd.idxmin()
    ax.annotate(f"max drawdown {dd.min():.1%}", (trough, dd.min()),
                xytext=(10, -4), textcoords="offset points", color=INK2, fontsize=9)

    ax.set_title("Drawdown (net of costs)")
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    return _save(fig, "drawdown.png")


def ic_series(ic: pd.Series) -> str:
    """Weekly cross-sectional Spearman IC with its mean."""
    ic = ic.dropna()
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.bar(ic.index, ic.values, width=5.0, color=BLUE, alpha=0.55, lw=0)
    ax.axhline(0, color=BASELINE, lw=1)
    ax.axhline(ic.mean(), color=INK2, lw=1.2, ls="--")
    ax.annotate(f"mean IC {ic.mean():+.3f}", (ic.index[-1], ic.mean()),
                xytext=(8, 0), textcoords="offset points", color=INK2, fontsize=9, va="center")

    ax.set_title("Weekly information coefficient (signal vs forward return, Spearman)")
    ax.margins(x=0.02)
    fig.subplots_adjust(right=0.9)
    return _save(fig, "information_coefficient.png")


def long_short_bars(df: pd.DataFrame) -> str:
    """Average weekly return by leg vs the combined book."""
    vals = {
        "Long leg": df["long_ret"].mean(),
        "Short leg": df["short_ret"].mean(),
        "L/S net": df["strategy_ret_net"].mean(),
    }
    colors = [BLUE, AQUA, RED]

    fig, ax = plt.subplots(figsize=(7, 4))
    bars = ax.bar(list(vals), list(vals.values()), color=colors, width=0.55)
    ax.axhline(0, color=BASELINE, lw=1)
    for b, v in zip(bars, vals.values()):
        ax.annotate(f"{v:+.2%}", (b.get_x() + b.get_width() / 2, v),
                    xytext=(0, 6 if v >= 0 else -14), textcoords="offset points",
                    ha="center", color=INK2, fontsize=9)

    ax.set_title("Average weekly return by leg")
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:.2%}")
    ax.grid(axis="x", visible=False)
    return _save(fig, "long_short.png")
