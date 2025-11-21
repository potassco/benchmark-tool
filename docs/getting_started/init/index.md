---
title: "Initilaize benchmark environment"
icon: "material/play-outline"
---

The `init` subcommand can be used to prepare the necessary folder structure to run
the benchmarktool and provide some example [runscripts] and script [templates]. By
default existing files are not overwritten.

```bash
btool init
```

The `-o, --overwrite` option can be used to overwrite existing files.

You can use the `--resultparser-template` option to create a copy of the `clasp` resultparser
called `rp_tmp.py`, which you can use as a base to create your own. You can overwrite the
default `clasp` resultparser by providing `claps.py` inside the resultparsers folder.
More information on how to modify resultparsers can be found in the corresponding
section[resultparsers]

After using `btool init` in a directory of your choice, it will be structured as follows:

- `programs/`: Place solver/tool executables here
- `resultparsers/`: Place custom [resultparsers] here
- `runscripts/`: Contains example [runscripts]
- `templates/`: Contains example script [templates]

[resultparsers]: ../../reference/resultparser.md
[runscripts]: ../gen/runscript.md
[templates]: ../gen/templates.md
