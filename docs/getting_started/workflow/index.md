---
title: "Generic workflow"
icon: "material/book-open-variant"
---

This section only describes the most basic and common use of the benchmark-tool.
For more information regarding each subcommand and their options check the corresponding section.

#### Generating  and running benchmarks

After installation you do not have to run the benchmark-tool inside benchmark-tool directory, but it is
recommended. If you do not, make sure that all mandatory folders are present. Those are `programs/` and `templates/`.

To start using the benchmark-tool create a new [runscript] or modify an existing one. Check that all
files/folders referenced in the runscript exist. These are most likely your benchmark instances/encodings,
templates and system-under-test. Also make sure, that the the `runlim` executable is inside the `programs/`
folder and any [custom resultparser][resparser] is correctly installed.
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

This newly created .xml file can then be used as input for the [conv] subcommand to generate an .ods file
and optionally an .ipynb jupyter notebook. By default only the time and timeout measures are displayed.
Further measures can be selected using the -m option.

```
btool conv -o <out.ods> <result.xml>
```

[dispatcher]: ../run_dist/index.md
[verify]: ../verify/index.md
[gen]: ../gen/index.md
[eval]: ../eval/index.md
[conv]: ../conv/index.md
[resparser]: ../../reference/resultparser.md
