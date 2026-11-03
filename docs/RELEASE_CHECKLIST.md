# Release and reproducibility checklist

- [x] Consolidated count-model and continuous-time Hawkes analyses, with clear distinction between them.
- [x] Included source code, frozen parameters, saved outputs, figures, and working paper.
- [x] Verified 6 numerical tests (3 compensator + 3 chronology/scoring).
- [x] Reproduced all 15 archived model/date count scores across October 23–27 using the original ZIPs and the packaged evaluator.
- [x] Reproduced all 9 Hawkes Phase 6 fits and all archived summary fields using the original ZIPs and the packaged code.
- [x] Reran synthetic Hawkes parameter recovery and pilot timestamp-grouping diagnostics.
- [x] Produced and visually inspected four-page working-paper PDF in initial package preparation.
- [x] Excluded raw data ZIPs and resume files.
- [x] Obtained user approval and published the public GitHub repository.
- [x] Moved research files to repository root.
- [ ] Independent fresh clone on a different machine/environment with dependency installation.
- [ ] Independent external code and scientific review.

See `docs/reproducibility_2026-11-03.md` for verification scope, commands and unresolved warnings.
Do not claim a validated causal Hawkes mechanism, peer-reviewed results, or investable trading alpha.
