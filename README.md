# BTC/USDT Trade-Arrival Dynamics: Count Forecasting and Hawkes Diagnostics

**Status:** Exploratory research / working paper. Not peer reviewed. No trading strategy or return claim.  
**Author:** Jude Kriel Ramcharitar (2026)

This study has two distinct components:

1. One-second arrival-count forecasting using distinct microsecond execution timestamps, comparing blended trailing rates, exponential event-history features, and autoregressive counts.
2. Continuous-time exponential Hawkes diagnostics under alternative definitions of market events, compared with a limited time-varying Poisson benchmark and time-rescaling checks.

## Main findings

- Across October 23–27, the count-AR model gained an average **+0.0571 negative-binomial log-score units/second** over the blended trailing-rate benchmark. It outperformed exponential-history counts on 3/5 dates.
- In three selected 20-minute windows, continuous-time Hawkes outscored the tested nonstationary Poisson baseline in 9/9 event-definition/date comparisons, but fitted parameters were highly sensitive to grouping executions into event bursts.
- One decay estimate hit an optimizer bound; several residual tests failed. Likelihood improvement alone **does not establish causal self-excitation**.

## Research limitations

These were retrospective experiments with evolving model choices, not preregistered tests. Raw trades are not parent orders; timestamp grouping changes the event definition. No claims of profitable trading signals, market impact, causal excitation, or investable alpha are made.

## Reproduction

The full prepared repository includes `src/`, `tests/`, `results/`, `figures/`, `docs/`, and `paper/`. The original Binance BTCUSDT spot daily `trades` archives are excluded due to file size. **The remaining research files are not yet uploaded to this GitHub repository.** Until they are, the reproduction instructions below are not executable from this repository alone.

When all files have been uploaded, use Python 3.11+:

```bash
python -m pip install -r requirements.txt
python tests/test_compensator.py
python tests/test_causality.py
python src/counts/reproduce.py --data-dir data --out results/counts_recomputed.json
```

Source data: [Binance Public Data](https://data.binance.vision/). See `docs/data_manifest.json` in the prepared research package for exact daily file names and checksums.

The paper is a working paper, not peer-reviewed research.
