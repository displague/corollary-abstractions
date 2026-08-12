"""Sandboxed unittest runner for external_verifier's python-tests backend.

Usage (subprocess only, `python -I`): _verifier_sandbox.py <sandbox_dir>
<candidate_path> <tests_path>.

First act: install a CPython audit hook that refuses, for the remainder of
the process, (1) socket address resolution/connection/binding, (2) subprocess
and exec/spawn/fork, and (3) file opens for writing outside <sandbox_dir>.
Audit hooks cannot be uninstalled, so candidate code cannot shed the hook.

This is a DISCIPLINE boundary, not a security boundary: ctypes or a hostile
C extension bypasses the audit layer entirely. The verdict that records a run
under this runner says exactly that (see external_verifier.check_python_tests
`checks`), and nothing may read a PASS here as sandbox-proof of anything
beyond "the pinned tests passed without tripping the hook".
"""

from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

_REFUSED_PREFIXES = (
    "socket.getaddrinfo",
    "socket.gethostbyname",
    "socket.connect",
    "socket.bind",
    "socket.sendto",
    "subprocess.Popen",
    "os.system",
    "os.exec",
    "os.spawn",
    "os.posix_spawn",
    "os.fork",
)

_WRITE_MODES = frozenset("wax+")

# The `open` audit event carries (path, mode, flags), and the MODE IS None
# for every low-level open: `os.open`, `_io.FileIO`, and — the reason this
# exists — CPython's own bytecode cache writer. Reading only the mode let a
# sandboxed check write `__pycache__` into the repository while the verdict
# claimed writes outside the sandbox were refused. The flags are the second
# reading of the same event, and both are consulted now.
_WRITE_FLAGS = (
    os.O_WRONLY | os.O_RDWR | os.O_APPEND | os.O_CREAT | os.O_TRUNC
)


class SandboxRefusal(RuntimeError):
    pass


def _install_hook(sandbox_root: Path) -> None:
    resolved_root = sandbox_root.resolve()

    def hook(event: str, args: tuple) -> None:
        for prefix in _REFUSED_PREFIXES:
            if event.startswith(prefix):
                raise SandboxRefusal(f"sandbox refused audit event {event}")
        if event == "open":
            target, mode = args[0], args[1]
            flags = args[2] if len(args) > 2 else None
            writing = mode is not None and any(
                c in _WRITE_MODES for c in str(mode)
            )
            if not writing and isinstance(flags, int):
                writing = bool(flags & _WRITE_FLAGS)
            if not writing:
                return
            try:
                resolved = Path(target).resolve()
            except (TypeError, ValueError, OSError):
                # A non-path target (fd) is out of scope for this boundary.
                return
            if not resolved.is_relative_to(resolved_root):
                raise SandboxRefusal(
                    f"sandbox refused write outside sandbox: {resolved}"
                )

    sys.addaudithook(hook)


def main() -> int:
    sandbox_dir, candidate, tests = sys.argv[1], sys.argv[2], sys.argv[3]
    candidate_path = Path(candidate).resolve()
    tests_path = Path(tests).resolve()
    # Imports resolve against the pinned modules' directories, nothing else
    # is added; -I already stripped cwd and site customisations.
    for parent in {str(candidate_path.parent), str(tests_path.parent)}:
        if parent not in sys.path:
            sys.path.insert(0, parent)
    _install_hook(Path(sandbox_dir))

    loader = unittest.TestLoader()
    suite = loader.discover(
        str(tests_path.parent), pattern=tests_path.name, top_level_dir=None
    )
    if suite.countTestCases() == 0:
        print(f"no tests discovered in {tests_path}", file=sys.stderr)
        return 2
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
