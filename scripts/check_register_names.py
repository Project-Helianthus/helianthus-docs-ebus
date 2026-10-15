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
six words; the object of `time` has to carry the vocabulary role `activity` or
`event`, a bound, period or manner needs an object or a predicate to qualify,
and `average` needs a period before it. A command name
`[target]_[action]_command` is checked with its target decomposed as a name of
its own; a name with the placeholder `unknown` ends with it and an optional
index.

Covered surfaces: the B524 service (OP=0x00 identifiers, OP=0x02 and OP=0x06
registers) in the B524 fixtures (including the write-template labels that are
register names), the register tables of the B524 register map
and protocol page, and the register-name tables of the B524 semantic-plane
page. `previous_name` columns hold earlier names and are not checked.
"""

from __future__ import annotations

import csv
import re
import string
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
    # Class markers of an object: what a `time` can last or separate.
    "activity",
    "event",
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
# Classes of the object that `time` measures (vocabulary role markers).
TIMED_ROLES = frozenset({"activity", "event"})
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
                # The number of subjects takes only the bound `maximum`, the
                # supported number of them (naming.md, `count` row and "A bound
                # after ..."), and no period or manner.
                if "period" in chosen or "manner" in chosen:
                    return False
                bound = next((words[i] for i, slot in enumerate(chosen) if slot == "bound"), None)
                if bound is not None and bound != "maximum":
                    return False
            elif object_word not in COUNTED_OBJECTS:
                return False
        if predicate == "time":
            # `time` is the duration of an activity, the interval between
            # occurrences of an event, or a remaining time: its object is a
            # vocabulary word marked `activity` or `event`.
            if object_word is None or not TIMED_ROLES & vocabulary.roles[object_word]:
                return False
        # A bound or a period qualifies a quantity or a predicate, never a bare
        # subject; the manner `average` follows its period.
        if ("bound" in chosen or "period" in chosen or "manner" in chosen) and (
            object_word is None and predicate is None
        ):
            return False
        # `remaining` is the time until the next occurrence or the end
        # (architecture/naming.md, `time` row), so it only follows `time`.
        if "remaining" in words and predicate != "time":
            return False
        if "average" in words and "period" not in chosen:
            return False
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
        seen_term = False
        for word in condition:
            roles = vocabulary.roles.get(word, frozenset())
            if not roles or roles & {"marker", "placeholder"} or word == "command":
                raise NameError_(f"{name}: {word!r} is not a vocabulary term for a condition")
            if roles != {"bound"}:
                seen_term = True
        # a bound precedes the object it qualifies (an earlier term that can also
        # be an object only supplies context): only attributes, places and further
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
    # A command target counts as one word of the command name (naming.md,
    # "Operations and commands"), so the six-word limit applies to the whole
    # command name, which has three words, and not to the nested target.
    if word_count > MAX_WORDS and not nested:
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
# The changed-name summary tables of the register map: a backticked register or
# range (`| `0x001D` | `name` | `previous_name` |`) and a backticked selector
# (`| `GG=0x01, RR=0x0012` | `name` | ... |`, groups and registers may be listed
# with `/`). Only the raw Name cell is a name.
SUMMARY_REGISTER_ROW = re.compile(rf"^\| `0x[0-9A-F]{{4}}(?:-0x[0-9A-F]{{4}})?` \| {CELL} \|")
SUMMARY_SELECTOR_ROW = re.compile(
    rf"^\| `GG=0x[0-9A-F]{{2}}(?:/0x[0-9A-F]{{2}})*, RR=0x[0-9A-F]{{4}}` \| {CELL} \|"
)
# A row of the `Candidate write encodings` table after the constraint catalog:
# a backticked selector, then the catalog names of the written registers, each in
# a code span and separated by `, `. Every cell of the column is validated by
# position, except the documented prose value `none in the catalog`.
WRITE_ENCODING_ROW = re.compile(rf"^\| `GG=[^|]*\| {CELL} \|")
# The one prose value of the catalog-name column.
NO_CATALOG_NAME = "none in the catalog"
# A register row of a table keyed by group and register.
GROUP_REGISTER_ROW = re.compile(rf"^\| 0x[0-9A-F]{{2}} \| 0x[0-9A-F]{{4}} \| {CELL} \|")
# A register row of the protocol page: `| 0x0036 | `name` |`.
PROTOCOL_ROW = re.compile(rf"^\| `?0x[0-9A-F]{{4}}`? \| {CELL} \|")

# The explicit notes the pages write in place of a name for a register that has
# none yet: `(unknown)`, `(unknown, 8 regs)` and `(unknown_temp_config)`. Any
# other cell is validated as a name, in parentheses or not.
UNNAMED = re.compile(r"\(unknown(?:, [1-9][0-9]* regs)?\)|\(unknown_temp_config\)")


def _strip_code_span(part: str) -> str:
    """Remove exactly one complete outer code span; any other backtick stays, so
    unbalanced or repeated delimiters reach decompose() and fail there."""
    part = part.strip()
    if len(part) >= 2 and part.startswith("`") and part.endswith("`"):
        return part[1:-1]
    return part


def _cell_names(cell: str, *, paired: bool = False) -> list[str]:
    """Names in a table cell: strip one complete outer code span per name, keep
    the rest as written, and leave out only the explicit unnamed notes."""
    names = []
    for part in cell.strip().split(" / ") if paired else [cell.strip()]:
        part = _strip_code_span(part)
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


# Columns of the protocol page's tables that carry a register name when the row
# does not begin with a register: located by the header cell of the table.
NAME_COLUMN_HEADERS = {"Register", "Write", "Name"}
TRAILING_NOTE = re.compile(r" \([^()]*\)$")


GROUP_REGISTER_SELECTOR = re.compile(r"GG=0x([0-9A-Fa-f]{2})\b.*?RR=0x([0-9A-Fa-f]{4})\b")
# The body cell may be cut at an escaped pipe (`<u8 0\\|1>`), so its closing
# backtick is not required.
WRITE_BODY = re.compile(r"`02 01 ([0-9A-F]{2}) [0-9A-F]{2} ([0-9A-F]{2}) ([0-9A-F]{2})(?: |`|$)")


def _row_selector(cells: list[str]) -> tuple[str, str] | None:
    """The (group, register) of a row: `GG=..., RR=...` in a cell, else the
    selector bytes of a write body (`02 01 GG II RR_low RR_high ...`)."""
    for cell in cells:
        match = GROUP_REGISTER_SELECTOR.search(cell)
        if match:
            return f"0x{match[1].upper()}", f"0x{match[2].upper()}"
    for cell in cells:
        match = WRITE_BODY.match(cell)
        if match:
            register = int(match[3] + match[2], 16)
            return f"0x{match[1]}", f"0x{register:04X}"
    return None


def _raw_name_column_cells(lines: list[str]) -> list[tuple[int, str, tuple[str, str] | None, str]]:
    """Raw name cells of tables whose rows do not begin with a register."""
    found: list[tuple[int, str, tuple[str, str] | None, str]] = []
    header: list[str] | None = None
    for number, line in enumerate(lines, 1):
        if not line.startswith("|"):
            header = None
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if header is None:
            header = cells
            continue
        if set("".join(cells)) <= set("-: "):
            continue
        if PROTOCOL_ROW.match(line) or HEX_H_ROW.match(line):
            continue
        selector = _row_selector(cells)
        for cell, title in zip(cells, header):
            if title in NAME_COLUMN_HEADERS:
                found.append((number, cell, selector, title))
    return found


def _name_column_cells(lines: list[str]) -> list[tuple[int, str, tuple[str, str] | None, str]]:
    """Name cells of tables whose rows do not begin with a register.

    Strip one trailing parenthesised note, then classify a cell as canonical
    when it contains a code span or is a single whitespace-free token. Strip
    exactly one outer code span and preserve the raw remainder for validation
    and comparison with the catalog name of the row's selector. Unquoted cells
    with inner whitespace are prose; register-leading rows are read by the
    register-row matchers instead. For catalog-named selectors, the additional
    mangled-name check catches prose that normalizes to the catalog name; only
    prose that does not normalize to that name remains exempt.
    """
    found = []
    for number, cell, selector, title in _raw_name_column_cells(lines):
        remainder = TRAILING_NOTE.sub("", cell)
        token = _strip_code_span(remainder)
        if "`" in remainder or (token and not any(ch.isspace() for ch in token)):
            found.append((number, token, selector, title))
    return found


def name_column_cells(lines: list[str]) -> list[tuple[int, str, tuple[str, str] | None]]:
    return [(number, token, selector) for number, token, selector, _ in _name_column_cells(lines)]


def mangled_canonical_names(
    lines: list[str], catalog_rows: list[dict[str, str]]
) -> list[tuple[int, str, str]]:
    """Skipped prose cells whose normalized form is their selector's name."""
    catalog = {(row["group"], row["register"]): row["name"] for row in catalog_rows if row["name"]}
    canonical = set(name_column_cells(lines))
    found = []
    for number, cell, selector, _ in _raw_name_column_cells(lines):
        token = _strip_code_span(TRAILING_NOTE.sub("", cell))
        if selector not in catalog or (number, token, selector) in canonical:
            continue
        normalized = re.sub(r"[\s-]+", "_", token.lower()).strip(string.punctuation)
        expected = catalog[selector]
        if normalized == expected and token != expected:
            found.append((number, token, expected))
    return found


