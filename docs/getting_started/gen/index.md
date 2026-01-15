---
title: "Generating Benchmarks Scripts"
icon: "material/play-outline"
---

The `gen` subcommand helps you set up the folder structure and scripts needed to run
your benchmarks efficiently. It automates the creation of directories and job
scripts based on your configuration.

To generate the benchmark folder structure and scripts, use the following
command:

```bash
btool gen ./runscripts/runscript-example.xml
```

You can use the `-e, --exclude` option to exclude previously finished benchmarks
in the start script, thus avoiding running them again.

If the output directory, specified in the runscript, already exists, the program
is interrupted. The `-f, --force` option can be used to disable this behaviour
and overwrite existing files.

After generation, start your benchmarks by executing either the `start.sh` or
`start.py` file found in the `machine` subfolder of the generated structure.
If you want to run your generated benchmark set on a cluster and it consists of
many jobs, you can use the `run-dist` subcommand to dispatch jobs to the cluster
without overloading the queue. Make sure to use a `run-dist` inside a persistent
shell (tmux, screen, ...).

!!! info
    You do not need to manually use the `sbatch` command for these start files.
    The start script will automatically submit the relevant `.dist` job files
    to the cluster using `sbatch`.
