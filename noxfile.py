import os
import sys

import nox

nox.options.sessions = "lint_pylint", "typecheck", "test"

EDITABLE_TESTS = True
PYTHON_VERSIONS = None
if "GITHUB_ACTIONS" in os.environ:
    PYTHON_VERSIONS = ["3.9", "3.11"]
    EDITABLE_TESTS = False

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
        "src/benchmarktool/tools.py",
        "src/benchmarktool/result/ods_gen.py",
        "src/benchmarktool/runscript/parser.py", 
        "src/benchmarktool/runscript/runscript.py",
        #"src",
        "tests",
    ]
    if check:
        autoflake_args.remove("--in-place")
    session.run("autoflake", *autoflake_args)

    #isort_args = ["--profile", "black", "src", "tests"]
    isort_args = [
        "--profile", 
        "black",
        "src/benchmarktool/tools.py",
        "src/benchmarktool/runscript/parser.py", 
        "src/benchmarktool/runscript/runscript.py", 
        "src/benchmarktool/result/ods_gen.py",
        "tests"
    ]
    if check:
        isort_args.insert(0, "--check")
        isort_args.insert(1, "--diff")
    session.run("isort", *isort_args)

    #black_args = ["src", "tests"]
    black_args = [
        "src/benchmarktool/tools.py",
        "src/benchmarktool/runscript/parser.py", 
        "src/benchmarktool/runscript/runscript.py",
        "src/benchmarktool/result/ods_gen.py", 
        "tests"
    ]
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
    session.run(
        "pylint",
        "src/benchmarktool/tools.py",
        "src/benchmarktool/result/ods_gen",
        "tests",
        "src/benchmarktool/runscript/parser",
        "src/benchmarktool/runscript/runscript",
    )
    #session.run("pylint", "benchmarktool", "tests")


@nox.session
def typecheck(session):
    """
    Typecheck the code using mypy.
    """
    session.install("-e", ".[typecheck]")
    session.run("mypy", "--strict", "src/benchmarktool/result/ods_gen.py", "src/benchmarktool/tools.py")
    session.run("mypy", "--strict", "src/benchmarktool/runscript/parser.py", "src/benchmarktool/runscript/runscript.py")
    session.run("mypy", "--strict", "-p", "tests")


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
