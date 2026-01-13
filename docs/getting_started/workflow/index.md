---
title: "Generic workflow"
icon: "material/book-open-variant"
---

This section only describes the most basic and common use of the benchmark-tool.
For more information regarding each subcommand and their options check the corresponding section.

#### Generating  and running benchmarks

After installation you can create the required directory structure for the benchmark tool using
the [init] subcommand:

```
btool init
```

Afterwards you should see the following folders:

- `programs/`: Place solver/tool executables here
- `resultparsers/`: Place custom [resultparsers][resparser] here
- `runscripts/`: Contains example [runscripts]
- `templates/`: Contains example script [templates]

If you want to create a new [resultparser][resparser] or want to modify the provided one, you can use
`btool init --resultparser-template` to also create a copy of the clasp resultparser as `rp_tmp.py`.

To start using the benchmark-tool create a new [runscript] or modify an existing one. Check that all
files/folders referenced in the runscript exist. These are most likely your benchmark instances/encodings,
templates and system-under-test. Also make sure, that the the `runlim` executable is inside the `programs/`
folder and any [custom resultparser][resparser] is placed inside the `resultparsers/` folder.
If everything is setup you can generate you benchmarks using the [gen] subcommand:

```
btool gen <runscript.xml>
```

Afterwards, you should see an output folder with your specified name, which contains all your benchmarks.
Check the [runscript] section to see how the benchmarks are structured.

You can start your benchmarks by running the `start.py` script for sequential jobs or the `start.sh` script
for distributed jobs. Both types of scripts can be found inside the `<output>/<project>/<machine>/` folder.
Alternatively you can use the [dispatcher] `btool run-dist` to schedule your distributed jobs.

After running all your benchmarks you can continue to the evaluation step. Optionally you can use the
[verify] subcommand to check for runlim errors inside your results.

!!! info
    At the moment all projects defined inside a runscript have to be run before an evaluation is
    possible.

#### Evaluating the results

To evaluate your benchmarks and collect the results use the [eval] subcommand:

```
btool eval <runscript.xml> > <results.xml>
```

This newly created .xml file can then be used as input for the [conv] subcommand to generate an .xls
file and optionally an .ipynb jupyter notebook. By default only the time and timeout measures are displayed. Further measures can be selected using the -m option.

```
btool conv -o <out.xls> <result.xml>
```

[runscripts]: ../gen/runscript.md
[templates]: ../gen/templates.md
[dispatcher]: ../run_dist/index.md
[verify]: ../verify/index.md
[init]: ../init/index.md
[gen]: ../gen/index.md
[eval]: ../eval/index.md
[conv]: ../conv/index.md
[resparser]: ../../reference/resultparser.md
