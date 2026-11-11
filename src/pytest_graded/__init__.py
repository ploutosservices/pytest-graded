"""pytest-graded: run each test script as one pytest item, and fail a script that graded nothing.

A test script here is a program that prints one line per case it grades, `ok  <label>` or
`FAIL  <label>`, and exits non-zero when a case failed. pytest collects each matching file as one
item, runs it in its own process, and draws one of four verdicts:

    PASSED          exit 0, and at least one ok/FAIL line
    FAILED          exit non-zero, and the script graded something first
    DID NOT RUN     exit non-zero, and the script graded nothing
    GRADED NOTHING  exit 0, and not one ok/FAIL line

Anything but PASSED fails the item, and the failure's first word is the verdict. pytest's own rule
is that a test that asserts nothing passes; GRADED NOTHING is the case that rule lets through.

Configuration (pytest.ini, pyproject.toml or setup.cfg):

    graded_files      glob of script names to collect, default `tests-*.py`
    graded_strip_env  environment variable names removed before each script runs
"""
import fnmatch
import os
import re
import subprocess
import sys

import pytest

__version__ = "0.1.0"

# A graded line is "ok  <label>" or "FAIL  <label>", optionally indented. Anchored and
# case-sensitive, so a stray "ok" inside a message is never a verdict.
GRADED = re.compile(r"^\s*(ok|FAIL)\s", re.M)
FAILED_CASE = re.compile(r"^\s*FAIL\s")


def pytest_addoption(parser):
    parser.addini("graded_files", "glob of test script names collected one item per file",
                  default="tests-*.py")
    parser.addini("graded_strip_env", "environment variable names removed before each script runs",
                  type="args", default=[])


def failing_lines(out, err, limit=12):
    """The FAIL lines a failed script printed, with whatever it indented under each one."""
    kept, taking = [], False
    for line in ((out or "") + "\n" + (err or "")).splitlines():
        if FAILED_CASE.match(line):
            if len(kept) >= limit:
                kept.append(f"... and more, beyond the first {limit}")
                break
            kept.append(line.strip())
            taking = True
        elif taking and line.startswith((" ", "\t")) and line.strip():
            kept.append("  " + line.strip())
        else:
            taking = False
    return kept or ["the script exited non-zero and printed no FAIL line; read its output"]


def classify(path, cwd, strip=()):
    """(verdict, exit code, cases graded, reason) for one script, run as its own process."""
    env = {k: v for k, v in os.environ.items() if k not in set(strip)}
    p = subprocess.run([sys.executable, str(path)], capture_output=True, text=True, env=env,
                       cwd=str(cwd))
    # Both streams: a script that prints its verdicts to stderr graded real cases.
    graded = len(GRADED.findall(p.stdout or "")) + len(GRADED.findall(p.stderr or ""))
    if p.returncode == 0:
        if graded == 0:
            return "GRADED NOTHING", 0, 0, (
                "exit 0 with zero graded cases: every case skipped, or the script's inputs "
                "matched nothing. Nothing was proven.")
        return "PASSED", 0, graded, ""
    if graded:
        return "FAILED", p.returncode, graded, "\n".join(failing_lines(p.stdout, p.stderr))[:1600]
    # The last traceback line is where a reader starts.
    tail = [l for l in (p.stderr or p.stdout or "").splitlines() if l.strip()]
    return "DID NOT RUN", p.returncode, 0, tail[-1].strip() if tail else "no output at all"


class Verdict(Exception):
    pass


class GradedFile(pytest.File):
    def collect(self):
        yield GradedItem.from_parent(self, name="graded")


class GradedItem(pytest.Item):
    def runtest(self):
        strip = self.config.getini("graded_strip_env")
        state, rc, graded, reason = classify(self.path, self.config.rootpath, strip)
        if state != "PASSED":
            note = f" ({graded} case(s) graded)" if state == "FAILED" else f" (exit {rc})"
            raise Verdict(f"{state}{note}: {reason}")

    def repr_failure(self, excinfo):
        if isinstance(excinfo.value, Verdict):
            return str(excinfo.value)
        return super().repr_failure(excinfo)

    def reportinfo(self):
        return self.path, None, self.path.name


def pytest_collect_file(file_path, parent):
    if fnmatch.fnmatch(file_path.name, parent.config.getini("graded_files")):
        return GradedFile.from_parent(parent, path=file_path)
