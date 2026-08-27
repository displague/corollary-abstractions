#!/usr/bin/env python3
"""B5's accept-all stub: the capability-blind control.

`docs/DESIGN-cold-receipt.md` §7 specifies it exactly — *"for Lean kinds, a
program that prints nothing and exits 0"* — and §13 makes it the one arm that
can void every kind at once. It is written to be able to.

**Disclosed weakness in the substitution.** §7 asks for a stub *"of the same
name and interface"*. This stub matches the **interface** — the same argv
shape (a probe path appended to a checker prefix), the same cwd, the same
exit-code contract — but not the **name**: it is invoked through an
interpreter rather than as a file called `lean.exe`, because producing a
same-named native executable needs a toolchain this workstation does not
have. The substitution is therefore weaker than the design's wording, and
that is recorded here rather than glossed.
"""

import sys

if __name__ == "__main__":
    # Prints nothing, accepts everything.
    sys.exit(0)
