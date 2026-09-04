"""The suite must run outside this pod (CI portability guard).

Same class of defect as A1: a check that silently only works in one place has stopped being a
check. Thirteen test files hardcoded the pod root, which exists in the Emergent pod and nowhere
else — four broke imports through `sys.path.insert`, four broke on a bare `open()`, and nine did
a `load_dotenv` that was a silent no-op elsewhere. A collection error aborts the whole pytest
run, so one of them was enough to fail the entire offline job before a single assertion ran.

Paths now come from `__file__` via the two conftest roots. This test is what stops the next one
creeping back in.
"""
import ast
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SELF = os.path.basename(os.path.abspath(__file__))

# Assembled rather than written, so the file that bans the literal does not contain it.
POD = "/" + "app" + "/"
TEST_DIRS = (os.path.join(ROOT, "tests"), os.path.join(ROOT, "backend", "tests"))


def _test_files():
    for directory in TEST_DIRS:
        for name in sorted(os.listdir(directory)):
            if name.endswith(".py") and name != SELF:
                yield os.path.join(directory, name)


def test_no_test_file_hardcodes_a_pod_path():
    offenders = []
    for path in _test_files():
        for lineno, line in enumerate(open(path, encoding="utf-8"), 1):
            if POD in line:
                offenders.append(f"{os.path.relpath(path, ROOT)}:{lineno} — {line.strip()[:100]}")
    assert not offenders, (
        "Hardcoded pod paths — these run in the Emergent pod and nowhere else. Derive from "
        "__file__ instead:\n" + "\n".join(offenders)
    )


def test_both_test_roots_have_a_conftest():
    """The single place paths and environment are derived. Deleting one silently un-fixes this."""
    for directory in TEST_DIRS:
        conftest = os.path.join(directory, "conftest.py")
        assert os.path.exists(conftest), f"no conftest.py at {directory}"
        source = open(conftest, encoding="utf-8").read()
        assert "os.path.abspath(__file__)" in source, f"{conftest} does not derive its root"
        assert "load_dotenv" in source and "sys.path.insert" in source
        assert POD not in source


def test_every_test_file_imports_cleanly():
    """A syntax or collection error in any one file aborts the entire run, so parse them all."""
    for path in _test_files():
        with open(path, encoding="utf-8") as fh:
            ast.parse(fh.read(), filename=path)


def test_no_test_file_reintroduces_its_own_dotenv_path():
    """load_dotenv with a literal path is the silent failure: missing file, no error, no env."""
    offenders = []
    for path in _test_files():
        if os.path.basename(path) == "conftest.py":
            continue
        source = open(path, encoding="utf-8").read()
        for node in ast.walk(ast.parse(source)):
            if (isinstance(node, ast.Call) and getattr(node.func, "id", "") == "load_dotenv"
                    and node.args and isinstance(node.args[0], ast.Constant)):
                offenders.append(f"{os.path.relpath(path, ROOT)}:{node.lineno}")
    assert not offenders, ("load_dotenv with a literal path outside conftest — a no-op wherever "
                           f"that path doesn't exist: {offenders}")


def test_the_workflow_runs_both_roots():
    workflow = open(os.path.join(ROOT, ".github", "workflows", "rk-tests.yml"), encoding="utf-8").read()
    assert "pytest tests" in workflow
    assert "RK_ALLOW_PLACEHOLDER_ALPHA" in workflow
    assert POD not in workflow
