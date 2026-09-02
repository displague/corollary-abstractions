# H-P1 run 1, superseded

`house_rules_verdicts.run1.json` and `house_rules_receipts.run1.json` are the
two declared outputs of the **first** registered H-P1 run, written at commit
`2ac8c9f` ([H-P1] The registered run: twelve green, the sentence unfired,
R-H1 licensed) by `scripts/run_house_rules_gates.py` as that commit froze it.

They are **retained and never re-scored.** An independent adversarial review
of the freeze (`27d358d`) and the run (`2ac8c9f`) reproduced every number in
them and returned MERGE AFTER FIXES. Nothing in these two files is withdrawn
as arithmetic; what the review found is that some of the checks behind the
numbers could not have failed, that some scope was undisclosed, and that one
of the vectors a gate reported as stopped was present in the committed tree
at the time. Specifically:

* **F1** — B3 executes no mutant. The 32 mutants are prose descriptions and
  the id-to-detector map was authored in the runner and never checked against
  each mutant's sealed `stopper_mechanism`.
* **F2** — two of B3's detectors could not fail: `name_sweep` planted a name
  in a temporary directory and found it again (seven mutants), and
  `checker_inputs_exclude_the_runs_outputs` asserted an absence true of any
  module (one mutant).
* **F3** — B9's control family was unregistered and structurally unable to
  fire: its ceiling on the 19-row scored half is 0.736842 against a threshold
  of 0.784211, and the fitted rule predicted one class for every scored row.
* **F4** — the served `declare` grammar example carried an ADMITTED fixture
  symbol from H-P0 through this run, which is b3-m08's own vector sitting in
  the committed tree while run 1 scored that mutant STOPPED.

Run 2 supersedes these files at `experiments/house_rules_verdicts.json` and
`experiments/house_rules_receipts.json`, scored on a tree where the leak is
repaired, the two dead detectors are repaired or retired, and B3's and B9's
disclosures are published. The preregistration carries the five dated
amendments that record all of it (`amd-2026-09-02-*`), each stating that it
was authored AFTER run 1's score and that it loosens nothing.

**Run 1's twelve-green table stands as the record of what the run-1 runner
scored.** It is not evidence that the capability was contained, because two
of the checks behind B3 could not have said otherwise; it is the record that
those checks, as written, passed. That distinction is the reason the files
are kept rather than deleted.
