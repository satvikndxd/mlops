"""Backward-compatible shim: `python run_backtest.py` == `quant-backtest`."""

from quant_research.cli import main

if __name__ == "__main__":
    main()
