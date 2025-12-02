---
title: "Runscripts for Benchmarking"
---

A runscript defines all aspects of a benchmark set and the systems used to run
them. The following sections explain each part of a typical runscript, helping
you adapt an existing runscript or create a new one from scratch.

Various runscripts can be found on the [examples] page.

## Runscript Elements

A runscript element is defined as follows:

```xml
<runscript output="output-folder">
    ...
</runscript>
```

The `output` attribute specifies the top-level folder where all scripts and
results are stored.

### Machine Elements

The `runscript` element can contain any number of the `machine` elements:

```xml
<machine name="hpc" cpu="24x8xE5520@2.27GHz" memory="24GB"/>
```

The attributes are as follows:

- The `name` attribute identifies the machine.
- The `cpu` attribute describes the CPU of the machine.
- The `memory` attribute describes the available memory of the machine.

!!! info
    The `cpu` and `memory` attributes are for informational purposes only.

### Folder Structure

When running the `gen` subcommand with a runscript, a folder structure is created.

```text
<output>
└─ <project>
   └─ <machine>
      └─ results
         └─ <benchmark-set>
            └─ <sytem-name>-<system-version>-<setting>
               ├─ <benchclass>
               │  ├─ <instance>
               │  │  ├─ <run>
               │  │  ├─ ...
               │  │  └─ <run>
               │  ├─ ...
               │  └─ <instance>
               │     └─ ...
               ├─ ...
               └─ <benchclass>
                  └─ ...
```

1. The name of the top-level folder is specified by the `output` attribute of
the `runscript` element.
2. The second folder in the hierarchy represents the project, which will be
explained later.
3. The third folder corresponds to the name of the machine on which the
benchmark is run. Within this folder, you will find the start scripts for
launching the benchmark and the resulting output files.

## Configuration

Configurations are used to reference run templates. You can define any number
of configurations:

```xml
<config name="seq-generic" template="templates/seq-generic.sh"/>
```

For more information refer to the [template][run template] page.

## System

Systems are defined as follows:

```xml
<system name="clingo" version="5.8.0" measures="clingo" config="seq-generic"
        cmdline="--stats">
    ...
</system>
```

- The `name` and `version` attributes together specify the name of an executable
or script called `<name>-<version>`, which must be placed in the `./programs`
directory. For example, the solver referenced by the [run template] in the
configuration is `./programs/clingo-5.8.0`. You can freely modify this script
as needed.
- The `measures` attribute specifies the name of a [result parser] used during
benchmark result evaluation. This does not affect benchmark script generation.
- The `config` attribute refers to the configuration to use for running this
system.
- The `cmdline` attribute is optional and can be any string, which will be passed
to the system regardless of the setting.
- The `cmdline_post` attribute is similar but is placed after `setting.cmdline`
in the order of arguments.

A runscript can contain any number of systems, each with any number of
settings.

### Setting

Settings are identified by their `name` and define additional arguments and
encodings used by the system.

```xml
<setting name="setting-1" cmdline="--quiet=1,0" tag="basic">
    <encoding file="encodings/default.lp"/>
    <encoding file="extra.lp" tag="extra"/>
</setting>
```

- The `cmdline` attribute can be any valid string, which will be passed to the
system after `system.cmdline` when this setting is selected.
- The `cmdline_post` attribute is similar but is placed after `system.cmdline_post`
in the order of arguments.
- The `tag` attribute is a space seperated identifier used within the runscript
to select multiple settings at once.
- Each setting can contain any number of encoding elements.
    - The `file` attribute is a relative path from the directory where `bgen`
    is run to the encoding file.
    - If no `tag` is given, the encoding is passed to the system for all
    instances when this setting is selected.
    - If a `tag` is given, encoding usage is instance-dependent. Multiple
    encodings can be selected by using the same tag.
- The setting element also supports an optional `disttemplate` attribute. The
default value is `templates/single.dist`, which refers to [single.dist]. This
attribute is only relevant for distributed jobs. More information about dist
templates can be found on the [templates] page.
- Another optional attribute for distributed jobs is `distopts`, which allows
    you to add additional options for distributed jobs. `distopts` expects a
    comma-separated string of options. For example, `distopts="#SBATCH
    --hint=compute_bound,#SBATCH --job-name=\"my_benchmark_run\""` results in
    the following lines being added to the script:

    ```bash
    #SBATCH --hint=compute_bound
    #SBATCH --job-name="my_benchmark_run"
    ```

    The default template for distributed jobs uses SLURM; a comprehensive list
    of available options is provided in the [SLURM documentation].

To summarize, the commandline arguments will always be given to the
system-under-test in the following order:

```
system.cmdline setting.cmdline system.cmdline_post setting.cmdline_post
```

## Job

A job defines additional arguments for individual runs. You can define any
number of jobs. There are two types: sequential jobs (`seqjob`) and distributed
jobs (`distjob`) for running benchmarks on a cluster.

### Sequential Jobs

A sequential job is identified by its `name` and sets the `timeout` (in
seconds) for a single run, the number of `runs` for each instance, and
the number of solver processes executed in `parallel`. The optional
attribute `memout` sets a memory limit (in MB) for each run. If no limit
is set, a default limit of 2000 MB is used:

```xml
<seqjob name="seq-gen" timeout="900" runs="1" memout="1000" parallel="1"/>
```

### Distributed Jobs

A distributed job is also identified by its `name` and defines a `timeout`,
the number of `runs` and an optional `memout`:

```xml
<distjob name="dist-gen" timeout="900" runs="1" memout="1000"
        script_mode="timeout" walltime="23h 59m 59s" cpt="4"/>
```

Furthermore, a distributed job has the following additional attributes:

