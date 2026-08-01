"""Automatic research-note generation.

For each factor run, `analyze()` computes the full statistics bundle and
`write_report()` renders a self-contained markdown research note —
hypothesis, methodology, metrics, charts, interpretation, limitations —
so every experiment produces the same standardized artifact.

The interpretation section is rule-based: it is derived from the computed
statistics (IC t-stat, alpha p-value, beta, bootstrap CIs, sub-periods),
not hand-written per factor, so it cannot drift out of sync with results.
"""

from __future__ import annotations

import os

import pandas as pd
import statsmodels.api as sm

from .metrics import (
    PERIODS_PER_YEAR,
    annualized_return,
    bootstrap_ci,
    ic_stats,
    subperiod_table,
    summary_table,
)

LIMITATIONS = [
    "**Survivorship bias**: the universe is *current* S&P 500 constituents; "
    "stocks removed from the index (often after poor performance) are missing.",
    "**Simplified cost model**: flat fee per side on traded notional; no bid–ask "
    "spread, market impact, borrow costs, or short-locate constraints.",
    "**No sector neutralization**: cross-sectional ranks may partly reflect "
    "sector mean-reversion or sector trends.",
    "**Close-to-close execution**: assumes fills at the rebalance-day closing "
    "price with no implementation lag.",
    "**CAPM-only risk adjustment**: no Fama–French size/value/momentum controls.",
    "**No formal structural-break test**: sub-period results are descriptive.",
]


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


def analyze(df: pd.DataFrame, spy_ret: pd.Series, subperiods: list[tuple[str, str]]) -> dict:
    """Compute the full statistics bundle for one factor run."""
    capm, model = capm_regression(df["strategy_ret_net"], spy_ret)
    return {
        "table": summary_table(df["strategy_ret"], df["strategy_ret_net"]),
        "ic": ic_stats(df["ic"]),
        "capm": capm,
        "model": model,
        "boot": bootstrap_ci(df["strategy_ret_net"]),
        "subs": subperiod_table(df, subperiods),
        "cost_drag": annualized_return(df["strategy_ret"])
        - annualized_return(df["strategy_ret_net"]),
    }


def interpret(stats: dict) -> list[str]:
    """Rule-based interpretation derived from the computed statistics."""
    ic, capm, boot = stats["ic"], stats["capm"], stats["boot"]
    table, subs = stats["table"], stats["subs"]
    out = []

    # signal quality
    if ic["ic_tstat"] >= 2:
        out.append(
            f"The signal shows statistically significant cross-sectional predictive "
            f"power (mean IC {ic['mean_ic']:+.3f}, t = {ic['ic_tstat']:.2f})."
        )
    elif ic["ic_tstat"] <= -2:
        out.append(
            f"The signal predicts in the *wrong* direction at conventional "
            f"significance (mean IC {ic['mean_ic']:+.3f}, t = {ic['ic_tstat']:.2f})."
        )
    else:
        out.append(
            f"The signal's predictive power is not statistically distinguishable "
            f"from zero (mean IC {ic['mean_ic']:+.3f}, t = {ic['ic_tstat']:.2f})."
        )

    # economic significance
    gross_s, net_s = table.loc["Gross", "Sharpe"], table.loc["Net of costs", "Sharpe"]
    out.append(
        f"Transaction costs reduce the Sharpe ratio from {gross_s:.2f} to {net_s:.2f} "
        f"(annualized cost drag {stats['cost_drag']:.2%})."
    )
    if capm["alpha_pvalue"] < 0.05:
        out.append(
            f"Net-of-cost CAPM alpha is statistically significant "
            f"({capm['alpha_annualized']:+.2%}/yr, p = {capm['alpha_pvalue']:.3f})."
        )
    else:
        out.append(
            f"Net-of-cost CAPM alpha is statistically indistinguishable from zero "
            f"({capm['alpha_annualized']:+.2%}/yr, p = {capm['alpha_pvalue']:.3f})."
        )

    # risk exposure
    if abs(capm["beta"]) > 0.3:
        out.append(
            f"Market beta of {capm['beta']:+.2f} is material: raw returns partly "
            f"reflect market exposure rather than cross-sectional selection."
        )
    else:
        out.append(f"Market beta of {capm['beta']:+.2f} is modest — the portfolio is close to market-neutral.")

    # uncertainty
    lo, hi = boot["sharpe_ci"]
    if lo < 0 < hi:
        out.append(
            f"The bootstrap 95% CI for the net Sharpe ratio [{lo:.2f}, {hi:.2f}] "
            f"spans zero — the sample cannot rule out no edge."
        )
    else:
        out.append(f"The bootstrap 95% CI for the net Sharpe ratio [{lo:.2f}, {hi:.2f}] excludes zero.")

    # stability (descriptive only)
    if len(subs) >= 2:
        last = subs.iloc[-1]
        full_sharpe = table.loc["Net of costs", "Sharpe"]
        if last["Net Sharpe"] < min(0, full_sharpe):
            out.append(
                f"Performance weakened in the most recent sub-period "
                f"({subs.index[-1]}: net Sharpe {last['Net Sharpe']:.2f}), though no "
                f"formal structural-break analysis was performed."
            )
        else:
            out.append(
                f"Sub-period results are broadly consistent with the full sample "
                f"(most recent: net Sharpe {last['Net Sharpe']:.2f}); no formal "
                f"structural-break analysis was performed."
            )
    return out


