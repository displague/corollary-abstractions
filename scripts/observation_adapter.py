#!/usr/bin/env python3
"""The first *external* retrieval source: a declared local observation folder.

ROADMAP-v0.7 item 6 asks for "one external source adapter whose returned
observations retain source, timestamp, query, and epistemic rung". This is
that adapter, and it is deliberately offline: it reads a caller-declared
directory of JSON observation files. Nothing here opens a socket.

Why a filesystem source counts as external, honestly stated: it is *not* one
of the five committed stores, it is *not* regenerated from the seeds, and
``scripts/check_regeneration.py`` says nothing about it. Its records therefore
carry no project authority at all — they are somebody's notes that happened to
be readable. What the adapter provides is the **contract** the network version
would need: every returned observation names where it came from, when the
source claims it was recorded, when this process fetched it, which query
fetched it, and at which epistemic rung it enters. A successful fetch proves
what was fetched, not that its content is true.

The rung ceiling is enforced here rather than downstream. An observation file
may declare ``conjectured`` or ``empirical``; any stronger label is refused at
load with the offending file named. There is no code path by which an external
observation becomes ``derived``, ``formal`` or ``proven``, and none by which it
can be cited in ``verified_by``.

The ``ObservationSource`` protocol below is the typed handle the interactive
harness's subsystem registry (``docs/DESIGN-interactive-harness.md`` §3.2)
wraps: ``probe()`` is the boot probe, ``fetch()`` is the registered path.
Per that section's probe semantics, a passing probe asserts liveness only and
never raises any record's rung.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Protocol, runtime_checkable

from text_keys import alias_covered, exact_key, query_tokens


#: External observations may never enter above ``empirical``. This is the
#: whole trust model in one tuple: unverified outside text is at best a
#: reported observation, and more often a conjecture.
EXTERNAL_RUNG_CEILING = ("conjectured", "empirical")


@dataclass(frozen=True)
class SourceProbe:
    """Liveness of one external source. Not an epistemic claim.

    ``docs/DESIGN-interactive-harness.md`` §3.2: "A probe never raises any
    verdict's epistemic rung, and the boot matrix is not evidence of verifier
    soundness." ``available`` means the adapter could read its declared root,
    nothing more.
    """

    source_id: str
    available: bool
    detail: str
    record_count: int = 0


@dataclass(frozen=True)
class Observation:
    """One external record with its complete provenance quadruple.

    ``source`` / ``recorded_at`` / ``query`` / ``rung`` are the four fields
    ROADMAP-v0.7 item 6 requires be retained. ``fetched_at`` and ``digest``
    are added because "what was fetched" is only checkable if the transaction
    time and the bytes are pinned too.
    """

    observation_id: str
    source: str
    query: str
    recorded_at: str
    fetched_at: str
    rung: str
    title: str
    text: str
    keywords: tuple[str, ...]
    digest: str
    location: str

    @property
    def provenance(self) -> tuple[str, ...]:
        """Stable source_ids for the retrieval record minted from this."""

        return (
            f"source:{self.source}",
            f"observation:{self.observation_id}",
            f"recorded_at:{self.recorded_at}",
            f"fetched_at:{self.fetched_at}",
            f"query:{exact_key(self.query)}",
            f"rung:{self.rung}",
            f"sha256:{self.digest}",
        )


@runtime_checkable
class ObservationSource(Protocol):
    """Typed handle for one registered external source.

    This is the item-6 "typed protocols" seam and the harness registry's
    ``adapter_factory`` shape at once — one vocabulary, not two. A source may
    only be consulted through ``fetch``; there is no ambient discovery and no
    "try things until something answers" path.
    """

    source_id: str

    def probe(self) -> SourceProbe: ...

    def fetch(self, key: str) -> tuple[Observation, ...]: ...


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class LocalObservationAdapter:
    """Read a declared directory of JSON observation files, read-only.

    Each ``*.json`` file holds one object::

        {
          "observation_id": "note.tide_gauge_2026",
          "title": "Tide gauge reading",
          "text": "...",
          "keywords": ["tide", "gauge"],
          "recorded_at": "2026-07-01T00:00:00+00:00",
          "epistemic_rung": "empirical"
        }

    Malformed files fail loudly at construction with the file named: an
    external source that silently drops records is worse than one that is
    absent, because the caller cannot tell a miss from a swallowed parse
    error. This mirrors the WordNet adapter's named-archive rule.
    """

    def __init__(
        self,
        root: Path,
        source_id: str | None = None,
        clock: Callable[[], str] = _utc_now,
    ):
        self.root = Path(root)
        self.source_id = source_id or f"local.observations:{self.root.name}"
        self._clock = clock
        self._records: tuple[dict[str, object], ...] = ()
        self._error = ""
        if not self.root.is_dir():
            self._error = f"observation root is not a directory: {self.root}"
            return
        self._records = tuple(self._load_all())

    def _load_all(self) -> list[dict[str, object]]:
        records: list[dict[str, object]] = []
        seen: set[str] = set()
        for path in sorted(self.root.glob("*.json")):
            # One read: the digest must cover the exact bytes that were
            # parsed, not a second read that could differ.
            raw = path.read_bytes()
            try:
                payload = json.loads(raw.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as exc:
                raise ValueError(f"invalid observation JSON: {path}") from exc
            if not isinstance(payload, dict):
                raise ValueError(f"observation file must be an object: {path}")
            observation_id = payload.get("observation_id")
            title = payload.get("title")
            text = payload.get("text")
            recorded_at = payload.get("recorded_at")
            rung = payload.get("epistemic_rung")
            for name, value in (
                ("observation_id", observation_id),
                ("title", title),
                ("text", text),
                ("recorded_at", recorded_at),
                ("epistemic_rung", rung),
            ):
                if not isinstance(value, str) or not value.strip():
                    raise ValueError(
                        f"observation {path} needs a non-empty string {name!r}"
                    )
            assert isinstance(recorded_at, str) and isinstance(rung, str)
            try:
                datetime.fromisoformat(recorded_at)
            except ValueError as exc:
                raise ValueError(
                    f"observation {path} has a non-ISO-8601 recorded_at "
                    f"{recorded_at!r}"
                ) from exc
            if rung not in EXTERNAL_RUNG_CEILING:
                # The laundering attempt this whole module exists to refuse:
                # an outside file cannot declare itself derived/formal/proven.
                raise ValueError(
                    f"observation {path} declares epistemic_rung {rung!r}; "
                    "external observations may not exceed "
                    f"{EXTERNAL_RUNG_CEILING[-1]!r}"
                )
            keywords = payload.get("keywords", [])
            if not isinstance(keywords, list) or not all(
                isinstance(word, str) and word for word in keywords
            ):
                raise ValueError(
                    f"observation {path} keywords must be non-empty strings"
                )
            assert isinstance(observation_id, str)
            if observation_id in seen:
                raise ValueError(
                    f"duplicate observation_id {observation_id!r} at {path}"
                )
            seen.add(observation_id)
            records.append(
                {
                    "observation_id": observation_id,
                    "title": title,
                    "text": text,
                    "keywords": tuple(keywords),
                    "recorded_at": recorded_at,
                    "rung": rung,
                    "digest": hashlib.sha256(raw).hexdigest(),
                    "location": path.name,
                }
            )
        return records

    def probe(self) -> SourceProbe:
        if self._error:
            return SourceProbe(self.source_id, False, self._error)
        return SourceProbe(
            self.source_id,
            True,
            f"read {len(self._records)} observation file(s) from {self.root}",
            len(self._records),
        )

    def _aliases(self, record: dict[str, object]) -> tuple[str, ...]:
        keywords = record["keywords"]
        assert isinstance(keywords, tuple)
        return (
            str(record["observation_id"]),
            str(record["title"]),
            *(str(word) for word in keywords),
        )

    def fetch(self, key: str) -> tuple[Observation, ...]:
        """Return every observation whose aliases match ``key``, closed-form.

        The match relation is exactly the store's: alias equality, or every
        query token covering some alias token. Using the same closed form
        means an external record can never be reached by a *looser* rule than
        a committed one — no privileged fuzzy path for outside data.
        """

        if self._error:
            return ()
        tokens = query_tokens(key)
        fetched_at = self._clock()
        matched: list[Observation] = []
        for record in self._records:
            aliases = self._aliases(record)
            hit = any(exact_key(key) == exact_key(alias) for alias in aliases)
            if not hit and tokens:
                hit = any(
                    alias_covered(tokens, query_tokens(alias)) for alias in aliases
                )
            if not hit:
                continue
            keywords = record["keywords"]
            assert isinstance(keywords, tuple)
            matched.append(
                Observation(
                    observation_id=str(record["observation_id"]),
                    source=self.source_id,
                    query=key,
                    recorded_at=str(record["recorded_at"]),
                    fetched_at=fetched_at,
                    rung=str(record["rung"]),
                    title=str(record["title"]),
                    text=str(record["text"]),
                    keywords=tuple(str(word) for word in keywords),
                    digest=str(record["digest"]),
                    location=str(record["location"]),
                )
            )
        return tuple(matched)