- The `walltime` sets an overall time limit for all runs in `[0-9]+d [0-9]+h
[0-9]+m [0-9]+s` format. Each value is optional and can be any integer, for
example, `12d 350s` sets the time to 12 days and 350 seconds. Alternatively, a
single value without a unit is interpreted as seconds.
- The `script_mode` attribute defines how runs are grouped and dispatched to
the cluster.
    - Value `multi` dispatches all runs individually for maximum
    parallelization. (In this mode the walltime is ignored.)
    - Value `timeout` dispatches groups of runs based on the `timeout` and
    `walltime` of the distributed job. Runs are gathered into groups such that
    the total time for each group is below the specified `walltime`. For
    example, if the `walltime` is 25 hours and you have 100 instances with a
    `timeout` of 1 hour each and 1 run each, there will be 4 groups of 25 runs
    each, which are dispatched separately.
- A final optional attribute for distributed jobs is `partition`, which
specifies the cluster partition name. The default is `kr`. Other values include
`short` and `long`. If `short` is used, the walltime cannot exceed 24 hours.
Note that these values depend on your cluster configuration.

!!! info
    If you have many runs, `script_mode=multi` can cause issues with the
    cluster's scheduler. Use `timeout` or dispatch the generated `.dist` jobs
    using `./dispatcher.py`.

## Benchmark Sets

The benchmark element defines a group of benchmark instances grouped into
classes to be run by systems. It is identified by its `name` and can contain
any number of `folder` or `files` elements:

```xml
<benchmark name="no-pigeons">
    ...
<benchmark/>
```

### Folder Elements

A `folder` element defines a `path` to a folder containing instances, which is
searched recursively. Each sub-folder folders with instances is treated as a
benchmark class, and results are separated accordingly:

```xml
<folder path="benchmarks/clasp" enctag="tag1" group="true">
    <ignore prefix="pigeons"/>
    <encoding file="encodings/no-pigeons.lp"/>
<folder/>
```

A folder `element` can have the following optional attributes:

- You can specify the optional `enctag` attribute to select encodings with
matching tags in setting definitions. These encodings are used with all
instances in this folder, when the corresponding setting is run. This topic is
discussed in more detail on the [encoding support] page.
- Instances can be grouped using the optional Boolean `group` attribute
(default is `false`). If enabled, instance files in same folder of form
`<instance>.<extension>` sharing the same prefix `<instance>` are passed
together to the system. For example, files `inst1.1.lp` and `inst1.2.lp` in the
same folder would be grouped as `inst1`.

A `folder` element can contain any number of `encoding` and `ignore` elements:

- To exclude folders from the benchmark, use the `ignore` element to define a
path `prefix` to be ignored.
- You can also specify encodings to be used with all instances in a folder
using the `encoding` element.

### File Elements

Instead of using a `folder` element to gather benchmark instances, you can also
manually add specific files using the `files` element:

```xml
<files path="benchmarks/clasp" enctag="tag1 tag2">
    <encoding file="default.lp"/>
    <add file="dir/inst1.lp" group="group1"/>
    <add file="dir/inst2.lp" group="group1"/>
</files>
```

The `files` element has the following optional attributes:

- The `path` attribute specifies the folder containing the instances to be added.
- The `enctag` attribute works the same way as for the `folder` element.

The `files` element can contain any number of `encoding` and `add` elements:

- The add element specifies a file to be added to the benchmark. The `file`
attribute gives the path to the instance relative to the `path` attribute of
its parent `files` element.
- Instance files can optionally be grouped together using the `group`
attribute. Groups of instances have to be located in the same directory and are
passed together to the system.

## Projects

Projects combine all previous elements to define a complete benchmark.

```xml
<project name="clingo-basic" job="seq-gen">
    ...
</project>
```

A `project` element has the following attributes:

- Each project is identified by its `name`, which also determines the name of
the second folder in the overall folder structure.
- The `job` attribute references a previously defined job to use as a template
for the benchmark.

There are two ways to define projects: using the `runtag` or the `runspec`
element. A project can contain any number of `runtag` and `runspec` elements.

### Runtag Elements

The `runtag` element specifies a machine and benchmark set to run:

```xml
<runtag machine="hpc" benchmark="no-pigeons" tag="basic"/>
```

It has the following attributes:

- The `machine` attribute references a previously defined machine.
- The `benchmark` attribute references a previously defined benchmark set.
- The `tag` attribute specifies one or multiple setting tags to be used. Only
settings with matching tags are selected. The tag may use `|` for disjunction and
spaces for conjunction. The disjunction has higher precedence, e.g., a runtag with
the tag `base | foo bar` selects settings, which either have `base` or both `foo`
and `bar` in their tags. A setting with only the tag `bar` would not be selected.
To include all settings, use the special `*all*` tag.

In the above example all instances defined in the `no-pigeons` benchmark are
run using the `seq-gen` job configuration on machine `hpc` once for each
setting with the tag `basic`.

### Runspec Elements

Finally, the `project` element can also contain `runspec` elements to select
explicitly a single machine, benchmark, system, version, and setting:

```xml
<runspec machine="hpc" benchmark="no-pigeons" system="clingo" version="5.8.0"
    setting="setting-1"/>
```

The attributes are as follows:

- The `machine` attribute references a previously defined machine.
- The `benchmark` attribute references a previously defined benchmark set.
- The `system` and `version` attributes reference a previously defined system.
- The `setting` attribute references a previously defined setting of the selected

[run template]: ./templates.md#run-templates
[result parser]: ../../reference/resultparser.md
[single.dist]: https://github.com/potassco/benchmark-tool/blob/master/templates/single.dist
[templates]: templates.md#dist-templates
[examples]: ../../examples/index.md#runscripts
[SLURM documentation]: https://slurm.schedmd.com/sbatch.html
[encoding support]: ../../reference/encoding_support.md
