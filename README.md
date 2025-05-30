# benchmarktool

A tool to easier generate, run and evalute benchmarks.

## Structure

`benchmarks/` - example benchmarks
`doc/`      - documentation
`output/`    - default output folder for the examples
`programs/`   - should contain solver/tool executables
`runscripts/` - contains example run-scripts
`src/`       - Python source files
`templates/`  - contains example call-scripts

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

## Usage

You can check a successful installation by running

```bash
$ bgen -h
```

Supported entry points:
`bgen`  - creates start scripts
`beval` - evaluates solver runs
`bconv` - transforms output of eval into spreadsheets

For more information and examples check `./doc/`.

> **_NOTE:_**  
This project is still in active development. 
If you encounter any bugs, have ideas for improvement or feature requests, please open an issue.