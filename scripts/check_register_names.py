"""Decompose canonical register names under the register naming rules.

The rules are in `architecture/naming.md` ("Register and field names"); the
vocabulary is `architecture/fixtures/register-name-vocabulary.csv`. Every
canonical name on a covered surface is split into vocabulary words (compound
terms matched longest first) and each word is given a role from its position
in the order of the parts:

    [purpose]_[attribute][subject][index]_[place]_[attribute][object][part]
    _[predicate]_[bound]_[period]_[manner]_[at_condition]

A name fails when a token has no vocabulary entry, when a word is a forbidden
synonym, when no role assignment follows that order, or when it has more than
six words. A command name `[target]_[action]_command` is checked with its
target decomposed as a name of its own; a name with the placeholder `unknown`
ends with it and an optional index.

Covered surfaces: the B524 service (OP=0x00 identifiers, OP=0x02 and OP=0x06
registers) in the B524 fixtures (including the write-template labels that are
register names), the register tables of the B524 register map
and protocol page, and the register-name tables of the B524 semantic-plane
page. `previous_name` columns hold earlier names and are not checked.
"""

from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VOCABULARY = ROOT / "architecture" / "fixtures" / "register-name-vocabulary.csv"
VAILLANT = ROOT / "protocols" / "vaillant"
FIXTURES = VAILLANT / "fixtures"
REGISTER_MAP = VAILLANT / "ebus-vaillant-B524-register-map.md"
PROTOCOL = VAILLANT / "ebus-vaillant-B524.md"
SEMANTIC_MAPPING = ROOT / "architecture" / "b524-semantic-mapping.md"

VOCABULARY_COLUMNS = ["token", "roles", "definition", "forbidden_synonyms"]
ROLES = {
    "purpose",
    "attribute",
    "subject",
    "place",
    "object",
    "part",
    "predicate",
    "bound",
    "period",
    "manner",
    "action",
    "placeholder",
    "marker",
}
# The closed predicate list of architecture/naming.md.
PREDICATES = {
    "setpoint", "limit", "offset", "hysteresis", "active", "enabled", "demand",
    "connected", "ready", "available", "ok", "fault", "state", "status", "mode",
    "type", "code", "bitfield", "count", "time", "level", "position", "ratio",
    "factor", "command",
}
# Compound predicate terms built on a predicate of the closed list.
PREDICATE_COMPOUNDS = {"operating_mode": "mode"}
ABBREVIATIONS = {"dhw", "pv", "rtc", "eeprom"}
MAX_WORDS = 6

# Slot order. Attributes appear before the subject or before the object.
SLOTS = [
    "purpose",
    "attribute_s",
    "subject",
    "index_s",
    "place",
    "attribute_o",
    "object",
    "part",
    "index_o",
    "predicate",
    "bound",
    "period",
    "manner",
]
SLOT = {name: number for number, name in enumerate(SLOTS)}
# Every slot except the two attribute slots holds at most one word.
SINGLE = {
    "purpose", "subject", "index_s", "place", "object", "part", "index_o",
    "predicate", "bound", "period", "manner",
}
ROLE_SLOTS = {
    "purpose": ["purpose"],
    "attribute": ["attribute_s", "attribute_o"],
    "subject": ["subject"],
    "place": ["place"],
    "object": ["object"],
    "part": ["part"],
    "predicate": ["predicate"],
    "bound": ["bound"],
    "period": ["period"],
    "manner": ["manner"],
}
# Trailing slots admitted by the predicate (architecture/naming.md, "Predicates"
# and "Order of the parts"). A bound follows a measured value (no predicate) or
# `setpoint`, `limit`, `offset`, `hysteresis`, `time`, `count`; a period follows
# a measured value, a `count` or a `time`; a manner follows a measured value.
# A name with any other predicate (a boolean, an enumeration, a code, ...) ends
# at the predicate, apart from a condition.
BOUND_PREDICATES = {None, "setpoint", "limit", "offset", "hysteresis", "time", "count"}
PERIOD_PREDICATES = {None, "count", "time"}
MANNER_PREDICATES = {None}
# Objects that are counted events or occurrences: `count` is "the number of
# occurrences of the object event" (architecture/naming.md, "Predicates"); the
# events of the Object row (`start`, `switch`), the vocabulary's `stop` event
# and the time-programme `period`. Without an object, `count` is the number of
# subjects and needs an explicit subject.
COUNTED_OBJECTS = {"start", "stop", "switch", "period"}
INDEX = re.compile(r"[1-9][0-9]*")
# A part follows its object directly: date and clock-time parts
# (architecture/naming.md) and the two halves of a text split across fields.
TEXT_OBJECTS = {"name", "phone_number", "serial_number", "access_code"}
PART_HOSTS = {
    "year": {"date"},
    "month": {"date"},
    "day": {"date"},
    "hour": {"clock_time"},
    "minute": {"clock_time"},
    "second": {"clock_time"},
    "prefix": TEXT_OBJECTS,
    "suffix": TEXT_OBJECTS,
}
PLACEHOLDER_PREFIX_SLOTS = {"purpose", "attribute_s", "subject", "index_s", "place"}
NAME = re.compile(r"[a-z][a-z0-9]*(?:_[a-z0-9]+)*")


