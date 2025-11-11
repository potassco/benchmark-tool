# benchmarktool

A tool to easier generate, run and evaluate benchmarks.

## Installation

The `setuptools` package is required to run the commands below. We recommend
the usage of conda, which already includes `setuptools` in its default python
installation.

```bash
$ git clone https://github.com/potassco/benchmark-tool
$ cd benchmark-tool
$ conda create -n <env-name> python=3.10
$ conda activate <env-name>
$ pip install .
```

The documentation can be accessed [here](https://potassco.org/benchmark-tool/)
or build and hosted using:

```bash
$ pip install .[doc]
$ mkdocs serve
```

And afterwards accessed at `http://localhost:8000/systems/benchmark-tool/`.

## Usage

You can check a successful installation by running

```bash
$ btool -h
```

Supported subcommands in order of use:

- `init`       Prepare the benchmark environment
- `gen`        Generate scripts from runscript
- `run-dist`   Run distributed jobs
- `verify`     Check for runlim errors and re-run failed instances
- `eval`       Collect results
- `conv`       Convert results to ODS or other formats


For more information and examples check the documentation.

> **_NOTE:_** This project is still in active development. If you encounter any
> bugs, have ideas for improvement or feature requests, please open an issue.
