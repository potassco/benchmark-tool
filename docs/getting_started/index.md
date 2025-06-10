

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