class NameError_(ValueError):
    """A canonical name that does not decompose."""


@dataclass(frozen=True)
class Vocabulary:
    roles: dict[str, frozenset[str]]
    forbidden: dict[str, str]

    @property
    def compounds(self) -> list[tuple[str, ...]]:
        terms = [tuple(token.split("_")) for token in self.roles if "_" in token]
        return sorted(terms, key=len, reverse=True)


def load_vocabulary(path: Path = VOCABULARY) -> Vocabulary:
    with path.open(encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames != VOCABULARY_COLUMNS:
            raise ValueError(f"{path}: columns must be {VOCABULARY_COLUMNS}")
        rows = list(reader)
    roles: dict[str, frozenset[str]] = {}
    forbidden: dict[str, str] = {}
    for row in rows:
        token = row["token"]
        if not NAME.fullmatch(token):
            raise ValueError(f"vocabulary token {token!r} is not snake_case")
        if token in roles:
            raise ValueError(f"vocabulary token {token!r} is listed twice")
        token_roles = frozenset(row["roles"].split("|"))
        unknown = token_roles - ROLES
        if not token_roles or unknown:
            raise ValueError(f"vocabulary token {token!r} has unknown roles {sorted(unknown)}")
        if not row["definition"].strip():
            raise ValueError(f"vocabulary token {token!r} has no definition")
        roles[token] = token_roles
        for synonym in filter(None, row["forbidden_synonyms"].split("|")):
            if synonym in forbidden:
                raise ValueError(f"forbidden synonym {synonym!r} is listed twice")
            forbidden[synonym] = token
    for synonym, token in forbidden.items():
        if synonym in roles:
            raise ValueError(f"forbidden synonym {synonym!r} of {token!r} is a vocabulary token")
    for token, token_roles in roles.items():
        if "predicate" in token_roles and token not in PREDICATES and token not in PREDICATE_COMPOUNDS:
            raise ValueError(f"{token!r} is not in the closed predicate list")
    return Vocabulary(roles=roles, forbidden=forbidden)


def segment(tokens: list[str], vocabulary: Vocabulary) -> list[str]:
    """Split tokens into vocabulary words, compound terms longest first."""
    words: list[str] = []
    position = 0
    while position < len(tokens):
        for compound in vocabulary.compounds:
            if tuple(tokens[position:position + len(compound)]) == compound:
                words.append("_".join(compound))
                position += len(compound)
                break
        else:
            words.append(tokens[position])
            position += 1
    return words


def _check_forbidden(name: str, words: list[str], vocabulary: Vocabulary) -> None:
    for word in words:
        if word in vocabulary.forbidden:
            raise NameError_(
                f"{name}: {word!r} is a forbidden synonym of {vocabulary.forbidden[word]!r}"
            )
    padded = f"_{name}_"
    for synonym, token in vocabulary.forbidden.items():
        if "_" in synonym and f"_{synonym}_" in padded and synonym not in words:
            covered = any(
                f"_{synonym}_" in f"_{word}_" for word in words if "_" in word
            )
            if not covered:
                raise NameError_(f"{name}: {synonym!r} is a forbidden synonym of {token!r}")


def _assign(
    words: list[str], vocabulary: Vocabulary, allowed: set[str], *, needs_core: bool
) -> list[str] | None:
    """Return one slot per word in non-decreasing order, or None.

    Roles other than attribute are tried first, so a noun is read as the
    subject or object before it is read as an attribute of a later noun.
    """

    def options(position: int, previous: str | None) -> list[str]:
        word = words[position]
        if INDEX.fullmatch(word):
            if previous == "subject":
                return ["index_s"]
            if previous == "object":
                return ["index_o"]
            return []
        if word not in vocabulary.roles:
            return []
        slots: list[str] = []
        for role in vocabulary.roles[word]:
            slots.extend(ROLE_SLOTS.get(role, []))
        if "part" in slots:
            host = words[position - 1] if position else None
            if previous != "object" or host not in PART_HOSTS.get(word, set()):
                slots.remove("part")
        return slots

    def trailing_slots_fit(chosen: tuple[str, ...]) -> bool:
        predicate = next((words[i] for i, slot in enumerate(chosen) if slot == "predicate"), None)
        predicate = PREDICATE_COMPOUNDS.get(predicate, predicate)
        object_word = next((words[i] for i, slot in enumerate(chosen) if slot == "object"), None)
        if predicate == "count":
            if object_word is None:
                if "subject" not in chosen:
                    return False
            elif object_word not in COUNTED_OBJECTS:
                return False
        if predicate == "time" and object_word is None:
            return False  # a duration of the object activity
        for slot, admitted in (
            ("bound", BOUND_PREDICATES),
            ("period", PERIOD_PREDICATES),
            ("manner", MANNER_PREDICATES),
        ):
            if slot in chosen and predicate not in admitted:
                return False
        return True

    def search(
        position: int, previous: str | None, used: frozenset[str], chosen: tuple[str, ...] = ()
    ) -> list[str] | None:
        if position == len(words):
            if not trailing_slots_fit(chosen):
                return None
            if "attribute_s" in used and "subject" not in used:
                return None
            if "attribute_o" in used and "object" not in used:
                return None
            if needs_core and not {"subject", "object", "predicate"} & used:
                return None
            return []
        ordered = sorted(
            options(position, previous),
            key=lambda slot: (slot.startswith("attribute"), SLOT[slot]),
        )
        for slot in ordered:
            if slot not in allowed:
                continue
            if previous is not None and SLOT[slot] < SLOT[previous]:
                continue
            if slot in SINGLE and slot in used:
                continue
            if slot == "index_o" and "subject" in used:
                continue
            rest = search(position + 1, slot, used | {slot}, (*chosen, slot))
            if rest is not None:
                return [slot, *rest]
        return None

    return search(0, None, frozenset())


def decompose(name: str, vocabulary: Vocabulary, *, nested: bool = False) -> list[tuple[str, str]]:
    """Return (word, role) pairs for a canonical name or raise NameError_."""
    if not NAME.fullmatch(name):
        raise NameError_(f"{name}: not lowercase snake_case ASCII")
    words = segment(name.split("_"), vocabulary)
    _check_forbidden(name, words, vocabulary)
    for word in words:
        if word not in vocabulary.roles and not INDEX.fullmatch(word):
            raise NameError_(f"{name}: token {word!r} has no vocabulary entry")

    # [target]_[action]_command
    if not nested and len(words) >= 3 and words[-1] == "command":
        action = words[-2]
        if "action" not in vocabulary.roles.get(action, frozenset()):
            raise NameError_(f"{name}: {action!r} before 'command' is not an action")
        target = "_".join(words[:-2])
        decompose(target, vocabulary, nested=True)
        return [(target, "target"), (action, "action"), ("command", "predicate")]

    if "command" in words:
        raise NameError_(
            f"{name}: 'command' only closes a name of the form [target]_[action]_command"
        )

    # condition: at_... closes the name
    condition: list[str] = []
    if "at" in words:
        at = words.index("at")
        condition = words[at + 1:]
        words = words[:at]
        if not condition:
            raise NameError_(f"{name}: empty condition after 'at'")
        seen_object = False
        seen_term = False
        for word in condition:
            roles = vocabulary.roles.get(word, frozenset())
            if not roles or roles & {"marker", "placeholder"} or word == "command":
                raise NameError_(f"{name}: {word!r} is not a vocabulary term for a condition")
            if roles == {"bound"}:
                if seen_object:
                    raise NameError_(f"{name}: inside a condition a bound precedes its object")
            else:
                seen_term = True
                if "object" in roles:
                    seen_object = True
        # a bound precedes the object it qualifies: only attributes, places and further
        # bounds may stand between them, and an object has to follow
        for position, word in enumerate(condition):
            if vocabulary.roles[word] != {"bound"}:
                continue
            for later in condition[position + 1:]:
                later_roles = vocabulary.roles[later]
                if "object" in later_roles:
                    break
                if later_roles != {"bound"} and not later_roles & {"attribute", "place"}:
                    raise NameError_(
                        f"{name}: inside a condition the bound {word!r} is not followed by its object"
                    )
            else:
                raise NameError_(
                    f"{name}: inside a condition the bound {word!r} is not followed by its object"
                )
        if not seen_term:
            raise NameError_(f"{name}: a condition needs a term other than a bound")

    # placeholder: [purpose]_[subject]_[place]_unknown[_index]
    placeholder: list[str] = []
    if "unknown" in words:
        at = words.index("unknown")
        placeholder = words[at:]
        words = words[:at]
        if condition or len(placeholder) > 2 or (
            len(placeholder) == 2 and not INDEX.fullmatch(placeholder[1])
        ):
            raise NameError_(f"{name}: 'unknown' must close the name, followed only by an index")

    allowed = PLACEHOLDER_PREFIX_SLOTS if placeholder else set(SLOTS)
    if not words and not placeholder:
        raise NameError_(f"{name}: a name needs a subject, an object or a predicate")
    slots = _assign(words, vocabulary, allowed, needs_core=not placeholder) if words else []
    if slots is None:
        if placeholder:
            raise NameError_(f"{name}: only purpose, attribute, subject or place may precede 'unknown'")
        raise NameError_(
            f"{name}: no role assignment follows the order of the parts "
            "with a subject, an object or a predicate"
        )

    counted = [word for word in words if not INDEX.fullmatch(word)]
    word_count = len(counted) + (1 if condition else 0) + (1 if placeholder else 0)
    if word_count > MAX_WORDS:
        raise NameError_(f"{name}: {word_count} words, more than {MAX_WORDS}")

    parts = [(word, slot.split("_")[0]) for word, slot in zip(words, slots)]
    if placeholder:
        parts.append(("unknown", "placeholder"))
        parts.extend((index, "index") for index in placeholder[1:])
    if condition:
        parts.append(("at_" + "_".join(condition), "condition"))
    return parts


# ---------------------------------------------------------------------------
# Covered surfaces
# ---------------------------------------------------------------------------

# The name cell of a row is captured whole (any non-pipe content); the code
# span is stripped afterwards by `_cell_names`, so a malformed name is reported
# by decompose() instead of making the whole row be skipped.
CELL = r"([^|]*?)"
# A register row of the register map: `| 0x0001 | name |` or a register range.
ROW = re.compile(rf"^\| 0x[0-9A-F]{{4}}(?:-0x[0-9A-F]{{4}})? \| {CELL} \|")
# An identifier or register row written `| 0000h | `name` |`, optionally paired
# (`| 0000h / 0001h | `a` / `b` |`).
HEX_H_ROW = re.compile(rf"^\| [0-9A-F]{{4}}h(?: / [0-9A-F]{{4}}h)? \| {CELL} \|")
# A register row of a table keyed by group and register.
GROUP_REGISTER_ROW = re.compile(rf"^\| 0x[0-9A-F]{{2}} \| 0x[0-9A-F]{{4}} \| {CELL} \|")
# A register row of the protocol page: `| 0x0036 | `name` |`.
PROTOCOL_ROW = re.compile(rf"^\| `?0x[0-9A-F]{{4}}`? \| {CELL} \|")

# The explicit notes the pages write in place of a name for a register that has
# none yet: `(unknown)`, `(unknown, 8 regs)` and `(unknown_temp_config)`. Any
# other cell is validated as a name, in parentheses or not.
UNNAMED = re.compile(r"\(unknown(?:, [1-9][0-9]* regs)?\)|\(unknown_temp_config\)")


def _cell_names(cell: str, *, paired: bool = False) -> list[str]:
    """Names in a table cell: strip one complete outer code span per name, keep
    the rest as written, and leave out only the explicit unnamed notes."""
    names = []
    for part in cell.strip().split(" / ") if paired else [cell.strip()]:
        part = part.strip()
        if len(part) >= 2 and part.startswith("`") and part.endswith("`"):
            part = part[1:-1]
        if not UNNAMED.fullmatch(part):
            names.append(part)
    return names


def _read_rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _csv_names(path: Path, column: str = "name") -> list[tuple[str, str]]:
    with path.open(encoding="utf-8", newline="") as handle:
        return [
            (f"{path.relative_to(ROOT)}:{number}", row[column])
            for number, row in enumerate(csv.DictReader(handle), 2)
            if row[column]
        ]


def _section(text: str, start: str, end: str) -> list[tuple[int, str]]:
    lines = text.splitlines()
    begin = next(i for i, line in enumerate(lines) if line.startswith(start))
    finish = next(i for i, line in enumerate(lines) if i > begin and line.startswith(end))
    return list(enumerate(lines[begin:finish], begin + 1))


def covered_names() -> list[tuple[str, str]]:
    names: list[tuple[str, str]] = []
    for fixture in (
        "b524-op02-register-names.csv",
        "b524-register-name-correspondence.csv",
        "b524-op02-requester-register-matrix.csv",
        "b524-op02-calendar-clock-selectors.csv",
        "b524-op00-system-information-ids.csv",
    ):
        names.extend(_csv_names(FIXTURES / fixture))
    # Write-template labels that are canonical register names (the other labels
    # describe a write in words). A canonical row is identified without looking
    # at the syntax of its label: its label differs from `previous_name`, or it
    # equals the catalog name of its selector. The raw label is validated.
    catalog = {
        (row["group"], row["register"]): row["name"]
        for row in _read_rows(FIXTURES / "b524-op02-register-names.csv")
    }
    templates = FIXTURES / "b524-op02-write-templates.csv"
    for number, row in enumerate(_read_rows(templates), 2):
        label = row["write"]
        selector = (row["group"], row["register"])
        if label != row["previous_name"] or catalog.get(selector) == label:
            names.append((f"{templates.relative_to(ROOT)}:{number}", label))

    register_map = REGISTER_MAP.read_text(encoding="utf-8")
    where = REGISTER_MAP.relative_to(ROOT)
    for number, line in _section(register_map, "## OP=0x02", "## Constraint Catalog"):
        for pattern, paired in ((ROW, False), (HEX_H_ROW, True)):
            match = pattern.match(line)
            if match:
                names.extend((f"{where}:{number}", name) for name in _cell_names(match[1], paired=paired))

    protocol = PROTOCOL.read_text(encoding="utf-8")
    where = PROTOCOL.relative_to(ROOT)
    for number, line in _section(protocol, "### 4.1 `0x00` ReadSystemInformation", "### 4.2"):
        match = HEX_H_ROW.match(line)
        if match:
            names.extend((f"{where}:{number}", name) for name in _cell_names(match[1], paired=True))
    for number, line in enumerate(protocol.splitlines(), 1):
        match = PROTOCOL_ROW.match(line)
        if match:
            names.extend((f"{where}:{number}", name) for name in _cell_names(match[1]))

    # Register-name tables of the semantic-plane page: `| 0x00 | 0x0007 | name |`.
    semantic = SEMANTIC_MAPPING.read_text(encoding="utf-8")
    where = SEMANTIC_MAPPING.relative_to(ROOT)
    for number, line in enumerate(semantic.splitlines(), 1):
        match = GROUP_REGISTER_ROW.match(line)
        if match:
            names.extend((f"{where}:{number}", name) for name in _cell_names(match[1]))
    return names


def main() -> int:
    vocabulary = load_vocabulary()
    failures = []
    names = covered_names()
    for where, name in names:
        try:
            decompose(name, vocabulary)
        except NameError_ as error:
            failures.append(f"{where}: {error}")
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        return 1
    distinct = len({name for _, name in names})
    print(f"Register name decomposition passed ({len(names)} occurrences, {distinct} names).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
