import pytest
from _scheme import decision
from luria import badges, ci, lint

@pytest.fixture(autouse=True)
def _no_ambient_ci(monkeypatch):
    for var in ci.CI_VARS:
        monkeypatch.delenv(var, raising=False)

def test_a_bare_shell_is_not_ci():
    assert ci.running_in_ci() is False

@pytest.mark.parametrize('var', ci.CI_VARS)
def test_any_known_variable_is_enough(monkeypatch, var):
    monkeypatch.setenv(var, 'true')
    assert ci.running_in_ci() is True

@pytest.mark.parametrize('value', ['', '0', 'false', 'no', 'off', '  False  '])
def test_a_runner_saying_not_a_build_is_believed(monkeypatch, value):
    monkeypatch.setenv('CI', value)
    assert ci.running_in_ci() is False

def test_a_terminal_gets_the_bare_command():
    assert ci.regenerate_remedy() == 'run `luria index`'

def test_ci_is_offered_both_ways_to_commit(monkeypatch):
    monkeypatch.setenv('CI', 'true')
    remedy = ci.regenerate_remedy()
    assert 'locally' in remedy
    assert 'generation job' in remedy and 'pushes' in remedy

def test_ci_warns_against_the_shape_that_commits_nothing(monkeypatch):
    monkeypatch.setenv('CI', 'true')
    remedy = ci.regenerate_remedy()
    assert 'not enough on its own' in remedy
    assert 'comparing that output against itself' in remedy

def test_the_remedy_never_forbids_generating_in_ci(monkeypatch):
    monkeypatch.setenv('CI', 'true')
    remedy = ci.regenerate_remedy().lower()
    for forbidding in ('do not add', 'never', 'must not', 'nothing that writes'):
        assert forbidding not in remedy, f'remedy forbids generation: {remedy!r}'

def test_the_remedy_names_the_command_it_was_given(monkeypatch):
    monkeypatch.setenv('CI', 'true')
    assert '`luria collect`' in ci.regenerate_remedy('luria collect')

def test_the_lint_carries_the_ci_remedy(monkeypatch, project):
    decision(project, 1, 'Active')
    (project / 'docs' / 'decisions' / 'README.md').write_text('stale\n')
    monkeypatch.setenv('CI', 'true')
    errors: list[str] = []
    lint.check_generated_index(errors)
    assert errors, 'a hand-written index should be stale'
    assert any(('regenerate and commit the result' in e for e in errors))
    assert any(('generation job' in e for e in errors))

def test_bare_badges_says_it_only_printed(capsys, monkeypatch, project):
    decision(project, 1, 'Active')
    assert badges.run() is None
    out, err = capsys.readouterr()
    assert badges.OPEN in out, 'the markdown still goes to stdout'
    assert 'printed only' in err
    assert 'printed only' not in out, 'stdout stays clean for redirection'
