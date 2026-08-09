#!/usr/bin/env python3
"""Read-only Open English WordNet JSON index for symbolic retrieval.

The upstream archive remains external. Loading records its SHA-256 for
provenance, validates the small portion of the JSON contract this adapter
consumes, and exposes synsets by entry lemma. It makes no proof claim: lexical
records enter the retrieval ladder at ``empirical``.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType
from typing import Mapping
from zipfile import BadZipFile, ZipFile


def lemma_key(value: str) -> str:
    return " ".join(value.replace("_", " ").strip().casefold().split())


@dataclass(frozen=True)
class WordNetSynset:
    synset_id: str
    members: tuple[str, ...]
    definitions: tuple[str, ...]
    examples: tuple[str, ...]
    relations: tuple[tuple[str, tuple[str, ...]], ...]
    part_of_speech: str


@dataclass(frozen=True)
class WordNetIndex:
    """Digest-attributed lexical graph loaded from one OEWN JSON archive."""

    archive: Path
    archive_sha256: str
    synsets: Mapping[str, WordNetSynset]
    lemma_synsets: Mapping[str, tuple[str, ...]]

    def __post_init__(self) -> None:
        # The index participates in authoritative-store membership checks. A
        # frozen dataclass around mutable dictionaries is not frozen enough.
        object.__setattr__(self, "synsets", MappingProxyType(dict(self.synsets)))
        object.__setattr__(
            self,
            "lemma_synsets",
            MappingProxyType(dict(self.lemma_synsets)),
        )

    @classmethod
    def load(cls, archive: Path) -> "WordNetIndex":
        archive = archive.resolve()
        digest = hashlib.sha256(archive.read_bytes()).hexdigest()
        synsets: dict[str, WordNetSynset] = {}
        lemma_ids: dict[str, set[str]] = {}
        try:
            with ZipFile(archive) as zipped:
                names = zipped.namelist()
                entry_names = sorted(
                    name for name in names if Path(name).name.startswith("entries-")
                )
                synset_names = sorted(
                    name
                    for name in names
                    if name not in entry_names and Path(name).name != "frames.json"
                )
                if not entry_names or not synset_names:
                    raise ValueError(
                        "WordNet archive must contain entries-*.json and synset JSON"
                    )

                for name in synset_names:
                    payload = _json_object(zipped, name)
                    for synset_id, raw in payload.items():
                        if synset_id in synsets:
                            raise ValueError(
                                f"duplicate WordNet synset id {synset_id!r}"
                            )
                        if not isinstance(raw, dict):
                            raise ValueError(f"{name}:{synset_id} must be an object")
                        members = _string_tuple(raw.get("members"), name, synset_id)
                        definitions = _string_tuple(
                            raw.get("definition"), name, synset_id
                        )
                        examples = _example_tuple(
                            raw.get("example", []), name, synset_id
                        )
                        part_of_speech = raw.get("partOfSpeech")
                        if not isinstance(part_of_speech, str) or not part_of_speech:
                            raise ValueError(
                                f"{name}:{synset_id}.partOfSpeech must be a string"
                            )
                        reserved = {
                            "definition",
                            "example",
                            "ili",
                            "members",
                            "partOfSpeech",
                            "source",
                            "wikidata",
                        }
                        relations = tuple(
                            sorted(
                                (
                                    relation,
                                    _string_tuple(targets, name, synset_id),
                                )
                                for relation, targets in raw.items()
                                if relation not in reserved
                            )
                        )
                        synsets[synset_id] = WordNetSynset(
                            synset_id,
                            members,
                            definitions,
                            examples,
                            relations,
                            part_of_speech,
                        )

                for name in entry_names:
                    payload = _json_object(zipped, name)
                    for lemma, by_pos in payload.items():
                        if not isinstance(lemma, str) or not isinstance(by_pos, dict):
                            raise ValueError(f"{name} entry values must be objects")
                        for pos_record in by_pos.values():
                            if not isinstance(pos_record, dict):
                                raise ValueError(f"{name}:{lemma} POS must be an object")
                            senses = pos_record.get("sense", [])
                            if not isinstance(senses, list):
                                raise ValueError(
                                    f"{name}:{lemma}.sense must be a list"
                                )
                            for sense in senses:
                                if not isinstance(sense, dict) or not isinstance(
                                    sense.get("synset"), str
                                ):
                                    raise ValueError(
                                        f"{name}:{lemma} sense must name a synset"
                                    )
                                synset_id = sense["synset"]
                                if synset_id not in synsets:
                                    raise ValueError(
                                        f"{name}:{lemma} references missing synset "
                                        f"{synset_id!r}"
                                    )
                                lemma_ids.setdefault(lemma_key(lemma), set()).add(
                                    synset_id
                                )
        except BadZipFile as exc:
            raise ValueError(f"WordNet archive is not a valid zip: {archive}") from exc

        return cls(
            archive,
            digest,
            synsets,
            {key: tuple(sorted(ids)) for key, ids in lemma_ids.items()},
        )

    def lookup(self, lemma: str) -> tuple[WordNetSynset, ...]:
        return tuple(
            self.synsets[synset_id]
            for synset_id in self.lemma_synsets.get(lemma_key(lemma), ())
        )


def _json_object(zipped: ZipFile, name: str) -> dict:
    try:
        payload = json.loads(zipped.read(name))
    except (KeyError, json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError(f"invalid WordNet JSON member {name!r}") from exc
    if not isinstance(payload, dict):
        raise ValueError(f"WordNet JSON member {name!r} must be an object")
    return payload


def _string_tuple(value: object, name: str, synset_id: str) -> tuple[str, ...]:
    if not isinstance(value, list) or not all(
        isinstance(item, str) and item for item in value
    ):
        raise ValueError(f"{name}:{synset_id} values must be non-empty strings")
    return tuple(value)


def _example_tuple(value: object, name: str, synset_id: str) -> tuple[str, ...]:
    if not isinstance(value, list):
        raise ValueError(f"{name}:{synset_id}.example must be a list")
    examples: list[str] = []
    for item in value:
        if isinstance(item, str) and item:
            examples.append(item)
            continue
        if (
            isinstance(item, dict)
            and isinstance(item.get("text"), str)
            and item["text"]
        ):
            source = item.get("source")
            examples.append(
                item["text"]
                if not isinstance(source, str) or not source
                else f"{item['text']} [{source}]"
            )
            continue
        raise ValueError(
            f"{name}:{synset_id}.example entries must be strings or text objects"
        )
    return tuple(examples)
