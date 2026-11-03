# Code and result audit — 2 November 2026

## Checked and reproduced

- Inspected the previous Phase 4 fitting/evaluation source and frozen-parameter JSON.
- Independently re-read the five October 23–27 ZIPs, verifying monotonic trade IDs/timestamps, UTC date bounds, and per-archive SHA-256 hashes.
- Recomputed 15 model/date NB mean log scores; all matched the saved results to <1e-9.
- Verified, using three unit tests, that changing observations at or after second t does not affect model features at t; and checked NB scores remain finite on simple fixtures.
- Training uses Poisson mean estimation and then separately estimates NB dispersion. This is **not** joint NB MLE.
- Validation dates were evaluated but **did not determine Phase 4 model choices** in the archived Phase 4 code. Describing them as calibration-selected would overstate it.
- Previously inspected later dates influenced the candidate model families, limiting claims of independent pre-registration.

## Important qualifications

- Events are distinct exchange-reported *timestamps*, not independently reconstructed market orders.
- EXP is a discrete-time exponential-history predictor, not a continuously fitted Hawkes model.
- The prior continuous-time fit has unstable decay parameters and lacks validated time-rescaling diagnostics.
- Residual overdispersion (Pearson 2.2–3.0 for AR) and zero-event miscalibration persist.
- Five-day sign-test p = .0625, and day bootstrap is weak with n=5.
- There is no trading signal, profit estimate, or causal excitation finding.

## Not independently proven here

- Cryptographic provenance of the historical moment each model family was selected.
- Completely independent rerun of initial September training; original fit code is provided for reference.
- An externally reviewed academic paper or peer-reviewed validation.
- Real-time execution or multi-exchange reproducibility.
