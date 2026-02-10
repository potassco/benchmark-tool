---
title: "Runscripts for Benchmarking"
---

A runscript defines all aspects of a benchmark set and the systems used to run
it. The following sections explain each part of a typical runscript, helping
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
results will be stored.


### Machine Elements

The `runscript` element can contain any number of `machine` elements:

```xml
<machine name="hpc" cpu="24x8xE5520@2.27GHz" memory="24GB"/>
```

The attributes are:

- `name`: Identifies the machine.
- `cpu`: Describes the machine's CPU.
- `memory`: Describes the available memory.

!!! info
    The `cpu` and `memory` attributes are for informational purposes only.

### Folder Structure

When running the `gen` subcommand with a runscript, the following folder
structure is created:

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

1. The name of the top-level folder is set by the `output` attribute of the
`runscript` element.
2. The second folder in the hierarchy represents the project (explained later).
3. The third folder is named after the machine on which the benchmark is run.
This folder contains the start scripts for launching the benchmark and the
resulting output files.


## Configuration

Configurations are used to reference run templates. You can define any number
of configurations:

```xml
<config name="seq-generic" template="templates/seq-generic.sh"/>
```

For more information, see the [template][run template] page.

## System

Systems are defined as follows:

```xml
<system name="clingo" version="5.8.0" measures="clingo" config="seq-generic"
        cmdline="--stats">
    ...
</system>
```

- `name` and `version`: Together, specify the name of an executable or script
`<name>-<version>`, which must be placed in the `./programs` directory. For
example, the solver referenced by the [run template] in the configuration is  
`./programs/clingo-5.8.0`. You can freely modify this script as needed.
- `measures`: The name of the [result parser] used to evaluate benchmark
results. This does not affect script generation.
- `config`: The configuration to use for running this system.
- `cmdline` (optional): Any string to be passed to the system, regardless of
the setting. Files should not be passed using the `cmdline`, since file paths
will be wrong.
- `cmdline_post` (optional): Like `cmdline`, but placed after `setting.cmdline`
in the argument order.

A runscript can contain any number of systems, each with any number of
settings.

Command-line arguments can be specified at the system, setting, or instance
level, using either the `cmdline` or `cmdline_post` attribute. By default,
the `seq-generic` run template arranges the command-line arguments in the
following order:

```
system.cmdline setting.cmdline instance.cmdline system.cmdline_post setting.cmdline_post instance.cmdline_post
```

If a different order is needed, simply modify the references in your template
accordingly.

### Setting

Settings are identified by their `name` and define additional arguments and
encodings used by the system.

```xml
<setting name="setting-1" cmdline="--quiet=1,0" tag="basic">
    <encoding file="encodings/default.lp"/>
    <encoding file="extra.lp" tag="extra"/>
    <variable cmd="--time-limit={}" value="30,100,30"/>
    <variable cmd="--memory-limit={}" value="1024;2048" post="true"/>
</setting>
```

A `setting` element can have the following optional attributes:

- `cmdline`: Any valid string, passed to the system after `system.cmdline` when
this setting is selected. Files should not be passed using the `cmdline`.
- `cmdline_post`: Like `cmdline`, but placed after `system.cmdline_post` in the
argument order.
- `tag`: A space-separated identifier used within the runscript to select
multiple settings at once.
- `dist_template`: The default value is `templates/single.dist`, which refers
to [single.dist]. This attribute is only relevant for distributed jobs. More information
about dist templates can be found on the [templates] page.
- `dist_options`: Allows one to add additional options for distributed jobs.
    `dist_options` expects a comma-separated string of options. For example,  
    `dist_options="#SBATCH --hint=compute_bound,#SBATCH -J=%x.%j.out"` results in the
    following lines being added to the script:

    ```bash
    #SBATCH --hint=compute_bound
    #SBATCH -J=%x.%j.out
    ```

    The default template for distributed jobs uses SLURM; a comprehensive list of available
    options is provided in the [SLURM documentation].

