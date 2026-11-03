# Phase 6 — Event-definition and continuous-time Hawkes diagnostics

**Status: exploratory, not a validated Hawkes market mechanism.** All three evaluation dates (Oct 23–25, 2026) were previously examined during development. They are not independent untouched test dates.

## Protocol

- Source: Binance BTCUSDT spot `trades` (individual execution records) with microsecond timestamps; raw ZIPs are not redistributed.
- Pilot windows: **12:00–12:10 UTC** parameter fitting, **12:10–12:20 UTC** held-out-in-window scoring.
- Event definitions, chosen as sensitivity analyses rather than tuned for a good fit: (1) first execution at each distinct microsecond timestamp, (2) beginning of a new burst if the preceding unique timestamp is more than 1 ms earlier, (3) same with a 10 ms gap. Burst starts are *not* verified parent market orders.
- Individual executions cannot be fed unchanged to the simple Hawkes conditional likelihood here: most records have identical timestamps, yielding multiple simultaneous events, violating its simple-point-process assumption. Those records are used for fragmentation diagnostics instead.
- Hawkes: exponential-kernel, stationary baseline, fitted by 4-start bounded maximum likelihood on the first 10 minutes (`mu > 0`, `0 < n < 0.98`, `0.003 < beta < 2000/s`).
- Nonstationary Poisson benchmark: deterministic two-minute time-of-day intensity shape, estimated from the *five September dates* at 12:00–12:20 UTC, with 40% shrinkage toward the across-bin mean; per-day scale obtained only from the Oct evaluation day's 12:00–12:10 period. It is a limited benchmark; it does not explicitly account for stochastic intraday volatility.
- Scores: **continuous-time point-process log likelihood** on 12:10–12:20, using conditioning on the 12:00–12:10 Hawkes event history. Scores across event definitions are not directly comparable because they predict different point processes.
- Residuals: exact integral of fitted conditional intensity between consecutive held-out events (including the first interval since 12:10); time-rescaling theorem predicts unit exponential, equivalent to uniform PIT. KS p-values are indicative diagnostics, **not calibrated model-selection p-values**, especially with estimated parameters. Lag-1 residual correlations are also reported.

## Execution fragmentation

| Date | Raw executions | Unique microsecond timestamps | Executions sharing a timestamp | Timestamps with mixed maker flags |
|---|---:|---:|---:|---:|
| 2026-10-23 | 33,398 | 5,024 | 85.0% | 3 |
| 2026-10-24 | 10,779 | 2,967 | 72.5% | 0 |
| 2026-10-25 | 11,003 | 3,204 | 70.9% | 0 |

Most same-timestamp executions share the same aggressor-side indicator, but this **does not prove** they belong to one parent order. The dataset does not provide a reliable parent-order identifier.

## Fitted Hawkes parameters, predictive gains, residual diagnostics

| Date | Event definition | Held-out events | Branching n | Beta (/s) | Timescale (ms) | Hawkes LL gain / event vs time-of-day Poisson | Hawkes PIT KS p | Lag-1 correlation |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 2026-10-23 | unique_microsecond_timestamp | 3,075 | 0.284 | 439.80 | 2.3 | +1.6437 | 4.26e-78 | +0.287 |
| 2026-10-23 | burst_gap_1ms | 2,212 | 0.259 | 52.75 | 19.0 | +0.5027 | 2.09e-18 | +0.195 |
| 2026-10-23 | burst_gap_10ms | 1,662 | 0.387 | 1.51 | 663.1 | +0.0558 | 3.61e-07 | +0.006 |
| 2026-10-24 | unique_microsecond_timestamp | 1,402 | 0.271 | 2000.00* | 0.5 | +0.2924 | 1.27e-29 | +0.157 |
| 2026-10-24 | burst_gap_1ms | 1,298 | 0.236 | 11.31 | 88.4 | +0.1078 | 0.00618 | +0.082 |
| 2026-10-24 | burst_gap_10ms | 1,178 | 0.451 | 0.62 | 1612.0 | +0.0032 | 0.304 | -0.021 |
| 2026-10-25 | unique_microsecond_timestamp | 1,629 | 0.266 | 468.57 | 2.1 | +0.9782 | 5.02e-05 | +0.215 |
| 2026-10-25 | burst_gap_1ms | 1,348 | 0.197 | 63.48 | 15.8 | +0.3036 | 0.132 | +0.136 |
| 2026-10-25 | burst_gap_10ms | 1,135 | 0.118 | 6.14 | 162.8 | +0.0295 | 0.313 | +0.051 |

*Optimizer search bound reached: do not interpret the beta estimate as identified.*

## Findings

1. **Hawkes wins held-out log likelihood versus this limited time-of-day Poisson baseline in all 9 date/event-definition comparisons.** That is evidence of predictive event-history structure relative to this benchmark, **not** proof that Hawkes is correct or best among alternatives.
2. **Time-scale and strength depend strongly on event definition.** On Oct 23, the fitted beta changes from 439.8/s on unique timestamps to 1.51/s after the 10-ms gap rule. These are different processes and cannot be interpreted as consistent estimates of one real-world decay rate.
3. **Residual adequacy is mixed.** On unique-timestamp events, all three days reject the exponential residual distribution at the 5% level. For the 10-ms bursts, Oct 24 and Oct 25 have non-rejecting marginal KS tests, but this does not establish the required independence or correct intensity specification.
4. **A boundary issue persists.** On Oct 24 unique-timestamp events, beta reaches the expanded 2,000/s optimization cap. The optimizer success flag is not sufficient evidence of identification.
5. **No causality or trading profitability inference.** A better conditional likelihood does not prove order-to-order causation or signal profitability.

## Scientific cautions and missing work

- Time-varying Poisson here is **not** a strong stochastic-intensity baseline. The shape relies on five September dates and fixed 2-minute windows; compare with more adaptive Cox/time-varying intensity processes before claiming uniqueness.
- Interval-rescaling tests are not by themselves proof of model adequacy; inspect PIT autocorrelation over multiple lags and per-regime diagnostics.
- Timestamp grouping rules are sensitivity definitions, not ground truth for parent market orders. Better exchange message/order identifiers or higher-fidelity order-flow feeds could improve economic interpretation.
- First 10 minutes are used for training and prior history; the model does not have a pre-12:00 warm-up period.
- The three dates have already influenced prior development; no fresh independence claims.
- For stable publishable Hawkes parameters, require independently held-out dates, multiple disjoint intraday windows, solver convergence checks, parameter uncertainty, and a clear causal-event definition.

## Reproduce

From the repository environment: `pip install numpy pandas scipy numba matplotlib`, place the referenced daily ZIPs in `/mnt/data` (or adapt `ROOT` in `run.py`) and run `python run.py`, `python checks.py`, `python make_report.py`. Raw exchange files are not included.

## Bottom line

The data clearly show very heavy execution fragmentation, and a short-memory point process predicts the selected event stream better than the limited time-of-day Poisson benchmark. **The Hawkes decay timescale is not robustly identified across economically plausible event definitions.** This is a useful *diagnostic research result*, not evidence that the original Hawkes interpretation has been fully validated.
