import copy
import json

import pytest

from scripts.check_nm_inventory import ROOT, validate


@pytest.fixture
def rows():
    return json.loads((ROOT / 'architecture/nm-implementation-inventory.json').read_text())


def test_inventory_valid(rows):
    validate(rows)


@pytest.mark.parametrize(('field', 'value'), [
    ('key', 'unknown'), ('page', 'architecture/other.md'),
    ('section', 'Other'), ('status', 'implemented composed infrastructure'),
    ('source', 'other.go'), ('symbol', 'Other'), ('limit', ''),
])
def test_target_fields_rejected(rows, field, value):
    rows[0][field] = value
    with pytest.raises(ValueError):
        validate(rows)


@pytest.mark.parametrize(('field', 'value'), [
    ('key', 'unknown'), ('page', 'architecture/other.md'), ('section', 'Other'),
    ('status', 'implemented composed infrastructure'), ('source', 'other.go'),
    ('symbol', 'Other'), ('limit', 'Production composition established.'),
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
