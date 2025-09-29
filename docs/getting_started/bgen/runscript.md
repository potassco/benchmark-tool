---
title: "Runscripts for Benchmarking"
---

A runscript defines all aspects of a benchmark set and the systems used to run
them. The following sections explain each part of a typical runscript, helping
you adapt an existing runscript or create a new one from scratch.

Various runscripts can be found on the [examples] page.

## Folder Structure

When running `bgen`, a folder structure is created. The name of the top-level
folder is specified by the root element in the runscript:

```xml
<runscript output="output-folder">
    ...
</runscript>
```

In this example, the top-level folder is named `output-folder`.

The second folder in the hierarchy represents the project, which will be
explained later.

The third folder corresponds to the name of the machine on which the benchmark
is run. Machines are defined in the runscript as follows:

```xml
<machine name="hpc" cpu="24x8xE5520@2.27GHz" memory="24GB"/>
```

!!! info
    The `cpu` and `memory` attributes are for informational purposes only.

    You can define any number of machines.

Within this folder, you will find the start scripts for launching the benchmark
and the resulting output. Results are organized as follows:

```
./results/<benchmark-name>/<system-name>-<system-version>-<setting>/<benchclass>/<instance>/<run>
```

## Configuration

Configurations are used to reference run templates. You can define any number
of configurations:

```xml
<config name="seq-generic" template="templates/seq-generic.sh"/>
```

For more information on the [template][run template] page.

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
system via the run template when this setting is selected.
- The `tag` attribute is an identifier used within the runscript to select
multiple settings at once.
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

## Job

A job defines additional arguments for individual runs. You can define any
number of jobs. There are two types: sequential jobs (`seqjob`) and distributed
jobs (`distjob`) for running benchmarks on a cluster.

A sequential job is identified by its `name` and sets the `timeout` (in
seconds) for a single run, the number of `runs` for each instance, and the
number of solver processes performed in `parallel`:

```xml
<seqjob name="seq-gen" timeout="900" runs="1" parallel="1"/>
```

A distributed job is also identified by its `name` and defines a `timeout` and
number of `runs`:

```xml
<distjob name="dist-gen" timeout="900" runs="1" script_mode="timeout"
         walltime="23h 59m 59s" cpt="4"/>
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
- A final optional attribute for distributed jobs  is `partition`, which
specifies the cluster partition name. The default is `kr`. Other values include
`short` and `long`. If `short` is used, the walltime cannot exceed 24 hours.
Note that these values depend on your cluster configuration.

!!! info
    If you have many runs, `script_mode=multi` can cause issues with the
    cluster's scheduler. Use `timeout` or dispatch the generated `.dist` jobs
    using `./dispatcher.py`.

## Benchmark/Instances

The benchmark element is mainly used to indicate the location of the instances. Any number of benchmarks can be defined.

```xml
<benchmark name="no-pigeons">
    ...
<benchmark/>
```

A benchmark is identified by its *name* and can contain any number of *folder* or *files* elements.
```xml
<folder path="benchmarks/clasp" enctag="tag1" group="true">
    <ignore prefix="pigeons"/>
    <encoding file="encodings/no-pigeons.lp"/>
<folder/>
```
Folder elements define a *path* to a folder containing instances. The folder is recursively searched. If there are several folders with instances, the folder where the instances are located is taken as a "domain" and there will be an additional separation of the results using these "domains".
If there are folders that should not be included in the benchmark instances, the *ignore* element can be used to define a *prefix* which will be ignored.

Instances can be grouped using the the optional boolean *group* attribute of the *folder* element. By default this value is set to `false`. If enbaled, instance files in the form `<instance>.<extension>` with the same 'instance' located in the same folder are grouped together. For example, if there where files `inst1.1.lp` and `inst1.2.1.lp` in the same folder, they would be grouped together to 'inst1' and the corresponding job would reference both files using `{run.files}` in the template.

It is also possible to specify any amount of encodings which should be called together with all instances in this folder by using the *encoding* element. Setting-depended encodings can be added by using the optional *enctag* attribute. A more detailed explanation with examples for encoding support can be found [here](../../reference/encoding_support.md).

```xml
<files path="benchmarks/clasp" enctag="tag1 tag2">
    <encoding file="default.lp"/>
    <add file="pigeons/pigeonhole11-unsat.lp"/>
</files>
```
Similar to folder, the *files* elements define a path to a folder containing instances, but specific instances have to be added manually using the *add* element. In the example above, only `benchmarks/clasp/pigeons/pigeonhole11-unsat.lp` is added.

Specified instance files can optionally be grouped together using the *group* attribute as seen below:

```xml
<files path="benchmarks/clasp">
    <add file="dir/inst1.lp" group="group1"/>
    <add file="dir/inst2.lp" group="group1"/>
</files>
```

Grouped instances have to be located in the same directory. If no groups are specified, instance files are not grouped.

The *files* element does also support instance- and setting-depended encodings. More information can be found [here](../../reference/encoding_support.md).

## Projects

Projects are used to combine all of the previous elements to define a complete benchmark. There are two ways to define projects, using the *runtag* or the *runspec* element. A project can contain any number of *runtag* and *runspec* elements.

```xml
<project name="clingo-basic" job="seq-gen">
    <runtag machine="hpc" benchmark="no-pigeons" tag="basic"/>
</project>
```

Each project is identified by its *name*. The value of *name* is also what gives the name of the seconds folder in the overall folder structure. *job* references a previously defined job to be used as a template for the benchmark.

The *runtag* element specifies a machine and benchmark (group of instances) to be run. One or multiple settings to be used can be selected by the *tag*. The special tag *all* can be used to select all settings. The system to be used is inferred through the setting.

In the above example all instances defined in the 'no-pigeons' benchmark are run using the 'seq-gen' job configuration on machine 'hpc' once for each setting with the tag 'basic'.

```xml
<project name="clingo-dist" job="dist-gen">
    <runspec machine="hpc" benchmark="no-pigeons" system="clingo" version="5.8.0" setting="setting-1"/>
</project>
```

Similar to the *runtag* element, the *runspec* element can be used to specify a machine and a benchmark. But in contrast to before, only a single *system* *version* with a single *setting* can be referenced.


[run template]: ./templates.md#run-templates
[result parser]: ../beval/index.md#resultparser
[single.dist]: https://github.com/potassco/benchmark-tool/blob/master/templates/single.dist
[templates]: templates.md#dist-templates
[examples]: ../../examples/index.md#runscripts
[SLURM documentation]: https://slurm.schedmd.com/sbatch.html
