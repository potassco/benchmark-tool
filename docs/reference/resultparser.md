---
title: "Modifying Resultparser"
icon: "material/text-box-check-outline"
---

# Modifying the Resultparser

The built-in [clasp][clasp] and [clasp_json][clasp_json] resultparsers extract
statistics from clasp/clingo text and JSON output, respectively. You can extend
these parsers or write a custom parser for another program.

## Selecting a parser

Run `btool init` to create the `resultparsers/` directory. Save custom parsers
there and set the `measures` attribute of the [system element] to the module
name without `.py`. For example, `measures="custom_parser"` loads
`resultparsers/custom_parser.py` relative to the directory where you run
`btool eval`.

Local parsers take precedence over built-in parsers. A local
`resultparsers/clasp.py` overrides the built-in `clasp` parser.

You can run `btool init --resultparser-template` to create `rp_tmp.py` in
the current directory as a copy of the built-in text parser.

## Parser interface

Every parser must define a callable with this signature:

```text
parse(path, runspec, instance, run) -> dict[str, tuple[str, Any]]
```

The function is called once per repetition of each benchmark instance:

| Argument | Meaning |
| --- | --- |
| `path` | Directory containing the output of this individual run, not the benchmark root. |
| `runspec` | A `benchmarktool.runscript.runscript.Runspec` describing the system, setting, project, and job. For example, `runspec.project.job.timeout` is the time limit in seconds. |
| `instance` | A `benchmarktool.runscript.runscript.Benchmark.Instance` describing the benchmark instance, including its name and input paths. |
| `run` | Repetition number, starting at **1**. |

Return a dictionary mapping each measure name to a `(data_type, value)` pair. Use `"float"` for numeric measures and `"string"` for
text measures. For example:

```text
{"time": ("float", 40.0), "timeout": ("float", 0), "status": ("string", "SATISFIABLE")}
```

The built-in parsers also report numeric `error` and `memout` flags. Reuse a
built-in parser when extending clasp/clingo output to retain its handling of
errors, timeouts, and memory limits. When both `time` and `timeout` are present,
`btool eval` adds the PAR score using the factor selected by `--par-x`.

## Adding your own statistics

Suppose your program produces normal clasp/clingo text output plus this line
in `runsolver.solver`:

```text
Time to run function: 20.23s
```

Save the following complete parser as `resultparsers/custom_parser.py`. It
keeps the built-in measures, adds a numeric `function_time`, and labels it
`"acceptable"` only when it is less than half the total runtime:

```python
import re
from typing import Any

from benchmarktool.resultparser import open_results
from benchmarktool.resultparser.clasp import parse as parse_clasp
from benchmarktool.runscript import runscript

FUNCTION_TIME = re.compile(r"^Time to run function:\s*(?P<val>[0-9]+(?:\.[0-9]+)?)s\s*$")


def parse(
    path: str,
    runspec: runscript.Runspec,
    instance: runscript.Benchmark.Instance,
    run: int,
) -> dict[str, tuple[str, Any]]:
    result = parse_clasp(path, runspec, instance, run)
    with open_results(path, "runsolver.solver") as output:
        for line in output:
            match = FUNCTION_TIME.match(line)
            if match:
                function_time = float(match.group("val"))
                result["function_time"] = ("float", function_time)
                result["function_time_status"] = (
                    "string",
                    "acceptable" if function_time < result["time"][1] / 2 else "unacceptable",
                )
                return result
    raise ValueError(f"Missing or invalid function time for instance {instance.name!r}, run {run}: {path}")
```

`open_results` supports both plain output files and files compressed with gzip
(`runsolver.solver.gz`). The example expects the custom statistic to be present;
it raises an explicit error rather than inventing a value if the line is missing
or malformed. If you add this statistic to a copied parser's regex dictionary
instead, remember to match the trailing `s` and store results using dictionary
assignment, for example `result["function_time"] = ("float", value)`.

In your existing runscript, set `measures="custom_parser"` on the relevant
`<system>` element. After running the benchmark, collect and display the new
measures:

```bash
btool eval ./runscripts/runscript-example.xml > benchmark-results.xml
btool conv -m time:t,timeout:to,function_time,function_time_status -o result.xlsx benchmark-results.xml
```

[system element]: ../getting_started/gen/runscript.md#system
[clasp]: https://github.com/potassco/benchmark-tool/blob/master/src/benchmarktool/resultparser/clasp.py
[clasp_json]: https://github.com/potassco/benchmark-tool/blob/master/src/benchmarktool/resultparser/clasp_json.py
