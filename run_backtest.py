"""Factor research runner: data -> signal -> portfolio -> costs -> risk -> inference.

Usage:
    python run_backtest.py                                # default: reversal
    python run_backtest.py --config configs/momentum.yaml # one factor
    python run_backtest.py --all                          # every config + comparison

Outputs per factor: charts/<name>_dashboard.png, results/<name>_summary.md,
results/<name>_weekly.csv. With --all: results/comparison.md.
The primary factor (reversal) also gets the four standalone README charts.
"""

from __future__ import annotations

import argparse
import glob
import os

import pandas as pd
import statsmodels.api as sm

import plots
from backtest import benchmark_weekly, load_config, run_backtest
from data import download_benchmark, download_prices, get_sp500_tickers
from metrics import (
    PERIODS_PER_YEAR,
    annualized_return,
    bootstrap_ci,
    drawdown_series,
    ic_stats,
    subperiod_table,
    summary_table,
)

START = "2019-01-01"
RESULTS_DIR = "results"
PRIMARY = "reversal"  # gets the standalone README charts
SUBPERIODS = [("2019", "2021"), ("2022", "2024"), ("2025", "2026")]


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


def fmt_summary(table: pd.DataFrame) -> pd.DataFrame:
    fmt = table.copy()
    for col in ["Ann. return", "Ann. vol", "Max drawdown", "Hit rate"]:
        fmt[col] = fmt[col].map("{:.2%}".format)
    fmt["Sharpe"] = fmt["Sharpe"].map("{:.2f}".format)
    return fmt


def run_factor(cfg: dict, px: pd.DataFrame, spy: pd.Series) -> dict:
    name = cfg["name"]
    print(f"== {name} ==")
    df = run_backtest(px, cfg)
    print(f"   {len(df)} weekly periods, {df.index[0]:%Y-%m-%d} -> {df.index[-1]:%Y-%m-%d}")

    spy_ret = benchmark_weekly(spy, df)
    table = summary_table(df["strategy_ret"], df["strategy_ret_net"])
    ic = ic_stats(df["ic"])
    capm, model = capm_regression(df["strategy_ret_net"], spy_ret)
    boot = bootstrap_ci(df["strategy_ret_net"])
    subs = subperiod_table(df, SUBPERIODS)

    # charts
    charts = [plots.dashboard(df, spy_ret, name)]
    if name == PRIMARY:
        charts += [
            plots.cumulative_returns(df),
            plots.drawdown(drawdown_series(df["strategy_ret_net"])),
            plots.ic_series(df["ic"]),
            plots.long_short_bars(df),
        ]
    for path in charts:
        print(f"   wrote {path}")

    # results
    os.makedirs(RESULTS_DIR, exist_ok=True)
    df.to_csv(os.path.join(RESULTS_DIR, f"{name}_weekly.csv"))

    sub_fmt = subs.copy()
    sub_fmt["Weeks"] = sub_fmt["Weeks"].astype(int)
    for col in ["Gross ann.", "Net ann."]:
        sub_fmt[col] = sub_fmt[col].map("{:.2%}".format)
    sub_fmt["Net Sharpe"] = sub_fmt["Net Sharpe"].map("{:.2f}".format)
    sub_fmt["Mean IC"] = sub_fmt["Mean IC"].map("{:+.3f}".format)

    lines = [
        f"# {name} — backtest results",
        "",
        f"_{cfg.get('description', '')}_",
        "",
        f"- Sample: {df.index[0]:%Y-%m-%d} to {df.index[-1]:%Y-%m-%d} "
        f"({len(df)} weekly periods)",
        f"- Average cross-section: {df['universe_size'].mean():.0f} stocks "
        f"({df['n_long'].mean():.0f} long / {df['n_short'].mean():.0f} short)",
        f"- Average weekly turnover: {df['turnover'].mean():.2f}x "
        f"(avg cost {df['cost'].mean() * 1e4:.1f} bps/week), annualized cost drag "
        f"{annualized_return(df['strategy_ret']) - annualized_return(df['strategy_ret_net']):.2%}",
        "",
        "## Performance",
        "",
        fmt_summary(table).to_markdown(),
        "",
        f"Bootstrap 95% CI (net, {boot['n_boot']} draws, seed 42): "
        f"ann. return [{boot['ann_return_ci'][0]:.2%}, {boot['ann_return_ci'][1]:.2%}], "
        f"Sharpe [{boot['sharpe_ci'][0]:.2f}, {boot['sharpe_ci'][1]:.2f}]",
        "",
        "## Sub-period analysis",
        "",
        sub_fmt.to_markdown(),
        "",
        "## Signal quality (weekly Spearman IC)",
        "",
        f"- Mean IC: {ic['mean_ic']:+.4f}, IC std: {ic['ic_std']:.4f}, "
        f"ICIR: {ic['icir']:+.3f}, t-stat: {ic['ic_tstat']:+.2f}, "
        f"% positive weeks: {ic['pct_positive']:.1%}",
        "",
        "## CAPM regression (net returns vs SPY, weekly)",
        "",
        f"- Alpha (weekly): {capm['alpha_weekly']:+.4%} "
        f"(annualized {capm['alpha_annualized']:+.2%}), "
        f"t = {capm['alpha_tstat']:+.2f}, p = {capm['alpha_pvalue']:.3f}",
        f"- Beta: {capm['beta']:+.3f} (t = {capm['beta_tstat']:+.2f}), "
        f"R²: {capm['r_squared']:.3f}, N = {capm['n_obs']}",
        "",
        "```",
        str(model.summary()),
        "```",
        "",
    ]
    summary_path = os.path.join(RESULTS_DIR, f"{name}_summary.md")
    with open(summary_path, "w") as f:
        f.write("\n".join(lines))
    print(f"   wrote {summary_path}")

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
    parser = argparse.ArgumentParser(description="Run factor backtests")
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
