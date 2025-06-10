---
title: "Templates"
---

# Templates

Templates are used to simplify the creation of different scripts. While run templates (`.sh` scripts) are used to generate scripts for individual benchmark runs, pbs templates (`.pbs` scripts) are used to enable computation on a cluster.

A collection of templates can be found [here](https://github.com/potassco/benchmark-tool/blob/master/templates).

## Run Templates
A run template dictates how each benchmark instance should be run. During generation the references inside the template, e.g. `run.file`, are replaced by the corresponding values.
The following references can currently be used:  
`run.file`: the instance file  
`run.encodings`: encoding files to be used for this instance  
`run.root`: the path to the benchmark-tool folder  
`run.timeout`: the walltime for this run  
`run.solver`: the solver/program to be used for this run
`run.args`: additional arguments to be used by the solver/program


Most templates make use of the [runsolver](http://www.cril.univ-artois.fr/~roussel/runsolver/) program to supervise the benchmark runs.

!!! info
    When using the provided templates you might have to update the runsolver version inside the template.

## Pbs Templates

Pbs templates describes how a single new job will look like, when grouping multiple jobs together to run on a cluster. This includes setting job parameters such as walltime, loading the environment and deciding in which order the jobs will be run.

While parameters can be set using the default `#SBATCH` syntax of SLURM, environments can be loaded explicitly in this file or by sourcing a `.bashrc`file.

To be able to load modules installed on the cluster, e.g. anaconda, use:
```bash
source /etc/profile.d/modules.sh

module load lang/Anaconda3/2024.02-1
source activate <env-name>
```