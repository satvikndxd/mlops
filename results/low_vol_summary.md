# low_vol — backtest results

_Low-volatility (long least volatile names, short most volatile)_

- Sample: 2019-05-10 to 2026-07-31 (378 weekly periods)
- Average cross-section: 488 stocks (49 long / 49 short)
- Average weekly turnover: 0.21x (avg cost 1.0 bps/week), annualized cost drag 0.47%

## Performance

|              | Ann. return   | Ann. vol   |   Sharpe | Max drawdown   | Hit rate   |
|:-------------|:--------------|:-----------|---------:|:---------------|:-----------|
| Gross        | -12.32%       | 15.40%     |    -0.8  | -67.98%        | 46.56%     |
| Net of costs | -12.79%       | 15.40%     |    -0.83 | -69.02%        | 46.56%     |

Bootstrap 95% CI (net, 2000 draws, seed 42): ann. return [-22.28%, -2.53%], Sharpe [-1.51, -0.10]

## Sub-period analysis

|           |   Weeks | Gross ann.   | Net ann.   |   Net Sharpe |   Mean IC |
|:----------|--------:|:-------------|:-----------|-------------:|----------:|
| 2019–2021 |     139 | -12.48%      | -12.98%    |        -0.74 |    -0.008 |
| 2022–2024 |     156 | -7.60%       | -8.07%     |        -0.58 |    -0.008 |
| 2025–2026 |      83 | -20.31%      | -20.73%    |        -1.42 |    -0.049 |

## Signal quality (weekly Spearman IC)

- Mean IC: -0.0170, IC std: 0.2658, ICIR: -0.064, t-stat: -1.24, % positive weeks: 47.6%

## CAPM regression (net returns vs SPY, weekly)

- Alpha (weekly): -0.0759% (annualized -3.87%), t = -0.89, p = 0.374
- Beta: -0.531 (t = -16.04), R²: 0.406, N = 378

```
                            OLS Regression Results                            
==============================================================================
Dep. Variable:               strategy   R-squared:                       0.406
Model:                            OLS   Adj. R-squared:                  0.405
Method:                 Least Squares   F-statistic:                     257.2
Date:                Sat, 01 Aug 2026   Prob (F-statistic):           1.78e-44
Time:                        16:06:07   Log-Likelihood:                 1016.7
No. Observations:                 378   AIC:                            -2029.
Df Residuals:                     376   BIC:                            -2021.
Df Model:                           1                                         
Covariance Type:            nonrobust                                         
==============================================================================
                 coef    std err          t      P>|t|      [0.025      0.975]
------------------------------------------------------------------------------
const         -0.0008      0.001     -0.890      0.374      -0.002       0.001
spy_ret       -0.5314      0.033    -16.038      0.000      -0.597      -0.466
==============================================================================
Omnibus:                       45.806   Durbin-Watson:                   2.244
Prob(Omnibus):                  0.000   Jarque-Bera (JB):              159.755
Skew:                          -0.480   Prob(JB):                     2.04e-35
Kurtosis:                       6.037   Cond. No.                         39.1
==============================================================================

Notes:
[1] Standard Errors assume that the covariance matrix of the errors is correctly specified.
```
