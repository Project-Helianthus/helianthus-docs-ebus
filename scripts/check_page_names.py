#!/usr/bin/env python3
"""Check renamed documentation page names, their inbound links and their status.

The finite table `architecture/page-status.json` lists every page whose file
name was normalized to lowercase kebab-case. For each row the checker requires:

- one-to-one destinations: no two rows share a destination or an earlier name,
  no destination collides (ignoring letter case) with a different file in its
  directory, and the directory itself is unchanged;
- a destination basename in lowercase kebab-case that is not a repository
  control file name (README.md, AGENTS.md, CONTRIBUTING.md, CHANGELOG.md and
  SECURITY.md are tooling entrypoints, not published page names);
- the destination present with its exact directory-entry spelling and the
  earlier spelling absent (letter case is compared on the listed entry, not
  through a case-insensitive existence test);
- a status from the closed set, kept as the page's own claim: the row quotes
  the page sentence that carries the status, and that sentence has to stay in
  the page;
- inbound-link closure: no repository file names an earlier basename, except
  pinned provenance that pairs the earlier path with a fixed owner commit and
  the kept text of a link on an existing References line (a References section
  or a table row labelled Reference) whose target is the renamed page;
- unchanged anchor targets: every Markdown link into a listed page resolves to
  the exact file and to a heading or explicit anchor of that page; the finite
  list of anchors that already failed before the rename must match exactly;
- the tree indexes: each is linked from README.md and links every publishable
  page of its tree except the identified pages kept out of navigation; a listed
  page outside every indexed tree is linked from README.md.

The earlier names are documentary only. Nothing reads them as a fallback.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import sys
from collections import Counter
from pathlib import Path

TABLE = "architecture/page-status.json"
CONTENT_ADDRESS = re.compile(r"^[0-9a-f]{64}$")
STATUSES = ("implemented", "accepted contract", "candidate", "historical", "unknown")
CONTROL_FILES = ("AGENTS.md", "CHANGELOG.md", "CONTRIBUTING.md", "README.md", "SECURITY.md")
NO_STATEMENT = "No page-level status statement in the opening section."
TOP_KEYS = {
    "table",
    "scope",
    "statuses",
    "control_files",
    "tree_indexes",
    "unlinked_pages",
    "pages",
    "pinned_provenance",
    "known_unresolved_links",
    "reference_link_texts",
    "inherited_unresolved_anchors",
}
ROW_KEYS = {"path", "previous_path", "status", "basis"}
ANCHOR_KEYS = {"source", "target", "anchor"}
KEBAB = re.compile(r"[a-z0-9]+(?:-[a-z0-9]+)*\.md")
BRANCH_URL = "https://github.com/Project-Helianthus/helianthus-docs-ebus/blob/main/"
SKIP_DIRS = {"__pycache__", "node_modules"}
INLINE_LINK = re.compile(r"\]\(\s*<?([^\s)>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
DEFINITION = re.compile(r"^\s{0,3}\[[^\]]+\]:\s*<?(\S+?)>?(?:\s|$)", re.M)
HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
REFERENCE_HEADING = re.compile(r"^#{1,6}\s+.*\bReferences?\b", re.I)
REFERENCE_ROW = re.compile(r"^\|\s*References?\s*\|")
LINK_WITH_TEXT = re.compile(r"\[((?:[^\[\]]|\[[^\]]*\])*)\]\(\s*<?([^\s)>]+)>?(?:\s+\"[^\"]*\")?\s*\)")
HTML_ANCHOR = re.compile(r"<a\s+(?:name|id)=\"([^\"]+)\"")
CANDIDATE_WORDS = re.compile(
    r"\bHypothesis\b|\bcandidates?\b|\bproposed\b|\bunconfirmed\b|not yet proven|"
    r"not live-validated|not yet live-validated",
    re.I,
)
STATUS_WORDS = {
    "implemented": re.compile(r"\bimplemented\b", re.I),
    "accepted contract": re.compile(
        r"\bcontract\b|\bauthoritative\b|\bcanonical\b|\bSpecification\b|library interface",
        re.I,
    ),
    "candidate": CANDIDATE_WORDS,
    "historical": re.compile(r"\bsuperseded\b|\bhistorical\b|\bretired\b", re.I),
}
NOT_IMPLEMENTED = re.compile(r"\bnot\b[^.]*\bimplemented\b|\bno\b[^.]*\bimplemented\b", re.I)


def normalize(text: str) -> str:
    return " ".join(text.split())


def heading_slug(text: str) -> str:
    text = re.sub(r"`([^`]*)`", r"\1", text)
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"[^\w\- ]", "", text.strip().lower())
    return text.replace(" ", "-")


def page_anchors(text: str) -> set[str]:
    anchors: set[str] = set()
    seen: Counter[str] = Counter()
    fenced = False
    for line in text.splitlines():
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            continue
        if fenced:
            continue
        match = HEADING.match(line)
        if match:
            slug = heading_slug(match.group(2))
            count = seen[slug]
            seen[slug] += 1
            anchors.add(slug if count == 0 else f"{slug}-{count}")
        anchors.update(HTML_ANCHOR.findall(line))
    return anchors


def entry_names(directory: Path) -> list[str]:
    try:
        return os.listdir(directory)
    except OSError:
        return []


def repository_files(root: Path):
    for current, dirs, files in os.walk(root):
        rel_dir = os.path.relpath(current, root)
        dirs[:] = sorted(
            d
            for d in dirs
            if d not in SKIP_DIRS and (not d.startswith(".") or d == ".github")
        )
        for name in sorted(files):
            if rel_dir == "." and name.startswith("."):
                continue  # local handoff files and tool state at the root
            rel = name if rel_dir == "." else posixpath.join(*Path(rel_dir).parts, name)
            yield rel, Path(current) / name


def read_text(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def valid_identifiers(value) -> bool:
    if not isinstance(value, list):
        return False
    if not all(isinstance(item, str) and re.fullmatch(r"[0-9a-f]{16}", item) for item in value):
        return False
    return len(value) == len(set(value))


def page_identifier(path: str) -> str:
    return hashlib.sha256(path.encode("utf-8")).hexdigest()[:16]


def file_key(rel: str) -> str:
    """Path whose content-address segment is shortened to its first 16 characters."""
    parts = rel.split("/")
    return "/".join(part[:16] if CONTENT_ADDRESS.match(part) else part for part in parts)


def resolve_file_key(root: Path, key: str) -> str:
    if (root / key).is_file():
        return key
    for rel, _ in repository_files(root):
        if file_key(rel) == key:
            return rel
    return key


def pinned_pairs(root: Path, entries: list) -> tuple[dict, list[str]]:
    pairs = {}
    errors = []
    if not isinstance(entries, list):
        return pairs, [f"{TABLE}: pinned_provenance must be a list"]
    for item in entries:
        if not valid_pin(item):
            errors.append(f"{TABLE}: malformed pinned pair")
            continue
        key = (item["file"], item["path"])
        path = root / resolve_file_key(root, key[0])
        text = read_text(path) or ""
        errors += pin_content_errors(path, item)
        if key in pairs or text.count(key[1]) != item["count"]:
            errors.append(f"{TABLE}: pinned pair {key} occurrence count differs or is duplicated")
        pairs[key] = item["count"]
    return pairs, errors


def valid_pin(item) -> bool:
    if not isinstance(item, dict) or set(item) != {"file", "path", "count", "content"}:
        return False
    return (all(isinstance(item[k], str) and item[k] for k in ("file", "path"))
            and type(item["count"]) is int and item["count"] > 0
            and isinstance(item["content"], str)
            and re.fullmatch(r"[0-9a-f]{16}", item["content"]) is not None)


def pin_content_errors(path: Path, item: dict) -> list[str]:
    try:
        content = hashlib.sha256(path.read_bytes()).hexdigest()[:16]
    except OSError:
        content = None
    if content != item["content"]:
        return [f"{item['file']}: the file changed, review the pinned pair and refresh the table"]
    return []


def pinned_occurrence(rel: str, text: str, start: int, end: int, pairs: dict) -> bool:
    for file, path in pairs:
        if file != file_key(rel):
            continue
        offset = text.rfind(path, 0, end)
        if offset >= 0 and offset <= start and offset + len(path) >= end:
            return True
    return False


def table_navigation_errors(table: dict) -> list[str]:
    errors: list[str] = []
    indexes = table["tree_indexes"]
    if not isinstance(indexes, list) or not all(
        isinstance(item, str) and item.endswith("/index.md") for item in indexes
    ):
        errors.append(f"{TABLE}: tree_indexes must list <tree>/index.md paths")
        table["tree_indexes"] = []
    unlinked = table["unlinked_pages"]
    if not isinstance(unlinked, dict) or any(
        key not in table["tree_indexes"] or not valid_identifiers(value)
        for key, value in unlinked.items()
    ):
        errors.append(
            f"{TABLE}: unlinked_pages must map listed tree indexes to identifier lists"
        )
        table["unlinked_pages"] = {}
    return errors


def load_table(root: Path) -> tuple[dict | None, list[str]]:
    try:
        table = json.loads((root / TABLE).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return None, [f"{TABLE}: unreadable status table ({exc.__class__.__name__})"]
    errors: list[str] = []
    if not isinstance(table, dict) or set(table) != TOP_KEYS:
        return None, [f"{TABLE}: top-level keys must be exactly {sorted(TOP_KEYS)}"]
    if table["statuses"] != list(STATUSES):
        errors.append(f"{TABLE}: statuses must be exactly {list(STATUSES)}")
    if table["control_files"] != list(CONTROL_FILES):
        errors.append(f"{TABLE}: control_files must be exactly {list(CONTROL_FILES)}")
    for key in ("table", "scope"):
        if not isinstance(table[key], str) or not table[key].strip():
            errors.append(f"{TABLE}: {key} must be a non-empty string")
    errors += table_navigation_errors(table)
    rows = table["pages"]
    if not isinstance(rows, list) or not rows:
        errors.append(f"{TABLE}: pages must be a non-empty list")
        table["pages"] = []
    anchors = table["inherited_unresolved_anchors"]
    if not isinstance(anchors, list):
        errors.append(f"{TABLE}: inherited_unresolved_anchors must be a list")
        table["inherited_unresolved_anchors"] = []
    return table, errors


def valid_rows(rows: list) -> tuple[list[dict], list[str]]:
    errors: list[str] = []
    valid: list[dict] = []
    for number, row in enumerate(rows, 1):
        where = f"{TABLE}: pages[{number}]"
        if not isinstance(row, dict) or set(row) != ROW_KEYS:
            errors.append(f"{where}: keys must be exactly {sorted(ROW_KEYS)}")
        elif not all(isinstance(row[key], str) and row[key] for key in ROW_KEYS):
            errors.append(f"{where}: every field must be a non-empty string")
        else:
            valid.append(row)
    return valid, errors


def uniqueness_errors(rows: list[dict]) -> list[str]:
    destinations = Counter(row["path"] for row in rows)
    folded = Counter(row["path"].casefold() for row in rows)
    earlier = Counter(row["previous_path"] for row in rows)
    errors = [
        f"{TABLE}: destination {path} is listed {count} times"
        for path, count in destinations.items()
        if count > 1
    ]
    errors += [
        f"{TABLE}: destinations collide ignoring letter case: {path}"
        for path, count in folded.items()
        if count > 1 and destinations[path] <= 1
    ]
    errors += [
        f"{TABLE}: earlier name {path} is listed {count} times"
        for path, count in earlier.items()
        if count > 1
    ]
    errors += [
        f"{TABLE}: {row['path']}: earlier name {row['previous_path']} is also a destination"
        for row in rows
        if row["previous_path"] in destinations
    ]
    return errors


def name_errors(row: dict) -> list[str]:
    where = f"{TABLE}: {row['path']}"
    directory, name = posixpath.split(row["path"])
    previous_directory, previous_name = posixpath.split(row["previous_path"])
    checks = (
        (directory != previous_directory, f"directory changed from {previous_directory}"),
        (not KEBAB.fullmatch(name), "basename is not lowercase kebab-case"),
        (
            name in CONTROL_FILES or previous_name in CONTROL_FILES,
            "repository control files are not renamed pages",
        ),
        (bool(KEBAB.fullmatch(previous_name)), f"earlier name {previous_name} already conforms"),
    )
    return [f"{where}: {message}" for failed, message in checks if failed]


def entry_errors(root: Path, row: dict) -> list[str]:
    where = f"{TABLE}: {row['path']}"
    directory, name = posixpath.split(row["path"])
    previous_name = posixpath.basename(row["previous_path"])
    entries = entry_names(root / directory)
    same_folded = [entry for entry in entries if entry.casefold() == name.casefold()]
    checks = (
        (name not in entries, "no directory entry with this exact spelling"),
        (previous_name in entries, f"earlier entry {previous_name} is still present"),
        (
            any(entry != name for entry in same_folded),
            "collides with a different entry ignoring letter case",
        ),
    )
    return [f"{where}: {message}" for failed, message in checks if failed]


def status_errors(root: Path, row: dict) -> list[str]:
    where = f"{TABLE}: {row['path']}"
    status = row["status"]
    if status not in STATUSES:
        return [f"{where}: status {status!r} is outside the closed set"]
    if status == "unknown":
        if row["basis"] != NO_STATEMENT:
            return [f"{where}: an unknown status uses the fixed basis sentence"]
        return []
    basis = normalize(row["basis"])
    text = read_text(root / row["path"])
    checks = (
        (not STATUS_WORDS[status].search(basis), f"basis does not state the {status} status"),
        (
            status == "accepted contract" and bool(CANDIDATE_WORDS.search(basis)),
            "a candidate basis cannot carry an accepted contract",
        ),
        (
            status == "implemented" and bool(NOT_IMPLEMENTED.search(basis)),
            "the basis denies implementation",
        ),
        (
            text is not None and basis not in normalize(text),
            "basis sentence is not on the page",
        ),
    )
    return [f"{where}: {message}" for failed, message in checks if failed]


def check_rows(root: Path, rows: list) -> tuple[list[dict], list[str]]:
    valid, errors = valid_rows(rows)
    errors += uniqueness_errors(valid)
    for row in valid:
        errors += name_errors(row) + entry_errors(root, row) + status_errors(root, row)
    return valid, errors


def reference_lines(text: str) -> set[int]:
    """Line numbers of existing References lines in a Markdown page."""
    lines: set[int] = set()
    in_section = fenced = False
    for number, line in enumerate(text.splitlines(), 1):
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
            continue
        if fenced:
            continue
        if line.startswith("#"):
            in_section = bool(REFERENCE_HEADING.match(line))
        elif in_section or REFERENCE_ROW.match(line):
            lines.add(number)
    return lines


def kept_link_text(rel: str, line: str, column: int, destination: str, allowed: dict) -> bool:
    """True when the column lies in the text of a link whose target is the destination."""
    for link in LINK_WITH_TEXT.finditer(line):
        if link.start(1) <= column < link.end(1):
            resolved = resolve(rel, link.group(2))
            return (resolved is not None and resolved[0] == destination
                    and (rel, link.group(1)) in allowed)
    return False


def valid_reference(item) -> bool:
    if not isinstance(item, dict) or set(item) != {"file", "text", "count"}:
        return False
    return (all(isinstance(item[k], str) and item[k] for k in ("file", "text"))
            and type(item["count"]) is int and item["count"] > 0)


def reference_counts(root: Path, rel: str) -> Counter:
    text = read_text(root / rel) or ""
    lines = reference_lines(text) if rel.endswith(".md") else set()
    return Counter(link.group(1)
                   for number, line in enumerate(text.splitlines(), 1) if number in lines
                   for link in LINK_WITH_TEXT.finditer(line))


def reference_pairs(root: Path, entries) -> tuple[dict, list[str]]:
    pairs = {}
    errors = []
    if not isinstance(entries, list):
        return pairs, [f"{TABLE}: reference_link_texts must be a list"]
    for item in entries:
        if not valid_reference(item):
            errors.append(f"{TABLE}: malformed reference link text")
            continue
        key = (item["file"], item["text"])
        if key in pairs or reference_counts(root, key[0])[key[1]] != item["count"]:
            errors.append(f"{TABLE}: reference link text {key} occurrence count differs or is duplicated")
        pairs[key] = item["count"]
    return pairs, errors


def check_closure(root: Path, rows: list[dict], pairs: dict, allowed: dict) -> list[str]:
    destination = {posixpath.basename(row["previous_path"]): row["path"] for row in rows}
    if not destination:
        return []
    pattern = re.compile(
        r"(?<![A-Za-z0-9_-])("
        + "|".join(sorted(map(re.escape, destination), key=len, reverse=True))
        + r")(?![A-Za-z0-9_-])"
    )
    errors: list[str] = []
    for rel, path in repository_files(root):
        text = read_text(path) if rel != TABLE else None
        if text is None:
            continue
        references = reference_lines(text) if rel.endswith(".md") else set()
        for match in pattern.finditer(text):
            if pinned_occurrence(rel, text, match.start(), match.end(), pairs):
                continue
            line = text.count("\n", 0, match.start()) + 1
            start = text.rfind("\n", 0, match.start()) + 1
            end = text.find("\n", match.start())
            content = text[start:] if end < 0 else text[start:end]
            if line in references and kept_link_text(
                rel, content, match.start() - start, destination[match.group(1)], allowed
            ):
                continue  # link text kept on a References line; its target is renamed
            errors.append(f"{rel}:{line}: still names the earlier page {match.group(1)}")
    return errors


def link_targets(text: str):
    fenced = False
    offset = 0
    for line in text.splitlines(keepends=True):
        if line.lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced:
            for match in INLINE_LINK.finditer(line):
                yield offset + match.start(), match.group(1)
            for match in DEFINITION.finditer(line):
                yield offset + match.start(), match.group(1)
        offset += len(line)


def resolve(source: str, target: str) -> tuple[str, str] | None:
    if target.startswith(BRANCH_URL):
        path, _, fragment = target[len(BRANCH_URL):].partition("#")
        return path, fragment
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", target):
        return None
    path, _, fragment = target.partition("#")
    if not path:
        return source, fragment
    return posixpath.normpath(posixpath.join(posixpath.dirname(source), path)), fragment


def inherited_anchors(inherited: list) -> tuple[set[tuple[str, str, str]], list[str]]:
    expected: set[tuple[str, str, str]] = set()
    errors: list[str] = []
    for number, item in enumerate(inherited, 1):
        if not isinstance(item, dict) or set(item) != ANCHOR_KEYS or not all(
            isinstance(item[key], str) and item[key] for key in ANCHOR_KEYS
        ):
            errors.append(f"{TABLE}: inherited_unresolved_anchors[{number}] is malformed")
            continue
        expected.add((item["source"], item["target"], item["anchor"]))
    return expected, errors


class LinkCheck:
    """Links into the listed pages: exact spelling and resolvable anchors."""

    def __init__(self, root: Path, rows: list[dict], expected: set[tuple[str, str, str]]):
        self.root = root
        self.pages = {row["path"] for row in rows}
        self.folded = {path.casefold(): path for path in self.pages}
        self.expected = expected
        self.seen: set[tuple[str, str, str]] = set()
        self.anchors: dict[str, set[str]] = {}
        self.errors: list[str] = []

    def anchor_set(self, page: str) -> set[str]:
        if page not in self.anchors:
            self.anchors[page] = page_anchors(read_text(self.root / page) or "")
        return self.anchors[page]

    def problem(self, rel: str, link_path: str, fragment: str) -> str | None:
        if link_path not in self.pages:
            if link_path.casefold() in self.folded:
                return f"link spelling differs from {self.folded[link_path.casefold()]}"
            return None
        if not fragment or fragment in self.anchor_set(link_path):
            return None
        key = (rel, link_path, fragment)
        if key in self.expected:
            self.seen.add(key)
            return None
        return f"anchor #{fragment} is not on {link_path}"

    def check_file(self, rel: str, text: str) -> None:
        for offset, target in link_targets(text):
            resolved = resolve(rel, target)
            if resolved is None:
                continue
            message = self.problem(rel, *resolved)
            if message:
                line = text.count("\n", 0, offset) + 1
                self.errors.append(f"{rel}:{line}: {message}")

    def stale(self) -> list[str]:
        return [
            f"{TABLE}: inherited unresolved anchor {source} -> {target}#{anchor} "
            "no longer occurs unresolved; remove it from the list"
            for source, target, anchor in sorted(self.expected - self.seen)
        ]


def check_links(root: Path, rows: list[dict], inherited: list) -> list[str]:
    expected, errors = inherited_anchors(inherited)
    links = LinkCheck(root, rows, expected)
    for rel, path in repository_files(root):
        text = read_text(path) if rel.endswith(".md") else None
        if text is not None:
            links.check_file(rel, text)
    return errors + links.errors + links.stale()


def exact_target(root: Path, path: str) -> bool:
    current = root
    for part in Path(path).parts:
        if part != ".." and part not in entry_names(current):
            return False
        current = current / part
    return current.exists()


def unresolved_links(root: Path) -> set[tuple[str, str]]:
    missing = set()
    for rel, path in repository_files(root):
        if not rel.endswith(".md"):
            continue
        for _, target in link_targets(read_text(path) or ""):
            resolved = resolve(rel, target)
            if resolved is not None and not exact_target(root, resolved[0]):
                missing.add((rel, target))
    return missing


def known_links(entries) -> tuple[set, list[str]]:
    expected = set()
    errors = []
    if not isinstance(entries, list):
        return expected, [f"{TABLE}: known_unresolved_links must be a list"]
    for item in entries:
        if not isinstance(item, dict) or set(item) != {"source", "target"}:
            errors.append(f"{TABLE}: malformed unresolved link")
        elif not all(isinstance(v, str) and v for v in item.values()):
            errors.append(f"{TABLE}: malformed unresolved link")
        else:
            expected.add((item["source"], item["target"]))
    return expected, errors


def check_missing_links(root: Path, entries) -> list[str]:
    expected, errors = known_links(entries)
    actual = unresolved_links(root)
    errors += [f"{source}: missing link target {target}" for source, target in sorted(actual - expected)]
    errors += [f"{TABLE}: {source} -> {target} no longer occurs unresolved; remove it from the list"
               for source, target in sorted(expected - actual)]
    return errors


def linked_paths(root: Path, source: str) -> set[str]:
    text = read_text(root / source) or ""
    out = set()
    for _, target in link_targets(text):
        resolved = resolve(source, target)
        if resolved is not None:
            out.add(resolved[0])
    return out


def unlinked_tree_pages(root: Path, tree: str, index: str, links: set[str]) -> list[str]:
    unlinked: list[str] = []
    for rel, _ in repository_files(root / tree):
        page = posixpath.join(tree, rel)
        if not page.endswith(".md") or page == index:
            continue
        if posixpath.basename(page) in CONTROL_FILES:
            continue
        if page not in links:
            unlinked.append(page)
    return unlinked


def check_indexes(
    root: Path, rows: list[dict], indexes: list[str], unlinked_pages: dict[str, list[str]]
) -> list[str]:
    errors: list[str] = []
    readme_links = linked_paths(root, "README.md")
    covered: set[str] = set()
    for index in indexes:
        tree = posixpath.dirname(index)
        if posixpath.basename(index) not in entry_names(root / tree):
            errors.append(f"{index}: tree index is missing")
            continue
        if index not in readme_links:
            errors.append(f"README.md: does not link the tree index {index}")
        links = linked_paths(root, index)
        unlinked = unlinked_tree_pages(root, tree, index, links)
        declared = set(unlinked_pages.get(index, []))
        if {page_identifier(page) for page in unlinked} != declared:
            errors.append(
                f"{index}: unlinked page identifiers differ; "
                f"unlinked pages: {[(page, page_identifier(page)) for page in sorted(unlinked)]}"
            )
        covered.update(
            row["path"] for row in rows if row["path"].startswith(tree + "/")
        )
    for row in rows:
        if row["path"] not in covered and row["path"] not in readme_links:
            errors.append(f"README.md: {row['path']} has no tree index and is not linked")
    return errors


def check(root: Path) -> list[str]:
    table, errors = load_table(root)
    if table is None:
        return errors
    rows, row_errors = check_rows(root, table["pages"])
    errors += row_errors
    pairs, pin_errors = pinned_pairs(root, table["pinned_provenance"])
    allowed, reference_errors = reference_pairs(root, table["reference_link_texts"])
    errors += pin_errors + reference_errors + check_closure(root, rows, pairs, allowed)
    errors += check_missing_links(root, table["known_unresolved_links"])
    errors += check_links(root, rows, table["inherited_unresolved_anchors"])
    errors += check_indexes(root, rows, table["tree_indexes"], table["unlinked_pages"])
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args(argv)
    errors = check(args.root)
    for error in errors:
        print(error, file=sys.stderr)
    if errors:
        return 1
    print("Page names, inbound links, anchors, tree indexes and the status table passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
