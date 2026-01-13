---
title: "Templates"
---

Templates control how scripts for benchmarking are generated. Run templates
(`.sh` scripts) are used for individual benchmark runs, while dist templates
(`.dist` scripts) serve distributed computation on clusters.

You can browse a curated collection of example templates in the [benchmark-tool
repository].

## Run Templates

Run templates define how each benchmark instance is executed. During script
generation, references within the template (e.g., `{files}`) are replaced
with corresponding values.

The following references are available:

- `files`: instance files
- `encodings`: encoding files used for this instance
- `root`: path to the benchmark-tool folder
- `timeout`: walltime for this run
- `memout`: memory limit for this run in MB (default: 20000)
- `solver`: solver or program used for this run
- `args`: additional arguments for the solver/program
- `options`: additional options

Most templates use the [runlim] program to supervise benchmark runs.

## Dist Templates

Dist templates define how jobs are grouped and executed on a cluster, including
job parameters such as walltime, environment setup, and job scheduling order.

Parameters can be set using the standard SLURM `#SBATCH` syntax.

The following references are available:

- `walltime`: overall time limit
- `cpt`: number of CPUs per task
- `partition`: cluster partition to use
- `dist_options`: additional options for distributed jobs (e.g., SLURM)
- `jobs`: list of jobs to run

[benchmark-tool repository]: https://github.com/potassco/benchmark-tool/blob/master/templates
[runlim]: https://github.com/arminbiere/runlim
