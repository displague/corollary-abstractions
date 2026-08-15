# Algorithms derived extract — attribution

`extract.json` in this directory is a **derived work**: eight functions
sliced from four TheAlgorithms/Python maths files by
`scripts/ingest_algorithms.py` —

- `maths/greatest_common_divisor.py`: `greatest_common_divisor`, `gcd_by_iterative` (`main()` dropped; it still uses Python-2 `except` syntax)
- `maths/factorial.py`: `factorial`, `factorial_recursive`
- `maths/double_factorial.py`: `double_factorial_recursive`, `double_factorial_iterative`
- `maths/binary_exponentiation.py`: `binary_exp_recursive`, `binary_exp_iterative`

The two modular exponentiation functions in `binary_exponentiation.py`
are declined this slice (docs/DESIGN-programming-second-wave.md §3) and
are not in the extract.

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

Stein's binary GCD, used in the first wave as the name-similar non-twin, is
**first-party** and is not part of this extract. See
`docs/DESIGN-programming-discipline.md` §3. Double factorial is the
ingested analog of that foil (token `factorial`, different recurrence).
