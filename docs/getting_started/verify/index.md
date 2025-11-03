---
title: "Result verifier"
icon: "material/play-outline"
---

The `verify` subcommand can be used to check the benchmark results inside a
given folder for runlim errors and remove the .finished files for affected
instances. To run the command simply provide the folder to check.

```bash
btool verify <folder>
```

!!!info
    Afterwards you can re-generate the start scripts, excluding finished/valid
    instances, by using the `gen` subcommand with the `-e` option.
