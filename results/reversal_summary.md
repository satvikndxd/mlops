# reversal — backtest results

_Short-term reversal (buy 5-day losers, sell 5-day winners) with a volatility screen_

- Sample: 2019-04-05 to 2026-07-31 (383 weekly periods)
- Average cross-section: 391 stocks (39 long / 39 short)
- Average weekly turnover: 1.77x (avg cost 8.9 bps/week), annualized cost drag 4.86%

## Performance

|              | Ann. return   | Ann. vol   |   Sharpe | Max drawdown   | Hit rate   |
|:-------------|:--------------|:-----------|---------:|:---------------|:-----------|
| Gross        | 7.92%         | 9.57%      |     0.83 | -10.97%        | 54.57%     |
| Net of costs | 3.06%         | 9.56%      |     0.32 | -14.43%        | 51.17%     |

Bootstrap 95% CI (net, 2000 draws, seed 42): ann. return [-3.63%, 10.51%], Sharpe [-0.39, 1.02]

## Sub-period analysis

|           |   Weeks | Gross ann.   | Net ann.   |   Net Sharpe |   Mean IC |
|:----------|--------:|:-------------|:-----------|-------------:|----------:|
| 2019–2021 |     144 | 10.19%       | 5.27%      |         0.43 |     0.016 |
| 2022–2024 |     156 | 9.10%        | 4.15%      |         0.56 |     0.029 |
| 2025–2026 |      83 | 1.99%        | -2.60%     |        -0.32 |     0.012 |

## Signal quality (weekly Spearman IC)

- Mean IC: +0.0205, IC std: 0.1864, ICIR: +0.110, t-stat: +2.15, % positive weeks: 54.3%

## CAPM regression (net returns vs SPY, weekly)

- Alpha (weekly): +0.0175% (annualized +0.91%), t = +0.27, p = 0.789
- Beta: +0.156 (t = +6.13), R²: 0.090, N = 383

```
                            OLS Regression Results                            
==============================================================================
Dep. Variable:               strategy   R-squared:                       0.090
Model:                            OLS   Adj. R-squared:                  0.087
Method:                 Least Squares   F-statistic:                     37.53
Date:                Sat, 01 Aug 2026   Prob (F-statistic):           2.25e-09
Time:                        16:06:12   Log-Likelihood:                 1130.6
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
Prob(Omnibus):                  0.000   Jarque-Bera (JB):             1012.170
Skew:                           1.314   Prob(JB):                    1.62e-220
Kurtosis:                      10.518   Cond. No.                         39.3
==============================================================================

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.
```