def header_column_names(lines: list[str]) -> list[tuple[int, str]]:
    return [
        (number, token)
        for number, token, _, title in _name_column_cells(lines)
        if title != "Register" or not re.fullmatch(r"0x[0-9A-F]{4}", token)
    ]


def selector_name_mismatches(
    lines: list[str], catalog_rows: list[dict[str, str]]
) -> list[tuple[int, str, str]]:
    """Name cells that differ from the catalog name of the selector of their row.

    Where the row carries a selector and the catalog names it, the raw name cell
    must equal that name, including whitespace; backtick and single-token
    validation are fallbacks when the catalog does not name the selector.
    """
    catalog = {(row["group"], row["register"]): row["name"] for row in catalog_rows if row["name"]}
    return [
        (number, token, catalog[selector])
        for number, token, selector, title in _name_column_cells(lines)
        if title != "Register" or not re.fullmatch(r"0x[0-9A-F]{4}", token)
        if selector in catalog and token != catalog[selector]
    ]


def canonical_template_labels(
    templates: list[dict[str, str]],
) -> list[tuple[int, str]]:
    """Return raw canonical labels using the explicit canonical/prose row role.

    The role is independent of the editable label, provenance and selector.
    Missing or invalid roles fail closed rather than silently omitting a row.
    This designation concerns naming only, not native write qualification.
    """
    labels = []
    for number, row in enumerate(templates, 2):
        role = row.get("write_role")
        if role not in {"canonical", "prose"}:
            raise ValueError(
                f"b524-op02-write-templates.csv:{number}: "
                f"write_role must be 'canonical' or 'prose', found {role!r}"
            )
        if role == "canonical":
            labels.append((number, row["write"]))
    return labels


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
    templates = FIXTURES / "b524-op02-write-templates.csv"
    for number, label in canonical_template_labels(
        _read_rows(templates)
    ):
        names.append((f"{templates.relative_to(ROOT)}:{number}", label))

    register_map = REGISTER_MAP.read_text(encoding="utf-8")
    where = REGISTER_MAP.relative_to(ROOT)
    for number, line in _section(register_map, "## OP=0x02", "## Constraint Catalog"):
        for pattern, paired in (
            (ROW, False),
            (HEX_H_ROW, True),
            (SUMMARY_REGISTER_ROW, False),
            (SUMMARY_SELECTOR_ROW, False),
        ):
            match = pattern.match(line)
            if match:
                names.extend((f"{where}:{number}", name) for name in _cell_names(match[1], paired=paired))

    # The register map after the constraint catalog carries canonical names in one
    # table only: the catalog names of `Candidate write encodings`. The enum
    # tables, the mapping conflicts (myPyllant and TSP leaf names), the state
    # machines (state values) and the other tables of that part name no register.
    for number, line in _section(
        register_map, "### Candidate write encodings", "## Open questions"
    ):
        match = WRITE_ENCODING_ROW.match(line)
        if match and match[1].strip() != NO_CATALOG_NAME:
            names.extend(
                (f"{where}:{number}", _strip_code_span(part))
                for part in match[1].split(", ")
            )

    protocol = PROTOCOL.read_text(encoding="utf-8")
    where = PROTOCOL.relative_to(ROOT)
    for number, line in _section(protocol, "### 4.1 `0x00` ReadSystemInformation", "### 4.2"):
        match = HEX_H_ROW.match(line)
        if match:
            names.extend((f"{where}:{number}", name) for name in _cell_names(match[1], paired=True))
    names.extend(
        (f"{where}:{number}", name)
        for number, name in header_column_names(protocol.splitlines())
    )
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
    try:
        names = covered_names()
    except ValueError as error:
        print(error, file=sys.stderr)
        return 1
    for where, name in names:
        try:
            decompose(name, vocabulary)
        except NameError_ as error:
            failures.append(f"{where}: {error}")
    protocol_lines = PROTOCOL.read_text(encoding="utf-8").splitlines()
    catalog_rows = _read_rows(FIXTURES / "b524-op02-register-names.csv")
    for number, token, expected in selector_name_mismatches(
        protocol_lines, catalog_rows
    ):
        selector = _row_selector([cell.strip() for cell in protocol_lines[number - 1].split("|")])
        group, register = selector
        failures.append(
            f"{PROTOCOL.relative_to(ROOT)}:{number}: selector GG={group}, RR={register}: "
            f"expected {expected!r}, found {token!r}"
        )
    for number, token, expected in mangled_canonical_names(protocol_lines, catalog_rows):
        selector = _row_selector([cell.strip() for cell in protocol_lines[number - 1].split("|")])
        group, register = selector
        failures.append(
            f"{PROTOCOL.relative_to(ROOT)}:{number}: selector GG={group}, RR={register}: "
            f"mangled canonical name: expected {expected!r}, found {token!r}"
        )
    for failure in failures:
        print(failure, file=sys.stderr)
    if failures:
        return 1
    distinct = len({name for _, name in names})
    print(f"Register name decomposition passed ({len(names)} occurrences, {distinct} names).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
