import os
import sys

import nox

nox.options.sessions = "lint_pylint", "typecheck", "test"

EDITABLE_TESTS = True
PYTHON_VERSIONS = None
if "GITHUB_ACTIONS" in os.environ:
    PYTHON_VERSIONS = ["3.10", "3.14"]
    EDITABLE_TESTS = False

FILES_TO_BE_CHECKED = [
    "src",
]


@nox.session
def doc(session):
    """
    Build the documentation.

    Accepts the following arguments:
    - serve: open documentation after build
    - further arguments are passed to mkbuild
    """

    options = session.posargs[:]
    open_doc = "serve" in options
    if open_doc:
        options.remove("serve")

    session.install("-e", ".[doc]")

    if open_doc:
        open_cmd = "xdg-open" if sys.platform == "linux" else "open"
        session.run(open_cmd, "http://localhost:8000/systems/benchmark-tool/")
        session.run("mkdocs", "serve", *options)
    else:
        session.run("mkdocs", "build", *options)


@nox.session
def format(session):
    """
    Autoformat source files.

    If argument check is given, only reports changes.
    """
    session.install("-e", ".[format]")
    check = "check" in session.posargs

    autoflake_args = [
        "--in-place",
        "--imports=benchmarktool",
        "--ignore-init-module-imports",
        "--remove-unused-variables",
        "-r",
        "tests",
    ] + FILES_TO_BE_CHECKED
    if check:
        autoflake_args.remove("--in-place")
    session.run("autoflake", *autoflake_args)

    isort_args = ["--profile", "black", "tests"] + FILES_TO_BE_CHECKED
    if check:
        isort_args.insert(0, "--check")
        isort_args.insert(1, "--diff")
    session.run("isort", *isort_args)

    black_args = ["tests"] + FILES_TO_BE_CHECKED
    if check:
        black_args.insert(0, "--check")
        black_args.insert(1, "--diff")
    session.run("black", *black_args)


@nox.session
def dev(session):
    """
    Create a development environment in editable mode.

    Activate it by running `source .nox/dev/bin/activate`.
    """
    session.install("-e", ".[dev]")


@nox.session
def lint_pylint(session):
    """
    Run pylint.
    """
    session.install("-e", ".[lint_pylint]")
    args = [
        "tests",
    ] + FILES_TO_BE_CHECKED
    session.run("pylint", *args)


@nox.session
def typecheck(session):
    """
    Typecheck the code using mypy.
    """
    session.install("-e", ".[typecheck]")
    args = ["--strict"] + FILES_TO_BE_CHECKED
    session.run("mypy", *args)


@nox.session(python=PYTHON_VERSIONS)
def test(session):
    """
    Run the tests.

    Accepts an additional arguments which are passed to the unittest module.
    This can for example be used to selectively run test cases.
    """

    args = [".[test]"]
    if EDITABLE_TESTS:
        args.insert(0, "-e")
    session.install(*args)
    if session.posargs:
        session.run("coverage", "run", "-m", "unittest", session.posargs[0], "-v")
    else:
        session.run("coverage", "run", "-m", "unittest", "discover", "-v")
        session.run("coverage", "report", "-m", "--fail-under=100")
