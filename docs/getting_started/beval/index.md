---
title: "beval"
icon: "material/play-outline"
---

# beval

The beval entry point can be used to gather all relevant results of a benchmark run and save them into an xml file. To do so the same [runscript](../bgen/runscript.md) used for the benchmark script generation has to be to passed as an argument.

```bash
$ beval ./runscripts/runscript-example.xml > benchmark-results.xml
```

The script writes the results in xml format to the standard output. It is recommended to save the result in a file by redirecting the output.

## Resultparser

How the results are evaluated is decided by the the value of the *measures* attribute of the [*system*](../bgen/runscript.md#system) element inside the runscript. The value of *measures* is a reference to a python file located in the `/src/benchmarktool/resultparser` directory.

This file has to contain a `parse()` function, which parses relevant statistics from the result files.

More information regarding the result parser can be found [here](../../reference/resultparser.md).

