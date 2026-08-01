"""End-to-end runner: data -> signals -> backtest -> costs -> risk -> charts.

Usage:  python run_backtest.py
Outputs: charts/*.png, results/weekly_returns.csv, results/summary.md
"""

from __future__ import annotations

import os

import pandas as pd
import statsmodels.api as sm

import plots
from backtest import COST_PER_SIDE, run_backtest, benchmark_weekly
from data import download_benchmark, download_prices, get_sp500_tickers
from metrics import (
    PERIODS_PER_YEAR,
    annualized_return,
    drawdown_series,
    ic_stats,
    summary_table,
)

START = "2019-01-01"
RESULTS_DIR = "results"


def capm_regression(strat_net: pd.Series, spy_ret: pd.Series):
    merged = pd.concat([strat_net.rename("strategy"), spy_ret], axis=1).dropna()
    X = sm.add_constant(merged["spy_ret"])
    model = sm.OLS(merged["strategy"], X).fit()
    alpha_weekly = model.params["const"]
    return {
        "alpha_weekly": float(alpha_weekly),
        "alpha_annualized": float((1 + alpha_weekly) ** PERIODS_PER_YEAR - 1),
        "alpha_tstat": float(model.tvalues["const"]),
        "alpha_pvalue": float(model.pvalues["const"]),
        "beta": float(model.params["spy_ret"]),
        "beta_tstat": float(model.tvalues["spy_ret"]),
        "r_squared": float(model.rsquared),
        "n_obs": int(model.nobs),
    }, model


def main() -> None:
    print("1/5 Universe & data ...")
    tickers = get_sp500_tickers()
    print(f"    {len(tickers)} current S&P 500 tickers")
    px = download_prices(tickers, start=START)
    spy = download_benchmark(start=START)

    print("2/5 Backtest ...")
    df = run_backtest(px)
    print(f"    {len(df)} weekly periods, {df.index[0]:%Y-%m-%d} -> {df.index[-1]:%Y-%m-%d}")

    print("3/5 Metrics ...")
    table = summary_table(df["strategy_ret"], df["strategy_ret_net"])
    ic = ic_stats(df["ic"])
    capm, model = capm_regression(df["strategy_ret_net"], benchmark_weekly(spy, df))

    print("4/5 Charts ...")
    for path in (
        plots.cumulative_returns(df),
        plots.drawdown(drawdown_series(df["strategy_ret_net"])),
        plots.ic_series(df["ic"]),
        plots.long_short_bars(df),
    ):
        print(f"    wrote {path}")

    print("5/5 Results ...")
    os.makedirs(RESULTS_DIR, exist_ok=True)
    df.to_csv(os.path.join(RESULTS_DIR, "weekly_returns.csv"))

    fmt = table.copy()
    for col in ["Ann. return", "Ann. vol", "Max drawdown", "Hit rate"]:
        fmt[col] = fmt[col].map("{:.2%}".format)
    fmt["Sharpe"] = fmt["Sharpe"].map("{:.2f}".format)

    lines = [
        "# Backtest results",
        "",
        f"- Sample: {df.index[0]:%Y-%m-%d} to {df.index[-1]:%Y-%m-%d} "
        f"({len(df)} weekly periods)",
        f"- Average cross-section after volatility filter: "
        f"{df['universe_size'].mean():.0f} stocks "
        f"({df['n_long'].mean():.0f} long / {df['n_short'].mean():.0f} short)",
        f"- Average weekly turnover (traded notional / NAV): {df['turnover'].mean():.2f}x, "
        f"cost {COST_PER_SIDE * 1e4:.0f} bps per side "
        f"(avg {df['cost'].mean() * 1e4:.1f} bps/week)",
        f"- Annualized cost drag: "
        f"{annualized_return(df['strategy_ret']) - annualized_return(df['strategy_ret_net']):.2%}",
        "",
        "## Performance",
        "",
        fmt.to_markdown(),
        "",
        "## Signal quality (weekly Spearman IC)",
        "",
        f"- Mean IC: {ic['mean_ic']:+.4f}",
        f"- IC std: {ic['ic_std']:.4f}",
        f"- ICIR: {ic['icir']:+.3f}",
        f"- t-stat of mean IC: {ic['ic_tstat']:+.2f}",
        f"- % weeks IC > 0: {ic['pct_positive']:.1%}",
        "",
        "## CAPM regression (net returns vs SPY, weekly)",
        "",
        f"- Alpha (weekly): {capm['alpha_weekly']:+.4%}  "
        f"(annualized {capm['alpha_annualized']:+.2%}), "
        f"t = {capm['alpha_tstat']:+.2f}, p = {capm['alpha_pvalue']:.3f}",
        f"- Beta: {capm['beta']:+.3f} (t = {capm['beta_tstat']:+.2f})",
        f"- R²: {capm['r_squared']:.3f}, N = {capm['n_obs']}",
        "",
        "```",
        str(model.summary()),
        "```",
        "",
    ]
    summary_path = os.path.join(RESULTS_DIR, "summary.md")
    with open(summary_path, "w") as f:
        f.write("\n".join(lines))
    print(f"    wrote {summary_path}")

    print()
    print(fmt.to_string())
    print()
    print(f"Mean IC {ic['mean_ic']:+.4f}  ICIR {ic['icir']:+.3f}  "
          f"alpha(ann) {capm['alpha_annualized']:+.2%} (p={capm['alpha_pvalue']:.3f})  "
          f"beta {capm['beta']:+.3f}")


if __name__ == "__main__":
    main()
