# reversal — research note

*This report is generated automatically by `quant_research.report`.*

## Hypothesis

Stocks that underperformed over the past week outperform over the next week (short-term reversal; Jegadeesh 1990, Lehmann 1990), and screening out high-volatility names leaves risk-adjusted excess returns that survive transaction costs.


## Methodology

- **Signal**: `reversal` with parameters `{'lookback': 5}` (higher score → long candidate)
- **Volatility screen**: drop names above the 80% cross-sectional quantile of trailing 21-day realized volatility
- **Portfolio**: long top 10% / short bottom 10% of the signal, equal-weighted, 0.5 gross per side (dollar-neutral)
- **Rebalance**: last trading day of each week; positions held until the next rebalance (non-overlapping holding periods)
- **Costs**: 5 bps per side on actual traded notional (`Σ|Δw| × fee`)
- **Universe**: current S&P 500 constituents with ≥70% price coverage
- **Sample**: 2019-04-05 to 2026-07-31 (383 weekly periods); average cross-section 391 stocks (39 long / 39 short)

## Performance

|              | Ann. return   | Ann. vol   |   Sharpe | Max drawdown   | Hit rate   |
|:-------------|:--------------|:-----------|---------:|:---------------|:-----------|
| Gross        | 7.92%         | 9.57%      |     0.83 | -10.97%        | 54.57%     |
| Net of costs | 3.06%         | 9.56%      |     0.32 | -14.43%        | 51.17%     |

- Average weekly turnover: 1.77x (avg cost 8.9 bps/week); annualized cost drag 4.86%
- Bootstrap 95% CI (net, 2000 draws, seed 42): ann. return [-3.63%, 10.51%], Sharpe [-0.39, 1.02]

### Sub-period analysis

|           |   Weeks | Gross ann.   | Net ann.   |   Net Sharpe |   Mean IC |
|:----------|--------:|:-------------|:-----------|-------------:|----------:|
| 2019–2021 |     144 | 10.19%       | 5.27%      |         0.43 |     0.016 |
| 2022–2024 |     156 | 9.10%        | 4.15%      |         0.56 |     0.029 |
| 2025–2026 |      83 | 1.99%        | -2.60%     |        -0.32 |     0.012 |

### Signal quality (weekly Spearman IC)

- Mean IC +0.0205, IC std 0.1864, ICIR +0.110, t-stat +2.15, % positive weeks 54.3%

### CAPM regression (net returns vs SPY, weekly)

- Alpha +0.0175%/week (annualized +0.91%), t = +0.27, p = 0.789
- Beta +0.156 (t = +6.13), R² 0.090, N = 383

## Charts

![dashboard](dashboard.png)

## Interpretation

- The signal shows statistically significant cross-sectional predictive power (mean IC +0.021, t = 2.15).
- Transaction costs reduce the Sharpe ratio from 0.83 to 0.32 (annualized cost drag 4.86%).
- Net-of-cost CAPM alpha is statistically indistinguishable from zero (+0.91%/yr, p = 0.789).
- Market beta of +0.16 is modest — the portfolio is close to market-neutral.
- The bootstrap 95% CI for the net Sharpe ratio [-0.39, 1.02] spans zero — the sample cannot rule out no edge.
- Performance weakened in the most recent sub-period (2025–2026: net Sharpe -0.32), though no formal structural-break analysis was performed.

## Limitations

- **Survivorship bias**: the universe is *current* S&P 500 constituents; stocks removed from the index (often after poor performance) are missing.
- **Simplified cost model**: flat fee per side on traded notional; no bid–ask spread, market impact, borrow costs, or short-locate constraints.
- **No sector neutralization**: cross-sectional ranks may partly reflect sector mean-reversion or sector trends.
- **Close-to-close execution**: assumes fills at the rebalance-day closing price with no implementation lag.
- **CAPM-only risk adjustment**: no Fama–French size/value/momentum controls.
- **No formal structural-break test**: sub-period results are descriptive.

## Appendix: full regression output

```
                            OLS Regression Results                            
==============================================================================
Dep. Variable:               strategy   R-squared:                       0.090
Model:                            OLS   Adj. R-squared:                  0.087
Method:                 Least Squares   F-statistic:                     37.53
Date:                Sat, 01 Aug 2026   Prob (F-statistic):           2.25e-09
Time:                        16:15:22   Log-Likelihood:                 1130.6
No. Observations:                 383   AIC:                            -2257.
Df Residuals:                     381   BIC:                            -2249.
Df Model:                           1                                         
Covariance Type:            nonrobust                                         
==============================================================================
                 coef    std err          t      P>|t|      [0.025      0.975]
------------------------------------------------------------------------------
const          0.0002      0.001      0.268      0.789      -0.001       0.001
spy_ret        0.1560      0.025      6.126      0.000       0.106       0.206
==============================================================================
Omnibus:                      137.369   Durbin-Watson:                   1.847
Prob(Omnibus):                  0.000   Jarque-Bera (JB):             1012.167
Skew:                           1.314   Prob(JB):                    1.62e-220
Kurtosis:                      10.518   Cond. No.                         39.3
==============================================================================

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.
```
