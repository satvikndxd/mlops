# momentum — backtest results

_6-1 momentum (past 126-day return, skipping the most recent 21 days)_

- Sample: 2019-08-16 to 2026-07-31 (364 weekly periods)
- Average cross-section: 391 stocks (39 long / 39 short)
- Average weekly turnover: 0.56x (avg cost 2.8 bps/week), annualized cost drag 1.46%

## Performance

|              | Ann. return   | Ann. vol   |   Sharpe | Max drawdown   | Hit rate   |
|:-------------|:--------------|:-----------|---------:|:---------------|:-----------|
| Gross        | -0.09%        | 10.21%     |    -0.01 | -15.36%        | 49.45%     |
| Net of costs | -1.55%        | 10.21%     |    -0.15 | -21.13%        | 49.18%     |

Bootstrap 95% CI (net, 2000 draws, seed 42): ann. return [-8.63%, 6.47%], Sharpe [-0.81, 0.68]

## Sub-period analysis

|           |   Weeks | Gross ann.   | Net ann.   |   Net Sharpe |   Mean IC |
|:----------|--------:|:-------------|:-----------|-------------:|----------:|
| 2019–2021 |     125 | -3.32%       | -4.80%     |        -0.42 |    -0.004 |
| 2022–2024 |     156 | 0.52%        | -0.92%     |        -0.11 |     0.01  |
| 2025–2026 |      83 | 3.77%        | 2.32%      |         0.21 |     0.014 |

## Signal quality (weekly Spearman IC)

- Mean IC: +0.0061, IC std: 0.2217, ICIR: +0.027, t-stat: +0.52, % positive weeks: 50.5%

## CAPM regression (net returns vs SPY, weekly)

- Alpha (weekly): -0.0145% (annualized -0.75%), t = -0.19, p = 0.846
- Beta: -0.017 (t = -0.60), R²: 0.001, N = 364

```
                            OLS Regression Results                            
==============================================================================
Dep. Variable:               strategy   R-squared:                       0.001
Model:                            OLS   Adj. R-squared:                 -0.002
Method:                 Least Squares   F-statistic:                    0.3570
Date:                Sat, 01 Aug 2026   Prob (F-statistic):              0.551
Time:                        16:06:09   Log-Likelihood:                 1033.9
No. Observations:                 364   AIC:                            -2064.
Df Residuals:                     362   BIC:                            -2056.
Df Model:                           1                                         
Covariance Type:            nonrobust                                         
==============================================================================
                 coef    std err          t      P>|t|      [0.025      0.975]
------------------------------------------------------------------------------
const         -0.0001      0.001     -0.194      0.846      -0.002       0.001
spy_ret       -0.0172      0.029     -0.598      0.551      -0.074       0.039
==============================================================================
Omnibus:                       33.258   Durbin-Watson:                   2.213
Prob(Omnibus):                  0.000   Jarque-Bera (JB):               81.743
Skew:                          -0.441   Prob(JB):                     1.78e-18
Kurtosis:                       5.147   Cond. No.                         38.8
==============================================================================

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.
```
