---
title: "Gathering Benchmark Results"
icon: "material/play-outline"
---

The `eval` subcommand is used to collect all relevant results from a
benchmark run and save them to an XML file. To do this, pass the same
[runscript] used for benchmark script generation as an argument:

```
btool eval ./runscripts/runscript-example.xml > benchmark-results.xml
```

The `--par-x` option can be used to set the factor for the
penalized-average-runtime score (default: 2).

Results are written in XML format to standard output, so it is recommended to
redirect the output to a file.

!!!info
    The evaluation of results is controlled by the `measures` attribute of the
    [system element] in the runscript. Use a module name without `.py`, such as
    `clasp` or `clasp_json` for a built-in parser, or `custom_parser` for a file
    named `resultparsers/custom_parser.py` in your current working directory.
    Local parsers take precedence over built-in parsers with the same name.

    For more details, see the [result parser documentation][result parser].

[runscript]: ../gen/runscript.md
[system element]: ../gen/runscript.md#system
[result parser]: ../../reference/resultparser.md
