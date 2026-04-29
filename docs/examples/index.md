---
hide:
  - navigation
---

# Examples

## Sequential Benchmark

The example assumes that you want to run a benchmark that shall be started using simple bash scripts.
To begin, call `btool init` and copy (or symlink) the two executables [clasp-3.4.0][1] and [runlim][2]
into the `./programs` folder.  
Now, run:  
`$ btool gen ./runscripts/runscript-seq.xml`  
This creates a set of start scripts in the `./output` folder.  
To start the benchmark, run:  
`$ ./output/clasp-big/houat/start.py`  
Once the benchmark is finished, run:  
`$ btool eval ./runscripts/runscript-seq.xml | btool conv -o result.xlsx`  
Finally, open the file in your favourite spreadsheet tool:  
`$ xdg-open result.xlsx`  

## Cluster Benchmark

This example assumes that you want to run a benchmark on a cluster. Once again,
call `btool init` and make sure, the two executables [clasp-3.4.0][1]
and [runlim][2] have been copied (or symlinked) into the `./programs` folder.  
Now, run:  
`$ btool gen ./runscripts/runscript-dist.xml`  
This creates a set of start scripts in the `./output` folder.  
To start the benchmark, run (on the cluster):  
`$ ./output/clasp-one-as/hpc/start.sh`  
Once the benchmark is finished, run:  
`$ btool eval ./runscripts/runscript-dist.xml | btool conv -o result.xlsx`  
Finally, open the file in your favourite spreadsheet tool:  
`$ xdg-open result.xlsx`  

## Runscripts
A collection of example runscripts to help you get started can be found either in the
`./runscripts` directory after executing `btool init` or [here][runscripts].

While [runscript-example.xml][runscript-example] gives a small example on how basic sequential
and cluster benchmarks can be defined. [runscript-seq.xml][runscript-seq] and
[runscript-dist.xml][runscript-dist] show more possibilities. [runscript-all][runscript-all]
tries to be a most complete example runscript.

Examples for the encoding support feature can be found [here](../reference/encoding_support.md).

For a more detailed explanation of a runscript and its components check
[here](../getting_started/gen/runscript.md)

[1]: https://potassco.org/clasp/
[2]: https://github.com/arminbiere/runlim
[3]: https://www.uni-potsdam.de/en/zim/angebote-loesungen/hpc
[runscripts]: https://github.com/potassco/benchmark-tool/tree/master/src/benchmarktool/init/runscripts
[runscript-example]: https://github.com/potassco/benchmark-tool/blob/master/src/benchmarktool/init/runscripts/runscript-example.xml
[runscript-seq]: https://github.com/potassco/benchmark-tool/blob/master/src/benchmarktool/init/runscripts/runscript-seq.xml
[runscript-dist]: https://github.com/potassco/benchmark-tool/blob/master/src/benchmarktool/init/runscripts/runscript-dist.xml
[runscript-all]: https://github.com/potassco/benchmark-tool/blob/master/src/benchmarktool/init/runscripts/runscript-all.xml
