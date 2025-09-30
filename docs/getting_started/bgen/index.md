---
title: "Generating Benchmarks Scripts"
icon: "material/play-outline"
---

The `bgen` tool helps you set up the folder structure and scripts needed to run
your benchmarks efficiently. It automates the creation of directories and job
scripts based on your configuration.

To generate the benchmark folder structure and scripts, use the following
command:

```bash
bgen ./runscripts/runscript-example.xml
```

After generation, start your benchmarks by executing either the `start.sh` or
`start.py` file found in the `machine` subfolder of the generated structure.

!!! info
    You do not need to manually use the `sbatch` command for these start files.
    The start script will automatically submit the relevant `.dist` job files
    to the cluster using `sbatch`.
