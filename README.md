# Testing the Short-Term Reversal Anomaly After Costs and Volatility Filtering

**A transaction-cost-aware backtest of a weekly market-neutral reversal strategy on S&P 500 equities (2019–2026).**

Independent quantitative research project. Python pipeline: data → signal → portfolio → costs → risk → inference.

## Research question

Do stocks that underperformed over the past week outperform over the next week — and does filtering out high-volatility stocks leave a strategy with risk-adjusted excess returns **after transaction costs**?

Short-term reversal is a well-documented cross-sectional anomaly (Jegadeesh 1990; Lehmann 1990). The goal here is not to "discover" a signal, but to test whether a known effect remains economically meaningful once tradability is taken seriously.

## Data

- Daily auto-adjusted close prices from Yahoo Finance (`yfinance`)
- Universe: current S&P 500 constituents (from Wikipedia), 490 tickers after a 70% data-coverage filter
- Sample: 2019-01-01 to 2026-07-31 → **383 non-overlapping weekly holding periods** (2019-04 to 2026-07)
- Benchmark: SPY, measured over the *exact same* holding windows as the strategy

## Strategy

At the last trading day of each week, using only information available up to that day:

1. **Signal**: `signal = −(past 5-day return)` (reversal)
2. **Volatility screen**: drop the top 20% of stocks by trailing 21-day realized volatility
3. **Portfolio**: long the top decile of the signal, short the bottom decile, equal-weighted, 0.5 gross per side → ~1x gross, dollar-neutral (~39 names per side on average)
4. **Holding period**: until the next weekly rebalance (~5 trading days); periods tile the sample exactly, so weekly returns are non-overlapping
5. **Costs**: 5 bps per side charged on **actual traded notional** (`Σ|Δw| × 5 bps`), not a flat fee — average realized turnover is 1.77x/week → ~8.9 bps/week, a **4.9%/yr cost drag**

## Results

| | Ann. return | Ann. vol | Sharpe | Max drawdown | Hit rate |
|:--|--:|--:|--:|--:|--:|
| **Gross** | 7.92% | 9.57% | 0.83 | −10.97% | 54.6% |
| **Net of costs** | 3.06% | 9.56% | 0.32 | −14.43% | 51.2% |

**Signal quality (weekly cross-sectional Spearman IC):**

- Mean IC **+0.021**, IC std 0.186, **ICIR 0.110**, t-stat of mean IC **+2.15**, 54.3% of weeks positive

**CAPM regression (net weekly returns vs SPY):**

- Alpha: +0.018%/week (**+0.91% annualized**), t = 0.27, p = 0.79 → *not statistically significant*
- Beta: **+0.156** (t = 6.13), R² = 0.09 → close to market-neutral, with a small residual long-market tilt

### Conclusion

> The reversal signal is statistically real — mean IC is positive and significant (t ≈ 2.2) and the gross Sharpe is 0.83 — but **its economic edge does not survive realistic transaction costs**. At 5 bps per side and ~1.8x weekly turnover, costs consume roughly 60% of gross returns, and net-of-cost alpha is indistinguishable from zero. This is consistent with the literature: short-term reversal profits are heavily turnover-dependent and have decayed in large-cap universes.

### Charts

![Cumulative returns](charts/cumulative_returns.png)
![Drawdown](charts/drawdown.png)
![Information coefficient](charts/information_coefficient.png)
![Long vs short](charts/long_short.png)

Full regression output and weekly return series: [`results/summary.md`](results/summary.md), [`results/weekly_returns.csv`](results/weekly_returns.csv).

## Reproduce

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python run_backtest.py
```

Downloads ~7.5 years of daily prices for the S&P 500 (cached to `data/` after the first run), runs the backtest, and writes `charts/` and `results/`.

## Repository layout

```
data.py          # universe (Wikipedia) + price download (yfinance), with caching
signals.py       # 5-day reversal signal, 21-day realized vol screen
backtest.py      # weekly rebalance loop, turnover-based costs, weekly IC
metrics.py       # annualized return/vol, Sharpe, drawdown, IC stats
plots.py         # matplotlib charts (CVD-safe palette)
run_backtest.py  # end-to-end runner
results/         # summary.md, weekly_returns.csv
charts/          # PNG charts
```

## Limitations

- **Survivorship bias**: the universe is *current* S&P 500 constituents, so stocks that were removed (often after poor performance) are missing. This likely flatters the long leg. A production study would use point-in-time constituents.
- **Simplified cost model**: flat 5 bps per side; no bid–ask spread modeling, market impact, borrow costs, or short-locate constraints. Real costs for the short leg would be higher.
- **No sector neutralization**: reversal returns may partly reflect sector mean-reversion.
- **Close-to-close execution**: assumes fills at the closing price on the rebalance day; no implementation lag.
- **No corporate-action point-in-time handling** beyond Yahoo's adjusted prices.
- **Single parameterization**: 5-day signal / 21-day vol / decile portfolios were fixed a priori (standard values from the literature, not optimized), but no sensitivity analysis across parameters is reported.

## Future work

- Point-in-time universe (e.g., historical index constituent files) to remove survivorship bias
- Spread-based cost model and turnover-reduction techniques (buffering, slower rebalance, signal blending)
- Sector-neutral ranking and Fama–French 3/5-factor regression instead of CAPM
- ML extension: walk-forward LightGBM on return/volatility/volume features, compared against this linear ranking baseline on IC and net Sharpe
