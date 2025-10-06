---
title: "Gathering Benchmark Results"
icon: "material/play-outline"
---

The `beval` entry point is used to collect all relevant results from a
benchmark run and save them to an XML file. To do this, pass the same
[runscript] used for benchmark script generation as an argument:

```bash
beval ./runscripts/runscript-example.xml > benchmark-results.xml
```

The `--par-x` option can be used to set the factor for the
penalized-average-runtime score (default: 2).

Results are written in XML format to standard output, so it is recommended to
redirect the output to a file.

!!!info
    The evaluation of results is controlled by the `measures` attribute of the
    [system element] in the runscript. This attribute should reference a Python
    file located in `src/benchmarktool/resultparser`.

    For more details, see the [result parser documentation][result parser].

[runscript]: ../bgen/runscript.md
[system element]: ../bgen/runscript.md#system
[result parser]: ../../reference/resultparser.md
