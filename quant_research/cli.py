"""Command-line entry point.

    quant-backtest                                  # primary study (reversal)
    quant-backtest --config configs/momentum.yaml   # one factor
    quant-backtest --all                            # every config + comparison

Outputs per factor: results/<name>/{report.md, dashboard.png, weekly.csv}.
With --all: results/comparison.md. The primary factor also gets standalone
README charts in charts/.
"""

from __future__ import annotations

import argparse
import glob
import os

import pandas as pd

from . import plots
from .data import download_benchmark, download_prices, get_sp500_tickers
from .engine import benchmark_weekly, load_config, run_backtest
from .metrics import annualized_return, drawdown_series
from .report import analyze, write_report

START = "2019-01-01"
RESULTS_DIR = "results"
PRIMARY = "reversal"  # gets the standalone README charts
SUBPERIODS = [("2019", "2021"), ("2022", "2024"), ("2025", "2026")]


def run_factor(cfg: dict, px: pd.DataFrame, spy: pd.Series) -> dict:
    name = cfg["name"]
    print(f"== {name} ==")
    df = run_backtest(px, cfg)
    print(f"   {len(df)} weekly periods, {df.index[0]:%Y-%m-%d} -> {df.index[-1]:%Y-%m-%d}")

    spy_ret = benchmark_weekly(spy, df)
    stats = analyze(df, spy_ret, SUBPERIODS)

    out_dir = os.path.join(RESULTS_DIR, name)
    os.makedirs(out_dir, exist_ok=True)
    df.to_csv(os.path.join(out_dir, "weekly.csv"))

    artifacts = [
        plots.dashboard(df, spy_ret, name, out_dir=out_dir),
        write_report(cfg, df, stats, out_dir),
    ]
    if name == PRIMARY:
        artifacts += [
            plots.cumulative_returns(df),
            plots.drawdown(drawdown_series(df["strategy_ret_net"])),
            plots.ic_series(df["ic"]),
            plots.long_short_bars(df),
        ]
    for path in artifacts:
        print(f"   wrote {path}")

    table, ic, capm = stats["table"], stats["ic"], stats["capm"]
    return {
        "Factor": name,
        "Net ann.": annualized_return(df["strategy_ret_net"]),
        "Net Sharpe": table.loc["Net of costs", "Sharpe"],
        "Max DD": table.loc["Net of costs", "Max drawdown"],
        "Mean IC": ic["mean_ic"],
        "IC t-stat": ic["ic_tstat"],
        "Alpha (ann.)": capm["alpha_annualized"],
        "Alpha p": capm["alpha_pvalue"],
        "Beta": capm["beta"],
        "Turnover/wk": float(df["turnover"].mean()),
    }


def write_comparison(rows: list[dict]) -> None:
    cmp = pd.DataFrame(rows).set_index("Factor")
    fmt = cmp.copy()
    for col in ["Net ann.", "Max DD", "Alpha (ann.)"]:
        fmt[col] = fmt[col].map("{:.2%}".format)
    for col in ["Net Sharpe", "IC t-stat", "Beta", "Turnover/wk"]:
        fmt[col] = fmt[col].map("{:.2f}".format)
    fmt["Mean IC"] = fmt["Mean IC"].map("{:+.3f}".format)
    fmt["Alpha p"] = fmt["Alpha p"].map("{:.3f}".format)

    path = os.path.join(RESULTS_DIR, "comparison.md")
    with open(path, "w") as f:
        f.write(
            "# Factor comparison (net of costs, weekly rebalance, identical engine)\n\n"
            + fmt.to_markdown()
            + "\n"
        )
    print(f"\nwrote {path}\n")
    print(fmt.to_string())


def main() -> None:
    parser = argparse.ArgumentParser(prog="quant-backtest", description="Run factor backtests")
    parser.add_argument("--config", default="configs/reversal.yaml")
    parser.add_argument("--all", action="store_true", help="run every config in configs/")
    args = parser.parse_args()

    paths = sorted(glob.glob("configs/*.yaml")) if args.all else [args.config]

    print("Loading universe & data ...")
    tickers = get_sp500_tickers()
    px = download_prices(tickers, start=START)
    spy = download_benchmark(start=START)

    rows = [run_factor(load_config(p), px, spy) for p in paths]

    if len(rows) > 1:
        write_comparison(rows)


if __name__ == "__main__":
    main()
