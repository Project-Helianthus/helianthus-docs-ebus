"""The automatic local-gate sweep executes the literal ratchet."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("rule_literals", ROOT / "scripts/check_rule_literals.py")
CHECKER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECKER)


def test_repository_literal_ratchet():
    assert CHECKER.check() == []


def test_module_assignment_forms():
    for source in ['VALUE = {value!r}', 'VALUE: str = {value!r}', 'VALUE = ({value!r},)']:
        assert not CHECKER.literals(source.format(value='a' * 120))
        assert CHECKER.literals(source.format(value='a' * 121))


def test_function_strings_are_outside_module_assignment_scope():
    assert not CHECKER.literals('def example():\n    return ' + repr('a' * 121))


def test_exact_baseline_rejects_new_changed_and_removed_debt(tmp_path):
    import json
    scripts = tmp_path / 'scripts'
    (scripts / 'rules').mkdir(parents=True)
    path = scripts / 'check_example.py'
    source = 'VALUE = ' + repr('a' * 121)
    path.write_text(source)
    baseline = scripts / 'rules/literal_baseline.json'
    baseline.write_text(json.dumps({'scripts/check_example.py': CHECKER.literals(source)}))
    assert CHECKER.check(tmp_path) == []
    for replacement in ['VALUE = ' + repr('b' * 121), source.replace('VALUE', 'OTHER'), '', source + '\nOTHER = ' + repr('a' * 121)]:
        path.write_text(replacement)
        assert CHECKER.check(tmp_path)
