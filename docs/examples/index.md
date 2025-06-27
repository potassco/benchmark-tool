---
hide:
  - navigation
---

# Examples

## Sequential Benchmark

The example assumes that you want to run a benchmark that shall be started using simple bash scripts. All the following instruction assume that the current working directory is the root directory of the benchmark-tool project. To begin, the two executables [clasp-3.4.0][1] and [runlim-2.0.0rc12][2] have to be copied (or symlinked) into the `./programs` folder.
Now, run:
`$ bgen ./runscripts/runscript-seq.xml`
This creates a set of start scripts in the `./output` folder.
To start the benchmark, run:
`$ ./output/clasp-big/houat/start.py`
Once the benchmark is finished, run:
`$ beval ./runscripts/runscript-seq.xml | bconv -o result.ods`
Finally, open the file:
`$ soffice result.ods`

## Cluster Benchmark

This example assumes that you want to run a benchmark on a cluster, i.g. on the [HPC][3] cluster at the university of Potsdam. Again, all the following instruction assume that the current working directory is the root directory of the benchmark-tool project. Once again make sure, the two executables [clasp-3.4.0][1] and [runlim-2.0.0rc12][2] have been copied (or symlinked) into the `./programs` folder.
Now, run:
`$ bgen ./runscripts/runscript-dist.xml`
This creates a set of start scripts in the `./output` folder.
To start the benchmark, run (on the cluster):
`$ ./output/clasp-one-as/hpc/start.sh`
Once the benchmark is finished, run:
`$ beval ./runscripts/runscript-dist.xml | bconv -o result.ods`
Finally, open the file:
`$ soffice result.ods`

## Runscripts
This tool comes with a [collection](https://github.com/potassco/benchmark-tool/blob/master/runscripts) of example runscripts to help you get started.

While [runscript-example.xml](https://github.com/potassco/benchmark-tool/blob/master/runscripts/runscript-example.xml) gives a small example on how basic sequential and cluster benchmarks can be defined. [runscript-seq.xml](https://github.com/potassco/benchmark-tool/blob/master/runscripts/runscript-seq.xml) and [runscript-dist.xml](https://github.com/potassco/benchmark-tool/blob/master/runscripts/runscript-dist.xml) show more possibilities. [runscript-all](https://github.com/potassco/benchmark-tool/blob/master/runscripts/runscript-all.xml) tries to be a most complete example runscript.

Examples for the encoding support feature can be found [here](../reference/encoding_support.md).

For a more detailed explanation of a runsript and its components check [here](../getting_started/bgen/runscript.md)

[1]: https://potassco.org/clasp/
[2]: https://github.com/arminbiere/runlim
[3]: https://www.uni-potsdam.de/en/zim/angebote-loesungen/hpc
