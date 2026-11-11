"""Each of the four verdicts, drawn by running pytest with the plugin over one drill script."""
import pathlib

import pytest

pytest_plugins = ["pytester"]

DRILLS = pathlib.Path(__file__).parent / "drills"


def run_drill(pytester, name):
    pytester.makefile(".py", **{name: (DRILLS / f"{name}.py").read_text()})
    return pytester.runpytest_subprocess("-rf")


def test_passed(pytester):
    r = run_drill(pytester, "tests-pass")
    r.assert_outcomes(passed=1)


@pytest.mark.parametrize("name, verdict", [
    ("tests-fail", "FAILED (2 case(s) graded): FAIL  a case that does not"),
    ("tests-broken", "DID NOT RUN (exit 1): ModuleNotFoundError"),
    ("tests-quiet", "GRADED NOTHING (exit 0)"),
])
def test_failing_verdicts(pytester, name, verdict):
    r = run_drill(pytester, name)
    r.assert_outcomes(failed=1)
    assert verdict in r.stdout.str()


def test_failed_keeps_the_indented_detail(pytester):
    r = run_drill(pytester, "tests-fail")
    assert "expected 3, got 4" in r.stdout.str()


def test_only_the_glob_is_collected(pytester):
    pytester.makefile(".py", helper="print('not a test script')")
    pytester.makefile(".py", **{"tests-pass": (DRILLS / "tests-pass.py").read_text()})
    r = pytester.runpytest_subprocess()
    r.assert_outcomes(passed=1)


def test_glob_is_configurable(pytester):
    pytester.makeini("[pytest]\ngraded_files = check_*.py\n")
    pytester.makefile(".py", check_one=(DRILLS / "tests-quiet.py").read_text())
    r = pytester.runpytest_subprocess()
    r.assert_outcomes(failed=1)
    assert "GRADED NOTHING" in r.stdout.str()


def test_stripped_variable_does_not_reach_the_script(pytester, monkeypatch):
    monkeypatch.setenv("GRADED_SECRET_DOOR", "https://example.invalid")
    pytester.makeini("[pytest]\ngraded_strip_env = GRADED_SECRET_DOOR\n")
    pytester.makefile(".py", **{"tests-env": (
        "import os\n"
        "print('ok    the door is gone' if 'GRADED_SECRET_DOOR' not in os.environ "
        "else 'FAIL  the door is gone')\n"
        "raise SystemExit('GRADED_SECRET_DOOR' in os.environ)\n")})
    r = pytester.runpytest_subprocess()
    r.assert_outcomes(passed=1)
