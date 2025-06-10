---
title: "bgen"
icon: "material/play-outline"
---

# bgen

The bgen entry point can be used to generate the benchmark folder structure and create all benchmark scripts according to a provided runscript.

```
$ bgen ./runscripts/runscript-example.xml
```

Afterwards the benchmarks can be started by executing the `start.sh` or `start.py` script from within the folder corresponding to the machine, the benchmark should be run on (3 folders down from where *bgen* was called).

!!! info
    It is not necessary to use an sbatch command for these start files. The file itself will call a number of pbs files using sbatch in order to add your benchmark jobs to the cluster.