- Each setting can contain any number of `encoding` elements. These encodings
will be used together with instances when using this setting:
    - `file`: A relative path from the directory where `btool gen` is run to the encoding file.
    - If no `tag` is given, the encoding is passed to the system for all instances when this
    setting is selected.
    - If a `tag` is given, encoding usage is instance-dependent. Multiple encodings can
    be selected by using the same tag.
- Each setting can also include any number of `variable` elements, which can be used to
define multiple settings at once. If several `variable` elements are present, settings
are generated for every possible combination of their values. The names of these
generated settings follow the pattern `<setting-name>_<value1>[_<value2>]...`.
All attributes (such as cmdline, tag, and encodings) are inherited from the parent setting.
    - `cmd`: Specifies the attribute or command. May contain `{}` as a placeholder for
    the value. If `{}` is not present, `={}` is automatically appended to the command.
    - `value`: Defines the values for the generated settings. Values can be provided as
    a range (`<float>,<float>,<float>`, representing start, end, and step) or as a
    pool (a `;`-separated list, i.e., `<any>;<any>;...`).
    - By default, the `cmd` and `value` pairs are included with the other command-line
    arguments in `cmdline`. The optional `post` attribute can be set to `true` to place
    the arguments in `cmdline_post` instead.

    For example, the setting at the start of the section would result in the following generated settings:
    
    |                         | --time-limit=30   | --time-limit=60   | --time-limit=90   |
    | ----------------------- | ----------------- | ----------------- | ----------------- |
    | **--memory-limit=1024** | setting-1_30_1024 | setting-1_60_1024 | setting-1_90_1024 |
    | **--memory-limit=2048** | setting-1_30_2048 | setting-1_60_2048 | setting-1_90_2048 |

## Job

A job defines additional arguments for individual runs. You can define any number of jobs.
There are two types: sequential jobs (`seqjob`) and distributed jobs (`distjob`) for
running benchmarks on a cluster.

### Sequential Jobs

A sequential job is identified by its `name` and sets the `timeout` (in seconds) for a
single run, the number of `runs` for each instance, and the number of solver processes
executed in `parallel`. The optional attribute `memout` sets a memory limit (in MB) for
each run. If no limit is set, a default limit of 20 GB is used. Additional options, which
will be passed to the runlim call, can be set using the optional `template_options`
attribute. `template_options` expects a comma-separated string of options, e.g.  
`template_options="--single,--report-rate=2000"`.

```xml
<seqjob name="seq-gen" timeout="900" runs="1" memout="1000" template_options="--single" parallel="1"/>
```

### Distributed Jobs

A distributed job is also identified by its `name` and defines a `timeout`, the number
of `runs`, and an optional `memout` and `template_options`:

```xml
<distjob name="dist-gen" timeout="900" runs="1" memout="1000" template_options="--single"
        script_mode="timeout" walltime="23h 59m 59s" cpt="4"/>
```

Additionally, a distributed job has the following attributes:

- `walltime`: Sets an overall time limit for all runs in `[0-9]+d [0-9]+h [0-9]+m [0-9]+s`
format. Each value is optional and can be any positive integer. For example, `12d 350s`
sets the time to 12 days and 350 seconds. Alternatively, a single value without a unit is
interpreted as seconds.
- `script_mode`: Defines how runs are grouped and dispatched to the cluster.
    - `multi`: Dispatches all runs individually for maximum parallelization. (In this
    mode, the walltime is ignored.)
    - `timeout`: Dispatches groups of runs based on the `timeout` and `walltime` of the
    distributed job. Runs are gathered into groups such that the total time for each
    group is below the specified `walltime`. For example, if the `walltime` is 25 hours
    and you have 100 instances with a `timeout` of 1 hour each and 1 run each, there
    will be 4 groups of 25 runs each, which are dispatched separately.
- `partition`: (Optional) Specifies the cluster partition name. The default is `kr`.
Other values include `short` and `long`. If `short` is used, the walltime cannot exceed
24 hours. Note that these values depend on your cluster configuration.

!!! info
    If you have many runs, `script_mode=multi` can cause issues with the cluster's
    scheduler. Use `timeout` or dispatch the generated `.dist` jobs using `btool run-dist`.

## Benchmark Sets

