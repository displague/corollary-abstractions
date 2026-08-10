#!/usr/bin/env python3
"""Durable signing authority for conversation sessions.

ROADMAP-v0.7 item 2 asks for "durable key identity, rotation, and revocation
for ASK receipts and supersession records **without serializing ambient
secrets into public state**". This module is the whole of that authority, and
the split it enforces is the point:

* **Private, never serialized into a session file.** One or more *root keys*
  and a monotone per-scope *issue counter*. They live in a keyfile the runtime
  owns (`--keyfile`, ``CORO_SESSION_KEYFILE``, or ``.runtime/session-keys.json``,
  which `.gitignore` excludes). Nothing in this file ever appears in a session
  snapshot, a receipt, a question, or a binding.
* **Public, and deliberately unsigned as a whole.** The session snapshot:
  frame state, story beats, questions, bindings, receipts. Every element that
  carries authority carries *its own* signature and *its own* key id; the
  envelope carries none. See :mod:`session_state` for why an envelope MAC was
  refused rather than forgotten.

Threat model, stated so it can be attacked
------------------------------------------

**What forging a binding requires.** A binding's signature is
``HMAC-SHA256(K, payload)`` where ``K = HKDF(root_secret, salt=key_id,
info=domain|scope)``. The payload names the schema, the key id, the domain,
the scope, and every semantic field. So an attacker needs the *root secret* —
not the session file, not the ledger snapshot, not another session's key, and
not a different domain's key under the same root. Editing any signed field, or
relabelling a binding with a different ``key_id``, changes the payload and
invalidates the signature; relabelling it with a *revoked* key id is refused
before the signature is even checked.

**What revocation means.** :meth:`SessionKeyRing.revoke` marks a root key
unusable for both signing *and verification*. Every session, receipt, binding,
and ledger snapshot that was signed under it stops authenticating immediately,
with the named reason ``revoked-key-id``. Revocation is therefore a blunt,
session-killing instrument by design: it is the only remedy for the failure
mode this scheme is weakest against (below), and a remedy that left old
material verifiable would not be one.

**Rotation** is the non-destructive half. :meth:`SessionKeyRing.rotate` mints a
new root key and demotes the previous active one to ``retired``: retired keys
still *verify* (so live sessions survive a rotation) but never *sign* new
material. Because every signed record names its key id, a ring can hold many
generations at once and each record says which one to consult.

**Named weakness (registered as P-DS7 before this file existed).** The scheme
is weakest against **root-key file compromise**, not cryptanalysis. Every
session key in every scope descends from one root secret, so a reader of the
keyfile can mint any binding, for any owner, in any session, indistinguishable
from a real one — and revocation is the only response. Defence in depth here
(a KDF per owner, a hardware-held root, per-owner roots) is deliberately *not*
built: it would be untested ceremony around the same single file. The second
weakness is **session forking**: two processes may import the same ledger
snapshot at the same counter value and diverge. Refusing that would brick any
session that crashed between export and import, so the counter enforces
*monotonicity* (no rollback) and not *uniqueness* (no fork). Both are scoped
out in the open rather than papered over.

**What the counter buys.** A signature cannot tell a current snapshot from an
earlier, genuinely signed one — replaying a pre-supersession ledger is a valid
message out of order. :meth:`SessionKeyRing.issue_sequence` stamps every
exported snapshot with a strictly increasing number *kept in the private
keyfile*, and :meth:`SessionKeyRing.admit_sequence` refuses anything below the
high-water mark as ``ledger-rollback``. The public snapshot cannot lower the
counter because the counter is not in the public snapshot.
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path

#: Version tag mixed into every derived key and every signed payload. Bumping
#: it invalidates all existing material by construction, which is what a
#: schema change to the signing scheme should do.
KEY_SCHEMA = "corollary.session-keys/1"

#: Environment override for the runtime-owned keyfile.
KEYFILE_ENV = "CORO_SESSION_KEYFILE"

#: Default keyfile location, relative to the repository root. `.gitignore`
#: excludes `.runtime/`; the secret must never be a tracked artifact.
DEFAULT_KEYFILE = Path(".runtime") / "session-keys.json"


class RefusalReason(str, Enum):
    """Every way durable authority can be refused, by name.

    These strings are contract, not prose: the acceptance scenario and its
    tests assert on them, and a refusal that cannot name itself is exactly the
    silent failure this item exists to abolish.
    """

    #: The stated key id is not in this ring at all.
    UNKNOWN_KEY_ID = "unknown-key-id"
    #: The stated key id exists but has been revoked.
    REVOKED_KEY_ID = "revoked-key-id"
    #: The stated key id exists and is usable, but the MAC does not match.
    SIGNATURE_MISMATCH = "signature-mismatch"
    #: A ledger snapshot older than the highest one this ring ever issued.
    LEDGER_ROLLBACK = "ledger-rollback"
    #: A snapshot or session file written by an incompatible schema version.
    SCHEMA_MISMATCH = "schema-version-mismatch"
    #: A ledger snapshot restored into a session it was not issued for.
    SESSION_MISMATCH = "session-id-mismatch"
    #: A binding whose own signature does not authenticate.
    FORGED_BINDING = "binding-signature-invalid"
    #: A binding a newer answer replaced; provenance, no longer authority.
    SUPERSEDED_BINDING = "binding-superseded"
    #: A goal-local binding whose goal was reopened.
    EXPIRED_BINDING = "binding-goal-expired"
    #: A clarification request that was already answered once.
    CONSUMED_REQUEST = "request-already-consumed"
    #: A binding claiming a lifetime the protocol does not let a reply declare.
    UNDECLARABLE_LIFETIME = "undeclarable-lifetime"


class KeyStatus(str, Enum):
    """Whether a root key may sign, may only verify, or may do neither."""

    ACTIVE = "active"
    RETIRED = "retired"
    REVOKED = "revoked"

    @property
    def signs(self) -> bool:
        return self is KeyStatus.ACTIVE

    @property
    def verifies(self) -> bool:
        return self is not KeyStatus.REVOKED


class KeyRingRefusal(Exception):
    """A named refusal from the key ring. Never a bare ``ValueError``.

    Carrying :class:`RefusalReason` rather than only a message is what lets a
    caller (and a test) distinguish "this key was rotated out" from "this
    ledger was rolled back" without string-matching English.
    """

    def __init__(self, reason: RefusalReason, detail: str = "") -> None:
        self.reason = reason
        self.detail = detail
        message = reason.value if not detail else f"{reason.value}: {detail}"
        super().__init__(message)


@dataclass(frozen=True)
class RootKey:
    """One generation of signing authority.

    ``secret`` is 32 bytes of ``secrets.token_bytes``. It is written to the
    private keyfile and to nowhere else; :meth:`public_record` is what any
    non-secret listing gets.
    """

    key_id: str
    secret: bytes
    status: KeyStatus
    created: str

    def public_record(self) -> dict[str, str]:
        return {
            "key_id": self.key_id,
            "status": self.status.value,
            "created": self.created,
        }


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def hkdf_sha256(secret: bytes, salt: bytes, info: bytes, length: int = 32) -> bytes:
    """RFC 5869 HKDF over SHA-256, in the twelve lines it actually is.

    Written out rather than pulled from a dependency because the whole point
    of this item is that the derivation is auditable: extract once with the
    salt, expand with the info string, take ``length`` bytes. The salt is the
    key id and the info is ``domain|scope``, so two domains or two scopes under
    one root are cryptographically unrelated even though one secret backs them.
    """

    if length < 1 or length > 255 * 32:
        raise ValueError("hkdf length out of range")
    prk = hmac.new(salt, secret, hashlib.sha256).digest()
    okm = b""
    block = b""
    counter = 1
    while len(okm) < length:
        block = hmac.new(
            prk, block + info + bytes([counter]), hashlib.sha256
        ).digest()
        okm += block
        counter += 1
    return okm[:length]


class SessionKeyRing:
    """Root keys plus the monotone counters, backed by a private keyfile.

    An *ephemeral* ring (:meth:`ephemeral`) has one active key, no file, and no
    persistence: it reproduces exactly the pre-item-2 behaviour in which a
    verifier's authority dies with the process. That is the default everywhere
    a caller does not ask for durability, which is why
    ``test_second_verifier_cannot_accept_first_verifiers_question`` still
    passes: two default verifiers hold two unrelated ephemeral roots. A
    process-global default would have quietly broken that test's whole claim.
    """

    def __init__(
        self,
        keys: dict[str, RootKey],
        active_key_id: str,
        counters: dict[str, int] | None = None,
        path: Path | None = None,
        superseded: dict[str, tuple[str, ...]] | None = None,
    ) -> None:
        if active_key_id not in keys:
            raise ValueError("active key id must be present in the ring")
        self._keys = dict(keys)
        self._active_key_id = active_key_id
        self._counters: dict[str, int] = dict(counters or {})
        self._superseded: dict[str, set[str]] = {
            scope: set(ids) for scope, ids in (superseded or {}).items()
        }
        self.path = path

    # -- construction ----------------------------------------------------

    @staticmethod
    def _mint(prefix: str = "k") -> RootKey:
        return RootKey(
            key_id=f"{prefix}-{secrets.token_hex(8)}",
            secret=secrets.token_bytes(32),
            status=KeyStatus.ACTIVE,
            created=_now(),
        )

    @classmethod
    def ephemeral(cls) -> "SessionKeyRing":
        """A process-local ring: one key, no file, gone at exit."""

        key = cls._mint("eph")
        return cls({key.key_id: key}, key.key_id, {}, None)

    @classmethod
    def open(cls, path: Path | str | None = None) -> "SessionKeyRing":
        """Load the runtime-owned keyfile, creating it on first use.

        Resolution order: explicit ``path``, then ``CORO_SESSION_KEYFILE``,
        then ``.runtime/session-keys.json`` under the current directory. The
        file is created with owner-only permissions where the platform honours
        them; on Windows ``chmod`` is advisory, which is recorded here rather
        than claimed away.
        """

        resolved = Path(
            path
            if path is not None
            else os.environ.get(KEYFILE_ENV, DEFAULT_KEYFILE)
        )
        if resolved.exists():
            return cls._read(resolved)
        key = cls._mint()
        ring = cls({key.key_id: key}, key.key_id, {}, resolved, {})
        ring.save()
        return ring

    @classmethod
    def _read(cls, path: Path) -> "SessionKeyRing":
        raw = json.loads(path.read_text(encoding="utf-8"))
        if raw.get("schema") != KEY_SCHEMA:
            raise KeyRingRefusal(
                RefusalReason.SCHEMA_MISMATCH,
                f"{path} declares {raw.get('schema')!r}, expected {KEY_SCHEMA!r}",
            )
        keys = {
            record["key_id"]: RootKey(
                key_id=record["key_id"],
                secret=base64.b64decode(record["secret"]),
                status=KeyStatus(record["status"]),
                created=record["created"],
            )
            for record in raw["keys"]
        }
        return cls(
            keys,
            raw["active_key_id"],
            raw.get("counters", {}),
            path,
            {
                scope: tuple(ids)
                for scope, ids in raw.get("superseded", {}).items()
            },
        )

    def save(self) -> None:
        """Write the private state back, atomically where the OS allows it."""

        if self.path is None:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "schema": KEY_SCHEMA,
            "active_key_id": self._active_key_id,
            "keys": [
                {
                    "key_id": key.key_id,
                    "secret": base64.b64encode(key.secret).decode("ascii"),
                    "status": key.status.value,
                    "created": key.created,
                }
                for key in self._keys.values()
            ],
            "counters": dict(sorted(self._counters.items())),
            "superseded": {
                scope: sorted(ids)
                for scope, ids in sorted(self._superseded.items())
            },
        }
        temporary = self.path.with_suffix(self.path.suffix + ".tmp")
        temporary.write_text(
            json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        os.replace(temporary, self.path)
        try:
            self.path.chmod(0o600)
        except (OSError, NotImplementedError):
            # Windows ignores POSIX mode bits. Documented, not pretended away.
            pass

    # -- identity, rotation, revocation ----------------------------------

    @property
    def active_key_id(self) -> str:
        return self._active_key_id

    def key_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._keys))

    def status(self, key_id: str) -> KeyStatus:
        key = self._keys.get(key_id)
        if key is None:
            raise KeyRingRefusal(RefusalReason.UNKNOWN_KEY_ID, key_id)
        return key.status

    def public_records(self) -> tuple[dict[str, str], ...]:
        return tuple(key.public_record() for key in self._keys.values())

    def rotate(self) -> str:
        """Mint a new active key and retire the previous one.

        Retired, not revoked: material signed under the old generation must
        keep verifying or a rotation would be indistinguishable from an
        outage. Rotation changes who *signs*; revocation changes who
        *verifies*.
        """

        previous = self._keys[self._active_key_id]
        self._keys[previous.key_id] = replace(previous, status=KeyStatus.RETIRED)
        fresh = self._mint()
        self._keys[fresh.key_id] = fresh
        self._active_key_id = fresh.key_id
        self.save()
        return fresh.key_id

    def revoke(self, key_id: str) -> None:
        """Make a generation unusable for signing *and* verification.

        Revoking the active key leaves the ring without a signer; the caller
        must :meth:`rotate` first, and attempting to sign under a revoked key
        raises rather than silently falling back to another generation.
        """

        key = self._keys.get(key_id)
        if key is None:
            raise KeyRingRefusal(RefusalReason.UNKNOWN_KEY_ID, key_id)
        self._keys[key_id] = replace(key, status=KeyStatus.REVOKED)
        self.save()

    # -- derivation ------------------------------------------------------

    def derive(self, key_id: str, scope: str, domain: str) -> bytes:
        """One purpose-bound signing key.

        ``scope`` names *whose* material this is (``session:<id>`` or
        ``owner:<name>``) and ``domain`` names *what kind* (``question``,
        ``reply``, ``binding``, ``receipt``, ``ledger``). Both are inputs to
        the KDF **and** are repeated inside every signed payload. The
        duplication is deliberate: the KDF makes cross-scope reuse produce an
        unrelated key, and the payload makes a scope relabelling visible even
        if some future caller derives carelessly.
        """

        key = self._keys.get(key_id)
        if key is None:
            raise KeyRingRefusal(RefusalReason.UNKNOWN_KEY_ID, key_id)
        if not key.status.verifies:
            raise KeyRingRefusal(RefusalReason.REVOKED_KEY_ID, key_id)
        info = f"{KEY_SCHEMA}|{domain}|{scope}".encode("utf-8")
        return hkdf_sha256(key.secret, key_id.encode("utf-8"), info)

    def signing_key_id(self) -> str:
        """The generation new material must be signed under."""

        if not self._keys[self._active_key_id].status.signs:
            raise KeyRingRefusal(
                RefusalReason.REVOKED_KEY_ID,
                f"active key {self._active_key_id} cannot sign; rotate first",
            )
        return self._active_key_id

    # -- monotone counters (anti-rollback) --------------------------------

    def high_water(self, scope: str) -> int:
        return self._counters.get(scope, 0)

    def issue_sequence(self, scope: str) -> int:
        """Stamp a new snapshot. Strictly increasing, persisted immediately."""

        nxt = self.high_water(scope) + 1
        self._counters[scope] = nxt
        self.save()
        return nxt

    def admit_sequence(self, scope: str, sequence: int) -> None:
        """Refuse a snapshot older than the newest this ring ever issued.

        ``>=`` rather than ``==`` on purpose. Equality would forbid restoring
        the snapshot you just wrote, and would forbid restoring the same
        snapshot twice after a crash — both legitimate. What it costs is
        stated in the module docstring: this admits *rollback* refusal, not
        *fork* refusal.
        """

        mark = self.high_water(scope)
        if sequence < mark:
            raise KeyRingRefusal(
                RefusalReason.LEDGER_ROLLBACK,
                f"{scope} snapshot sequence {sequence} is behind {mark}",
            )
        if sequence > mark:
            self._counters[scope] = sequence
            self.save()


    # -- cross-session supersession ---------------------------------------

    def record_superseded(self, scope: str, request_id: str) -> None:
        """Retire an owner-scoped (``durable``) answer, permanently.

        Session-scoped supersession lives in the verifier and travels in a
        :class:`retrieval.LedgerSnapshot`, because a session has a snapshot to
        travel in. A ``durable`` binding has no such carrier by definition: it
        is valid in conversations that do not exist yet, so the record that
        retires it has to live somewhere those conversations will look. The
        keyring is the only durable private state in the design, so it is
        where this goes.

        Found by :meth:`test_durable_supersession_is_filed_under_the_owner_scope`
        while probing this item's own fixes -- before it, a durable answer
        replaced in one session came back to life in the next, because the
        replacement was recorded on a verifier instance that the next session
        never met. That is a wrong-answer bug, not a cache miss.
        """

        self._superseded.setdefault(scope, set()).add(request_id)
        self.save()

    def is_superseded(self, scope: str, request_id: str) -> bool:
        return request_id in self._superseded.get(scope, ())

    def superseded_scopes(self) -> tuple[str, ...]:
        return tuple(sorted(self._superseded))


def session_scope(session_id: str) -> str:
    """Scope for material that dies with one conversation."""

    return f"session:{session_id}"


def owner_scope(owner: str) -> str:
    """Scope for material that outlives any one conversation."""

    return f"owner:{owner}"
