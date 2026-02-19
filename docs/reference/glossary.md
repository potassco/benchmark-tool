---
title: "Glossary"
icon: "material/book-search"
---


# Glossary

**btool**: The command-line tool used to initialize, generate, run, and evaluate benchmarks.
Subcommands include `init`, `gen`, `run-dist`, `eval`, `conv`, and `verify`.

**runlim**: A utility used to enforce resource limits (such as time and memory) on benchmark
runs. The `runlim` executable should be placed in the `programs/` directory and is used by
the generated scripts to control execution.

**SUT (System Under Test)**: The system being benchmarked. Each SUT, or a script calling it,
should be placed in the `programs/` directory and named according to the `<system>-<version>`
convention.

**template**: A shell script or file that defines how a system is executed during benchmarking.
Templates are referenced by configurations in the runscript and are stored in the `templates/`
directory.

**resultparser**: A script or tool that processes the output of benchmark runs to extract
relevant measures and results. Custom resultparsers can be placed in the `resultparsers/`
directory and referenced in the runscript via the `measures` attribute of a system.

**start.py / start.sh**: Scripts generated for launching benchmarks. `start.py` is used
for sequential jobs, and `start.sh` for distributed jobs. They are found in the output
structure under `<output>/<project>/<machine>/`.


## btool Subcommands

**init**: Initializes the required directory structure and files for the benchmark tool,
creating folders such as `programs/`, `resultparsers/`, `runscripts/`, and `templates/`.

**gen**: Generates the benchmark scripts and output folder structure from a given runscript
XML file.

**run-dist**: Schedules or dispatches distributed jobs (e.g., on a cluster) using the generated
scripts. Used for running distributed benchmarks.

**eval**: Evaluates the results of completed benchmarks, collecting and summarizing measures
into a results XML file.

**conv**: Converts results from XML format to other formats, such as Excel (.xlsx) or Jupyter
notebooks (.ipynb), for further analysis or reporting.

**verify**: Checks benchmark results for errors, such as runlim errors, to ensure the integrity
and correctness of the results.


## Directory Structure (created by `btool init`)

**programs/**: Directory for solver or tool executables and scripts. Each system-under-test
should be placed here, named as `<system>-<version>` to match the runscript.

**resultparsers/**: Directory for custom result parser scripts. Place any custom or provided
resultparser (e.g., `rp_tmp.py`) here.

**runscripts/**: Directory containing example or user-defined runscript XML files that describe
benchmark setups.

**templates/**: Directory for script templates used to generate run and distributed job scripts.
Contains example templates referenced by configurations in the runscript.


## Runscript Elements

**runscript**: The root element defining the benchmark set, systems, and output folder for
a benchmark run.

**machine**: Describes a machine used for benchmarking, including its name, CPU, and memory
(informational only).

**config**: Defines a configuration referencing a run template, specifying how systems are
executed.

**system**: Specifies a solver or tool to be benchmarked, including its name, version,
configuration, and command-line arguments. References a system-under-test/script inside
the `programs/` folder with the name `<system>-<version>`.

**setting**: Defines a configuration for a system, including command-line arguments, encodings,
tags, and variables for generating multiple settings.

**encoding**: Specifies a logic program or file to be used as part of a setting or benchmark
instance.

**variable**: Used within a setting to generate multiple settings by varying command-line
arguments or other parameters.

**job**: Template for how runs are executed, including sequential (`seqjob`) and distributed
(`distjob`) jobs, with attributes for timeout, runs, memory, and parallelism.

**seqjob**: A sequential job specifying timeout, number of runs, memory limit, and parallelism
for each run.

**distjob**: A distributed job for cluster execution, with attributes for timeout, runs, memory, walltime, script mode, and partition.

**benchmark**: Defines a set of benchmark instances, organized into classes, to be run by
systems.

**folder**: Specifies a directory containing benchmark instances, with options for encoding
tags, grouping, and command-line arguments.

**ignore**: Excludes folders or files from a benchmark by prefix.

**files**: Manually adds specific files as benchmark instances, with options for encoding tags
and grouping.

**add**: Used within `files` to add a specific file as a benchmark instance, with optional
grouping and command-line arguments.

**spec**: Loads benchmark specifications from `spec.xml` files, with options for instance tags
and recursive search.

**class**: Used in `spec.xml` to group instances, with a name and optional encoding tag.

**instance**: Specifies a single benchmark instance file, with optional tags, grouping, and
command-line arguments.

**project**: Combines all elements to define a complete benchmark setup, including the job,
machines, and benchmarks to run.

**runtag**: Specifies a machine and benchmark set to run, with optional setting tags for selection.

**runspec**: Explicitly specifies a single machine, benchmark, system, version, and setting to
use for a run.
