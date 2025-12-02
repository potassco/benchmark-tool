---
hide:
  - navigation
---

# Examples

## Sequential Benchmark

The example assumes that you want to run a benchmark that shall be started using simple bash scripts. To begin, call `btool init` and copy (or symlink) the two executables [clasp-3.4.0][1] and [runlim][2]
into the `./programs` folder.  
Now, run:  
`$ btool gen ./runscripts/runscript-seq.xml`  
This creates a set of start scripts in the `./output` folder.  
To start the benchmark, run:  
`$ ./output/clasp-big/houat/start.py`  
Once the benchmark is finished, run:  
`$ btool eval ./runscripts/runscript-seq.xml | btool conv -o result.ods`  
Finally, open the file:  
`$ soffice result.ods`  

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
`$ btool eval ./runscripts/runscript-dist.xml | btool conv -o result.ods`  
Finally, open the file:  
`$ soffice result.ods`  

## Runscripts
This tool comes with a [collection](https://github.com/potassco/benchmark-tool/blob/master/runscripts) of example runscripts to help you get started.

While [runscript-example.xml](https://github.com/potassco/benchmark-tool/blob/master/runscripts/runscript-example.xml) gives a small example on how basic sequential and cluster benchmarks can be defined. [runscript-seq.xml](https://github.com/potassco/benchmark-tool/blob/master/runscripts/runscript-seq.xml) and [runscript-dist.xml](https://github.com/potassco/benchmark-tool/blob/master/runscripts/runscript-dist.xml) show more possibilities. [runscript-all](https://github.com/potassco/benchmark-tool/blob/master/runscripts/runscript-all.xml) tries to be a most complete example runscript.

Examples for the encoding support feature can be found [here](../reference/encoding_support.md).

For a more detailed explanation of a runscript and its components check [here](../getting_started/gen/runscript.md)

[1]: https://potassco.org/clasp/
[2]: https://github.com/arminbiere/runlim
[3]: https://www.uni-potsdam.de/en/zim/angebote-loesungen/hpc
