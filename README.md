# BTC/USDT Trade-Arrival Dynamics: Count Forecasting and Hawkes Diagnostics

**Status:** exploratory research / working paper; not peer reviewed; no trading strategy or return claim.  
**Author:** Jude Kriel Ramcharitar (2026)

This repository consolidates two related **but distinct** analyses:

1. **One-second arrival-count forecasting** for distinct microsecond execution timestamps, comparing a blended trailing-rate baseline, a discrete-time exponential-history model, and an autoregressive count model. An independent frozen-parameter replay reproduced all 15 saved Oct 23–27 model/date log scores (see `docs/phase4_audit.md`).
2. **Continuous-time exponential Hawkes diagnostics** using three operational event definitions on Oct 23–25, with a limited time-of-day Poisson comparison and time-rescaling residual tests. Hawkes parameters vary materially with execution grouping; most specifications fail one or more diagnostic checks. These pilot windows were previously examined and **are not pristine independent tests**.

## Most important findings

- Across five October 23–27 dates the count-AR model gained **+0.0571 negative-binomial log-score units per second** on average versus the blended trailing-rate baseline. The AR model beat the exponential-history count model on only 3 of 5 dates.
- In three selected 20-minute windows, the continuous-time Hawkes specification outscored the limited nonstationary Poisson baseline in **9/9** event-definition/date comparisons, but estimates and goodness-of-fit are **sensitive to how executions are defined**. The beta estimate hit the optimizer bound on one fit. Conditional likelihood improvement alone is **not** a validated causal excitation mechanism.
- Raw exchange trades are not parent orders. No proof of causality, market impact, future profit or investable alpha is claimed.

## Reproducing the stored results

Create Python 3.11+ environment, then:

```bash
python -m pip install -r requirements.txt
python tests/test_compensator.py
python tests/test_causality.py
```

For count-evaluation replay, download original Binance BTCUSDT `trades` ZIPs for Oct 23–27 and put them in `data/` (names and expected SHA-256 in `docs/data_manifest.json`), then:

```bash
python src/counts/reproduce.py --data-dir data --out results/counts_recomputed.json
```

For the continuous-time event-definition analysis, place the 5 September ZIPs and Oct 23–25 ZIPs in `data/`, then run:

```bash
BTCUSDT_DATA_DIR=data python src/hawkes/run.py
```

On Windows PowerShell:

```powershell
$env:BTCUSDT_DATA_DIR = "data"
python src/hawkes/run.py
```

This step is computationally more intensive and regenerates `results/hawkes_recomputed/` without overwriting archived outcomes. For synthetic parameter-recovery checks:

```bash
BTCUSDT_DATA_DIR=data python src/continuous_time/validate.py
```

`src/counts/phase4_original.py` is preserved as an **archival training/validation script**. It is not certified here as an independently re-executed end-to-end training replay. The count replay checks frozen-parameter evaluation. Do not describe either analysis as pre-registered.

## Repository contents

- `paper/`: consolidated working paper (PDF and Markdown)
- `src/counts/`: frozen-model evaluation and archived fitting source
- `src/continuous_time/`: continuous-time estimator and synthetic parameter-recovery code
- `src/hawkes/`: operational event definitions, likelihood comparison and rescaling diagnostics
- `tests/`: checks used in prior experiments
- `results/`: archived model parameters and machine-readable results
- `figures/`: documented graphs
- `docs/`: audit notes, full Phase 6 report and checksummed source manifest

## Dataset and ethics

Source: [Binance Public Data](https://data.binance.vision/), spot daily BTCUSDT `trades`. Raw ZIPs are excluded because they are large. Verify source, license and any applicable use conditions independently before redistributing raw trade data. The repository is a research artifact, not investment advice.

## Research limitations

The limited continuous-time Poisson benchmark does not model stochastic activity intensity. Event-gap grouping does not reconstruct aggressor parent orders. Marginal KS non-rejection is not independent-residual validation. Five-day score statistics have limited day-level inferential power. Results are retrospective and methods evolved after earlier analyses of nearby dates. See the paper for full details.