The `benchmark` element defines a group of benchmark instances, organized into classes
to be run by systems. It is identified by its `name` and can contain any number of
`folder` or `files` elements or alternatively any number of `spec` elements:

```xml
<benchmark name="no-pigeons">
    ...
</benchmark>
```

### Folder Elements

A `folder` element defines a `path` to a folder containing instances, which is
searched recursively. Each sub-folder containing instances is treated as a
benchmark class, and results are separated accordingly:

```xml
<folder path="benchmarks/clasp" encoding_tag="tag1" group="true" cmdline_post="--text">
    <ignore prefix="pigeons"/>
    <encoding file="encodings/no-pigeons.lp"/>
</folder>
```

A `folder` element can have the following optional attributes:

- `encoding_tag`: Selects encodings with matching tags in setting definitions. These
encodings are used with all instances in this folder when the corresponding setting
is run. See the [encoding support] page for more details.
- `group`: A Boolean attribute (default is `false`). If enabled, instance files in the
same folder with the form `<instance>.<extension>` sharing the same prefix `<instance>`
are grouped together and passed to the system. For example, files `inst1.1.lp` and
`inst1.2.lp` in the same folder would be grouped as `inst1`.
- Similiar to the system and setting elements, a `folder` element can also include
`cmdline` and `cmdline_post` attributes, which adds the specified arguments to all
instances defined in this folder.

A `folder` element can contain any number of `encoding` and `ignore` elements:

- `ignore`: Excludes folders from the benchmark by defining a path `prefix` to be ignored.
- `encoding`: Specifies encodings to be used with all instances in the folder.

### File Elements

Instead of using a `folder` element to gather benchmark instances, you can also
manually add specific files using the `files` element:

```xml
<files path="benchmarks/clasp" encoding_tag="tag1 tag2">
    <encoding file="default.lp"/>
    <add file="dir/file1.lp" group="instance" cmdline="--text"/>
    <add file="dir/file2.lp" group="instance" cmdline="-c n=4"/>
</files>
```

The `files` element supports the following optional attributes:

- `path`: Specifies the folder containing the instances to be added.
- `encoding_tag`: Works the same way as for the `folder` element.

The `files` element can contain any number of `encoding` and `add` elements:

- `add`: Specifies a file to be added to the benchmark. The `file` attribute gives the
path to the instance relative to the `path` attribute of its parent `files` element.
Instance files can optionally be grouped together using the `group` attribute.
Groups of instances must be located in the same directory and are passed together to
the system. Similiar to the `system` and `setting` elements, `add` can also include
`cmdline` and `cmdline_post` attributes. Command-line arguments always count for the
entire group, e.g. with `files` element from above instance `instance` would be called
with `--text -c n=4`.
- `encoding`: Specifies files which are added to every group/instance.

The example above would result in a single benchmark instance `instance` which includes
the files `default.lp` `file1.lp` and `file2.lp`.

### Spec Elements

Alternatively, `spec` elements can be used to load benchmark specifications
from `spec.xml` files.

```xml
<spec path="benchmarks/clasp" instance_tag="tag1 | tag2 tag3"/>
```

The `spec` element has the following attributes:

- `path`: Specifies a folder to be recursively searched for any `spec.xml` files.
Once a `spec.xml` file is found, the search does not continue deeper. For example,
in the structure below, the last `spec.xml` file inside `subfolder` is ignored:

```xml
benchmarks/clasp
├── folder1
│   ├── ins1.lp
│   └── spec.xml
└── folder2
    ├── ins2.lp
    ├── spec.xml
    └── subfolder
        ├── ins2-1.lp
        └── spec.xml
```

- `instance_tag` (optional): Specifies which groups of instances to include for the
current benchmark. Tag groups are separated by `|`, and tags within a group are
separated by spaces. For example, `tag1 | tag2 tag3` selects instances that either
have `tag1` or both `tag2` and `tag3` together. Instances with only `tag2` or `tag3`
are not included. If the special tag `*all*` is used or `instance_tag` is not set,
all instances are included regardless of their tags.

#### Spec Files

A `spec.xml` file can be used to specify benchmark instances, similar to the
benchmark element in the runscript. Here is an example of a `spec.xml` with all features:

