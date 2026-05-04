
# Running Benchmarks

This page gives some examples on how to use the benchmark tool.

To get started install the benchmark tool as described [here][install], call `btool init`
and copy (or symlink) the two executables [clasp-3.4.0][1] and [runlim][2]
into the `./programs` folder.

=== "Sequential"

    This example assumes that you want to run a benchmark that shall be started using simple
    bash scripts.  
    After finishing the preparation described above, run:  
    `$ btool gen ./runscripts/runscript-seq.xml`  
    This creates a set of start scripts in the `./output` folder.  
    To start the benchmark, run:  
    `$ ./output/clasp-big/houat/start.py`  
    Once the benchmark is finished, run:  
    `$ btool eval ./runscripts/runscript-seq.xml | btool conv -o result.xlsx`  
    Finally, open the file in your favourite spreadsheet tool:  
    `$ xdg-open result.xlsx`  

=== "Distributed (Cluster)"

    This example assumes that you want to run a benchmark on a cluster.  
    After finishing the preparation described above, run:  
    `$ btool gen ./runscripts/runscript-dist.xml`  
    This creates a set of start scripts in the `./output` folder.  
    To start the benchmark, run (on the cluster):  
    `$ ./output/clasp-one-as/hpc/start.sh`  
    Once the benchmark is finished, run:  
    `$ btool eval ./runscripts/runscript-dist.xml | btool conv -o result.xlsx`  
    Finally, open the file in your favourite spreadsheet tool:  
    `$ xdg-open result.xlsx`  

[install]: ../getting_started/index.md#installation
[1]: https://potassco.org/clasp/
[2]: https://github.com/arminbiere/runlim
[3]: https://www.uni-potsdam.de/en/zim/angebote-loesungen/hpc
