# Getting started

## Installation

The `setuptools` package is required to run the commands below. We recommend
using conda, which includes `setuptools` in its default Python installation.
Any python version newer than 3.10 is supported. To install the tool, either
clone the [repository][btool] or download the latest release and run the
following commands:

```bash
git clone https://github.com/potassco/benchmark-tool
cd benchmark-tool
conda create -n <env-name> python=3.10
conda activate <env-name>
pip install .
```

The provided default templates use [runlim] to supervise benchmark execution.
If you want to use them, make sure to build the latest version and copy (or
symlink) the executable into the `./programs` directory.

## Structure

The repository is organized as follows:

- `./benchmarks/`: Example benchmarks
- `./docs/`: Documentation
- `./output/`: Default output folder for the examples
- `./programs/`: Place solver/tool executables here
- `./runscripts/`: Contains [example run-scripts][runscript]
- `./src/`: Python source files
- `./templates/`: Contains [example script templates][script]

## Usage

You can verify a successful installation by running:

```bash
btool -h
```

Supported subcommands in order of use:

- `gen`        Generate scripts from runscript
- `run-dist`   Run distributed jobs
- `verify`     Check for runlim errors
- `eval`       Collect results
- `conv`       Convert results to ODS or other formats


Each subcommand has their own help page, which you can access using:
```bash
btool <subcommand> -h
```

A generic workflow and detailed descriptions on how to use each component is
available via the sidebar.

!!! info
    When running benchmarks on a cluster, jobs may fail due to the following error:

    ```
    runlim error: group pid <X> larger than child pid <Y>
    ```

    This is a known [issue].

    For single-process systems under test (SUT), this issue can be avoided by
    using the `runlim` option `--single` in the corresponding template script
    (e.g., `templates/seq-generic-single.sh`). In that case, `{run.solver}`
    should either be the SUT executable or you should use `exec` if
    `{run.solver}` refers to a shell script.

    If you cannot use `--single`, the `verify` subcommand can
    be used to identify jobs that failed due to a `runlim error` and remove the
    corresponding `.finished` files. The `gen` subcommand can then generate a
    new start script, which excludes valid jobs, by using the `-e` option.

[btool]: https://github.com/potassco/benchmark-tool
[runlim]: https://github.com/arminbiere/runlim
[template]: ./gen/templates.md#run-templates
[runscript]: ./gen/runscript.md
[script]: ./gen/templates.md
[issue]: https://github.com/arminbiere/runlim/issues/8
[results]: https://github.com/potassco/benchmark-tool/blob/master/verify_results.sh