```xml
<spec>
    <class name="folder" encoding_tag="encTag">
        <folder path="test_folder" instance_tag="tagA" group="true" cmdline="-c n=4"/>
        <folder path="other_folder"/>
        <encoding file="enc1.lp"/>
    </class>
    <class name="instances">
        <instance file="test_f1.2.1.lp" instance_tag="tagB" group="test_f1" cmdline="-c n=10"/>
        <instance file="test_f1.2.2.lp" instance_tag="tagB" group="test_f1"/>
        <instance file="test_folder/test_foldered.lp" instance_tag="tagB tagA"/>
        <instance file="test_f2.lp" instance_tag="tagC"/>
    </class>
</spec>
```

Each `spec.xml` file contains a single `spec` root element, which may include any number
of `class` elements. Every `class` element must have a `name` attribute and may
optionally include an `encoding_tag` attribute.

For instances defined in the runscript, the benchmark class is determined by the
folder containing the instance. In contrast,
for instances defined in a `spec.xml` file, the benchmark class is constructed by combining
the relative path from the `path` attribute of the corresponding `spec` element in the
runscript to the location of the `spec.xml` file, together with the `name` attribute
of the `class` element.
For example, with the `spec` element and folder structure from the section above,
if the `spec.xml` file located in `folder1` contains a `class` element named
`class_name`, the benchmark class for its instances will be `folder1/class_name`.

The `encoding_tag` attribute can be used to assign setting-dependent encodings to
the instances. See the [encoding support] page for more information.

Each `class` element can contain any number of `folder`, `instance`, and `encoding`
elements. These function the same as those defined in the benchmark element in the
runscript. The only differences are that all paths are now relative to the `spec.xml`
file, and the `folder` and `instance` elements each also have an `instance_tag`
attribute. These tags allow for a selection of instances using the `instance_tag`
attribute of the `spec` element described above.


## Projects

Projects combine all previous elements to define a complete benchmark setup.

```xml
<project name="clingo-basic" job="seq-gen">
    ...
</project>
```

A `project` element includes the following attributes:

- `name`: Uniquely identifies the project and determines the name of the second
folder in the output structure.
- `job`: References a previously defined job to use as a template for the benchmark.

Projects can be defined in two ways: with `runtag` elements or `runspec` elements.
A project may contain any number of both.

### Runtag Elements

The `runtag` element specifies a machine and benchmark set to run:

```xml
<runtag machine="hpc" benchmark="no-pigeons" tag="basic"/>
```

It has the following attributes:

- `machine`: References a previously defined machine.
- `benchmark`: References a previously defined benchmark set.
- `tag` (optional): Specifies one or more setting tags to use. Only settings with
matching tag groups are selected. Tag groups are separated by `|`, and tags within
a group are separated by spaces. For example, `tag1 | tag2 tag3` selects instances
that either have `tag1` or both `tag2` and `tag3` together. Instances with only
`tag2` or `tag3` are not included. If the special tag `*all*` is used or `tag` is
not set, all instances are included regardless of their tags.

In the example above, all instances defined in the `no-pigeons` benchmark are
run using the `seq-gen` job configuration on machine `hpc`, once for each setting
with the tag `basic`.

### Runspec Elements

A `project` element can also include one or more `runspec` elements to explicitly
specify a single machine, benchmark, system, version, and setting to use:

```xml
<runspec machine="hpc" benchmark="no-pigeons" system="clingo" version="5.8.0"
    setting="setting-1"/>
```

The attributes are as follows:

- `machine`: References a previously defined machine.
- `benchmark`: References a previously defined benchmark set.
- `system` and `version`: Reference a previously defined system.
- `setting`: References a previously defined setting of the selected system.

[run template]: ./templates.md#run-templates
[result parser]: ../../reference/resultparser.md
[single.dist]: https://github.com/potassco/benchmark-tool/blob/master/templates/single.dist
[templates]: templates.md#dist-templates
[examples]: ../../examples/index.md#runscripts
[SLURM documentation]: https://slurm.schedmd.com/sbatch.html
[encoding support]: ../../reference/encoding_support.md
