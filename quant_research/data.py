"""Data acquisition: S&P 500 universe and daily adjusted prices.

Universe note: we use *current* S&P 500 constituents (from Wikipedia), which
introduces survivorship bias over the backtest window. This is acknowledged
as a limitation in the README; a production study would use point-in-time
constituents.
"""

from __future__ import annotations

import os
from io import StringIO

import pandas as pd
import requests
import yfinance as yf

WIKI_URL = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"
CACHE_DIR = "data"
PRICE_CACHE = os.path.join(CACHE_DIR, "prices.csv")


def get_sp500_tickers() -> list[str]:
    """Fetch current S&P 500 tickers from Wikipedia."""
    html = requests.get(
        WIKI_URL,
        headers={"User-Agent": "Mozilla/5.0 (independent research project)"},
        timeout=30,
    ).text
    table = pd.read_html(StringIO(html))[0]
    tickers = table["Symbol"].astype(str).tolist()
    # Yahoo Finance uses '-' instead of '.' for share classes (BRK.B -> BRK-B)
    return sorted({t.replace(".", "-") for t in tickers})


def download_prices(
    tickers: list[str],
    start: str = "2019-01-01",
    end: str | None = None,
    min_coverage: float = 0.7,
    use_cache: bool = True,
) -> pd.DataFrame:
    """Download daily auto-adjusted close prices for `tickers`.

    Drops tickers with less than `min_coverage` of the sample available
    (recent IPOs / listings), and caches the result to CSV.
    """
    if use_cache and os.path.exists(PRICE_CACHE):
        px = pd.read_csv(PRICE_CACHE, index_col=0, parse_dates=True)
        print(f"Loaded cached prices: {px.shape[0]} days x {px.shape[1]} tickers")
        return px

    px = yf.download(
        tickers, start=start, end=end, auto_adjust=True, progress=False
    )["Close"]
    px = px.sort_index()
    px = px.dropna(axis=1, thresh=int(min_coverage * len(px)))

    os.makedirs(CACHE_DIR, exist_ok=True)
    px.to_csv(PRICE_CACHE)
    print(f"Downloaded prices: {px.shape[0]} days x {px.shape[1]} tickers")
    return px


def download_benchmark(start: str = "2019-01-01", end: str | None = None) -> pd.Series:
    """Daily auto-adjusted close for SPY (market benchmark)."""
    spy = yf.download("SPY", start=start, end=end, auto_adjust=True, progress=False)[
        "Close"
    ]
    if isinstance(spy, pd.DataFrame):
        spy = spy.iloc[:, 0]
    return spy.rename("SPY")
