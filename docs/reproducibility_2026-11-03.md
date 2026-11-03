# Reproducibility verification — 2026-11-03

**Scope:** Clean local extraction of the prepared repository archive, with the same source and archived results as the published GitHub files. The original 16 Binance BTCUSDT daily ZIP archives were already available locally and were linked into a local `data/` directory. This was **not** an external reviewer replication or a clean `git clone` from a different machine. Numerical dependencies were supplied by the working environment (Python 3.13.5; NumPy 2.3.5, pandas 2.2.3, SciPy 1.17.0, Numba 0.65.1). Dependencies were not installed into a new virtual environment.

## Commands

```bash
python tests/test_compensator.py
python tests/test_causality.py
python src/counts/reproduce.py --data-dir data --out results/counts_recomputed.json
BTCUSDT_DATA_DIR=data python src/hawkes/run.py
BTCUSDT_DATA_DIR=data python src/continuous_time/validate.py
```

## Results

| Check | Outcome |
|---|---|
| Point-process compensator numerical checks | 3 passed |
| Chronology/scoring unit checks | 3 passed |
| Frozen-parameter count scores, Oct 23–27 (3 models × 5 dates) | **15/15 reproduced**, equal to archived `results/counts/phase4_results.json` scores at stored precision |
| Phase 6 Hawkes fits, Oct 23–25 (3 definitions × 3 dates) | **9/9 rows reproduced** |
| Phase 6 CSV comparison | All 14 non-key columns (counts, parameters, optimizer flags, likelihoods, rescaling statistics) matched; numerical maximum absolute difference **0.0** |
| Synthetic Hawkes recovery and real pilot diagnostics | Completed; three synthetic datasets and two date × four grouping configurations produced outputs |

### Interpretation

The reproducibility run confirms that the published code can reproduce the **archived evaluation numbers** with the original data, using the local Python environment. It does **not** establish correct model specification, statistical significance, stable branching parameters, external data robustness, or live trading profitability.

**Existing limitations remain:** the October 24 unique-timestamp fit hits `beta=2000/s` search bound; many Hawkes residual diagnostics reject; fitted parameters are highly sensitive to grouping; one synthetic optimizer fit returns `success=False` despite estimates close to the data-generating parameters. Previous model design was influenced by earlier exploration, so these are retrospective pilot evaluations. The frozen count replay does not independently reproduce original training.

## Remaining follow-up

- Independent clone on a second environment, including dependency installation from `requirements.txt`
- Optionally automate score comparisons as a regression test in CI
- Independent scientific review

**No raw exchange archives or credentials are published.**