def _fmt_summary(table: pd.DataFrame) -> pd.DataFrame:
    fmt = table.copy()
    for col in ["Ann. return", "Ann. vol", "Max drawdown", "Hit rate"]:
        fmt[col] = fmt[col].map("{:.2%}".format)
    fmt["Sharpe"] = fmt["Sharpe"].map("{:.2f}".format)
    return fmt


def _fmt_subs(subs: pd.DataFrame) -> pd.DataFrame:
    fmt = subs.copy()
    fmt["Weeks"] = fmt["Weeks"].astype(int)
    for col in ["Gross ann.", "Net ann."]:
        fmt[col] = fmt[col].map("{:.2%}".format)
    fmt["Net Sharpe"] = fmt["Net Sharpe"].map("{:.2f}".format)
    fmt["Mean IC"] = fmt["Mean IC"].map("{:+.3f}".format)
    return fmt


def write_report(cfg: dict, df: pd.DataFrame, stats: dict, out_dir: str) -> str:
    """Render the standardized markdown research note for one factor."""
    name = cfg["name"]
    ic, capm, boot = stats["ic"], stats["capm"], stats["boot"]
    filt = cfg.get("filter")
    port = cfg.get("portfolio", {})
    costs = cfg.get("costs", {})
    sig = cfg["signal"]

    filter_line = (
        f"drop names above the {filt['vol_cut']:.0%} cross-sectional quantile of "
        f"trailing {filt['vol_window']}-day realized volatility"
        if filt
        else "none (the signal itself is a volatility measure)"
    )

    lines = [
        f"# {name} — research note",
        "",
        "*This report is generated automatically by `quant_research.report`.*",
        "",
        "## Hypothesis",
        "",
        cfg.get("hypothesis", cfg.get("description", "")),
        "",
        "## Methodology",
        "",
        f"- **Signal**: `{sig['type']}` with parameters `{sig.get('params', {})}` "
        f"(higher score → long candidate)",
        f"- **Volatility screen**: {filter_line}",
        f"- **Portfolio**: long top {port.get('top_pct', 0.10):.0%} / short bottom "
        f"{port.get('top_pct', 0.10):.0%} of the signal, equal-weighted, "
        f"{port.get('gross_per_side', 0.5)} gross per side (dollar-neutral)",
        "- **Rebalance**: last trading day of each week; positions held until the "
        "next rebalance (non-overlapping holding periods)",
        f"- **Costs**: {costs.get('bps_per_side', 5)} bps per side on actual traded "
        "notional (`Σ|Δw| × fee`)",
        "- **Universe**: current S&P 500 constituents with ≥70% price coverage",
        f"- **Sample**: {df.index[0]:%Y-%m-%d} to {df.index[-1]:%Y-%m-%d} "
        f"({len(df)} weekly periods); average cross-section "
        f"{df['universe_size'].mean():.0f} stocks "
        f"({df['n_long'].mean():.0f} long / {df['n_short'].mean():.0f} short)",
        "",
        "## Performance",
        "",
        _fmt_summary(stats["table"]).to_markdown(),
        "",
        f"- Average weekly turnover: {df['turnover'].mean():.2f}x "
        f"(avg cost {df['cost'].mean() * 1e4:.1f} bps/week); annualized cost drag "
        f"{stats['cost_drag']:.2%}",
        f"- Bootstrap 95% CI (net, {boot['n_boot']} draws, seed 42): ann. return "
        f"[{boot['ann_return_ci'][0]:.2%}, {boot['ann_return_ci'][1]:.2%}], "
        f"Sharpe [{boot['sharpe_ci'][0]:.2f}, {boot['sharpe_ci'][1]:.2f}]",
        "",
        "### Sub-period analysis",
        "",
        _fmt_subs(stats["subs"]).to_markdown(),
        "",
        "### Signal quality (weekly Spearman IC)",
        "",
        f"- Mean IC {ic['mean_ic']:+.4f}, IC std {ic['ic_std']:.4f}, "
        f"ICIR {ic['icir']:+.3f}, t-stat {ic['ic_tstat']:+.2f}, "
        f"% positive weeks {ic['pct_positive']:.1%}",
        "",
        "### CAPM regression (net returns vs SPY, weekly)",
        "",
        f"- Alpha {capm['alpha_weekly']:+.4%}/week "
        f"(annualized {capm['alpha_annualized']:+.2%}), "
        f"t = {capm['alpha_tstat']:+.2f}, p = {capm['alpha_pvalue']:.3f}",
        f"- Beta {capm['beta']:+.3f} (t = {capm['beta_tstat']:+.2f}), "
        f"R² {capm['r_squared']:.3f}, N = {capm['n_obs']}",
        "",
        "## Charts",
        "",
        "![dashboard](dashboard.png)",
        "",
        "## Interpretation",
        "",
        *[f"- {s}" for s in interpret(stats)],
        "",
        "## Limitations",
        "",
        *[f"- {s}" for s in LIMITATIONS],
        "",
        "## Appendix: full regression output",
        "",
        "```",
        str(stats["model"].summary()),
        "```",
        "",
    ]
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "report.md")
    with open(path, "w") as f:
        f.write("\n".join(lines))
    return path
