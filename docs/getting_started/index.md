

# Getting started

## Installation

The `setuptools` package is required to run the commands below.
We recommend the usage of conda, which already includes `setuptools` in its default python installation.

```bash
$ git clone https://github.com/potassco/benchmark-tool
$ cd benchmark-tool
$ conda create -n <env-name> python=3.10
$ conda activate <env-name>
$ pip install .
```

The provided default templates make use of [runlim](https://github.com/arminbiere/runlim) to supervise benchmark execution. If you want to use them, make sure to build the latest version and copy (or symlink) the executable into the `./programs` directory. You might have to adjust the version number inside the template, see [here](./bgen/templates.md#run-templates).

## Structure

The repository is structures as follows:
`./benchmarks/`: example benchmarks
`./docs/`: documentation
`./output/`: default output folder for the examples
`./programs/`: place solver/tool executables here
`./runscripts/`: contains example run-scripts, see [here](./bgen/runscript.md)
`./src/`: Python source files
`./templates/`: contains example script templates, see [here](./bgen/templates.md)


## Usage

You can check a successful installation by running

```bash
$ bgen -h
```

Supported entry points:
`bgen`  - creates start scripts
`beval` - evaluates solver runs
`bconv` - transforms output of beval into spreadsheets

A detailed description on how to use each component can be accessed via the sidebar.
