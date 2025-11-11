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

After using `btool init` in a directory of your choice, it will be structured as follows:

- `programs/`: Place solver/tool executables here
- `runscripts/`: Contains example [runscripts]
- `templates/`: Contains example script [templates]

[runscripts]: ../gen/runscript.md
[templates]: ../gen/templates.md