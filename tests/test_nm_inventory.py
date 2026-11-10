import copy
import json

import pytest

from scripts.check_nm_inventory import PAGES, ROOT, validate


@pytest.fixture
def rows():
    return json.loads((ROOT / 'architecture/nm-implementation-inventory.json').read_text())


def test_inventory_valid(rows):
    validate(rows)


@pytest.mark.parametrize(('field', 'value'), [
    ('key', 'unknown'), ('page', 'architecture/other.md'),
    ('section', 'Other'), ('status', 'implemented composed infrastructure'),
    ('evidence', 'Proven'), ('candidate', False), ('limit', ''),
])
def test_target_fields_rejected(rows, field, value):
    rows[0][field] = value
    with pytest.raises(ValueError):
        validate(rows)


@pytest.mark.parametrize(('field', 'value'), [
    ('key', 'unknown'), ('page', 'architecture/other.md'), ('section', 'Other'),
    ('status', 'implemented composed infrastructure'), ('evidence', 'Proven'),
    ('candidate', False), ('limit', 'Production composition established.'),
])
def test_helper_fields_rejected(rows, field, value):
    row = next(item for item in rows if item['key'] == 'broadcast-helper')
    row[field] = value
    with pytest.raises(ValueError):
        validate(rows)


def test_missing_and_duplicate_rejected(rows):
    with pytest.raises(ValueError):
        validate(rows[:-1])
    rows.append(copy.deepcopy(rows[0]))
    with pytest.raises(ValueError):
        validate(rows)


@pytest.mark.parametrize('heading', ['Runtime Components', 'Runtime---Components'])
def test_colliding_section_keys_rejected(rows, tmp_path, heading):
    architecture = tmp_path / 'architecture'
    architecture.mkdir()
    for page in PAGES:
        text = (ROOT / 'architecture' / page).read_text()
        if page == 'nm-model.md':
            text += '\n### ' + heading + '\n'
        (architecture / page).write_text(text)
    with pytest.raises(ValueError, match='colliding section key'):
        validate(rows, root=tmp_path)


@pytest.mark.parametrize('key', ['broadcast-helper', 'responder-helper'])
@pytest.mark.parametrize(('field', 'value'), [
    ('source', 'withheld'), ('symbol', 'withheld'),
    ('evidence', ''), ('candidate', 1),
])
def test_helper_publication_contract_rejected(rows, key, field, value):
    row = next(item for item in rows if item['key'] == key)
    row[field] = value
    with pytest.raises(ValueError):
        validate(rows)
