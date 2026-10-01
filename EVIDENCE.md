# Local build evidence

Measured on 2026-10-01, Python 3.12.10, Windows, CPU only.

- pytest: 29 passing tests.
- Installed CLI full 200-record fixtures/run/report demo: 0.662 seconds, below 5 seconds. This is one local measured run, not a forecast or time-saving claim.
- Exact totals: 200 records, 120 allowed, 80 denied, 240 committed UTF-8 bytes.
- Exact planted denied-id comparison: all 80 found, zero false positives on this synthetic dataset.
- All data in this trial are synthetic. No real client or Henry trial is claimed.
- Build and editable installation used local tools with no network calls.
- Five-record hand-written sample is in examples/tiny; expected 2 allowed, 3 denied, 2 bytes.

The full report can be reproduced with the README demo. Generated demo and local state are ignored by git. No publication was performed. Verdict awaits two weeks of real-use evidence.
