# Algorithms derived extract — attribution

`extract.json` in this directory is a **derived work**: the two Euclidean
GCD implementations (`greatest_common_divisor`, `gcd_by_iterative`) sliced
from TheAlgorithms/Python `maths/greatest_common_divisor.py` by
`scripts/ingest_algorithms.py`. The source file's `main()` is dropped
(it still uses Python-2 `except` syntax and is not part of the algorithm).

- **Upstream:** TheAlgorithms/Python — <https://github.com/TheAlgorithms/Python>
- **Commit pinned:** `f5988cc09713315817df6a7e327e258013a94440`
  (per-file SHA-256 in `data_sources/manifest.json`).
- **License:** MIT — the pinned `LICENSE.md` is vendored alongside this
  file as `LICENSE`.

**Required citation** (MIT attribution; carried verbatim from the
manifest entry and load-bearing for any reuse of this extract):

> TheAlgorithms and contributors. TheAlgorithms/Python. MIT License.
> https://github.com/TheAlgorithms/Python
> (commit f5988cc09713315817df6a7e327e258013a94440).

Stein's binary GCD, used in this slice as the name-similar non-twin, is
**first-party** and is not part of this extract. See
`docs/DESIGN-programming-discipline.md` §3.
