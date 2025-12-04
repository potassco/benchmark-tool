# benchmarktool

A tool to easier generate, run and evaluate benchmarks.

## Installation

The benchmark tool can be installed with any Python version newer than 3.10
using pip:

```bash
pip install potassco-benchmark-tool
```

To access the latest updates and fixes you can either use:

```bash
pip install git+https://github.com/potassco/benchmark-tool
```

Or alternatively build the tool yourself, which requires the `setuptools`
package. We recommend using conda, which includes `setuptools` in its default
Python installation. To build the tool manually run the following commands:

```bash
git clone https://github.com/potassco/benchmark-tool
cd benchmark-tool
conda create -n <env-name> python=3.10
conda activate <env-name>
pip install .
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

- `init` Prepare the benchmark environment
- `gen` Generate scripts from runscript
- `run-dist` Run distributed jobs
- `verify` Check for runlim errors and re-run failed instances
- `eval` Collect results
- `conv` Convert results to spreadsheet and more

For more information and examples check the documentation.

> **_NOTE:_** This project is still in active development. If you encounter any
> bugs, have ideas for improvement or feature requests, please open an issue.
