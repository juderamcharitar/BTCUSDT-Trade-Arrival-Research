# Continuous-time Hawkes estimator: validation and boundary investigation

## What was tested

- Original exponential-kernel continuous-time point-process likelihood from the earlier research was recreated with an explicit, chronological event recursion and analytical compensator.
- The previous optimizer used `log(beta) <= 5`, forcing `beta <= 148.413/s`. This investigation expanded the bound to 2,000/s and used four independent initializations.
- Three synthetic branching-process-generated Hawkes datasets, with known parameters, tested parameter recovery.
- Two real BTC/USDT 10-minute samples from 12:00 UTC (2026-10-01 and 2026-10-23) tested raw timestamp events and grouped timestamps at 1 ms, 10 ms, and 100 ms.
- Unit checks included the exact homogeneous-Poisson limit, pre-window event compensation, and protection against future-event contamination.

## Synthetic recovery

| Truth mu | Truth n | Truth beta (/sec) | Est mu | Est n | Est beta (/sec) | Optimizer success |
|---:|---:|---:|---:|---:|---:|:---:|
| 4.000 | 0.250 | 0.500 | 3.941 | 0.251 | 0.329 | Yes |
| 3.000 | 0.550 | 2.000 | 3.185 | 0.546 | 2.167 | No |
| 1.800 | 0.700 | 12.000 | 1.794 | 0.697 | 11.857 | Yes |

A single optimizer-run success flag was false in the second synthetic test even though the best objective and recovered parameters were close to the truth. This needs convergence tolerance / numerical-gradient refinement before treating the estimator as fully verified. These are three examples, not a Monte Carlo coverage study.

## Real-data sensitivity

| Date | Timestamp grouping | Events | Estimated branching mass n | beta (/sec) | Decay time (ms) |
|---|---|---:|---:|---:|---:|
| 2026-10-01 | Exact microsecond | 2,127 | 0.284 | 210.62 | 4.75 |
| 2026-10-01 | 1 ms | 1,952 | 0.330 | 34.04 | 29.37 |
| 2026-10-01 | 10 ms | 1,680 | 0.446 | 3.67 | 272.65 |
| 2026-10-01 | 100 ms | 1,323 | 0.424 | 0.64 | 1557.51 |
| 2026-10-23 | Exact microsecond | 1,949 | 0.284 | 439.80 | 2.27 |
| 2026-10-23 | 1 ms | 1,731 | 0.267 | 92.96 | 10.76 |
| 2026-10-23 | 10 ms | 1,476 | 0.268 | 10.02 | 99.85 |
| 2026-10-23 | 100 ms | 1,178 | 0.351 | 0.40 | 2530.96 |

## Interpretation

1. **No obvious arithmetic failure in the likelihood implementation.** The synthetic examples recover the branching mass and decay scale reasonably closely, and the compensator and likelihood boundary tests pass. This does not yet prove accuracy under all real-data regimes.
2. **The original upper-bound hit was partly a search-range artifact.** With beta allowed to reach 2,000/s, exact-timestamp estimates on the two selected real windows were approximately 211/s and 440/s, above the old 148/s cap, with no new boundary hits.
3. **The economically meaningful timescale remains unidentified.** With 100-ms grouping, the fitted beta moves to approximately 0.64/s and 0.40/s. These are fundamentally different event definitions, so they are not interchangeable estimates of the same physical process.
4. **Identical timestamps and clustered fills are central.** A distinct timestamp is not necessarily a distinct market order. Aggregating by time bucket can merge unrelated events, while using every execution can split a single parent order into many apparent events.
5. **We have not established Hawkes model adequacy, causal triggering, or profitability.** Need time-rescaling diagnostics against properly specified time-varying baselines, and broader synthetic parameter-recovery experiments.

## Limitations and next step

- This is a targeted diagnostic using two ten-minute real windows and three known-parameter synthetic datasets, selected after extensive earlier exploration. It is not a new independent chronological evaluation.
- The process is initialized with no pre-window history. A warm-up segment preceding the estimation period can reduce initial-condition bias, especially for slow decay.
- SciPy numerical optimization can terminate without a success flag despite near-truth estimates: improve gradients and convergence reporting before full inference.
- Work out a plausible economic event definition (at minimum, same-timestamp aggregation, and if available aggressor-side grouping) and choose it **before** further fitting; do not select grouping to make the model look good.
- Fit and check time-rescaling diagnostics and stronger nonstationary Poisson baselines, then evaluate on predesignated untouched windows.

## Reproduction

Install Python with `numpy pandas scipy numba`; put original Binance daily ZIPs under `/mnt/data/`, then run `python validate.py` and `python checks.py`. Inputs and SHA-256 hashes are recorded in `results.json`. No raw exchange data is redistributed.
