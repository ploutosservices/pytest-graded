# pytest-graded

Run each test script as one pytest item, and fail a script that graded nothing.

pytest's own rule is that a test that asserts nothing passes. For a suite of test scripts, that
rule lets through the most expensive failure there is: a script whose loop matched no input,
exited 0, and proved nothing. This plugin runs each script in its own process, counts the cases it
graded, and gives one of four verdicts.

## The four verdicts

| verdict | exit code | cases graded | pytest outcome |
|---|---|---|---|
| PASSED | 0 | one or more | passed |
| FAILED | non-zero | one or more | failed, with the script's FAIL lines |
| DID NOT RUN | non-zero | none | failed, with the last line of the traceback |
| GRADED NOTHING | 0 | none | failed |

A graded case is a line of the script's output, on stdout or stderr, that starts with `ok` or
`FAIL` followed by white space, optionally indented:

```
ok    the thermostat reads 21.5
FAIL  the shade reports its battery
      expected a percentage, got null
```

Lines indented under a `FAIL` line are carried into pytest's failure report.

## Install

```
pip install git+https://github.com/ploutosservices/pytest-graded
```

pytest finds the plugin by its entry point; no `-p` flag is needed.

## Configure

In `pytest.ini`, `pyproject.toml` (`[tool.pytest.ini_options]`) or `setup.cfg`:

| setting | default | meaning |
|---|---|---|
| `graded_files` | `tests-*.py` | glob of script names collected, one item per file |
| `graded_strip_env` | none | environment variable names removed before each script runs, so no script reaches, for example, a real alert endpoint |

Each script runs with the same Python interpreter as pytest, from the project's root directory.

## Run

```
python -m pytest                        # every script matching graded_files
python -m pytest tests-shades.py        # one script
```

## Tests

The four verdicts are each drawn from a drill script in `tests/drills/`:

```
pip install -e .
python -m pytest
```

## Licence

Apache-2.0. See `LICENSE` and `NOTICE`.
