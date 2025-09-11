---
title: "runscript"

---

# Runscript

A runscript defines all aspects of a benchmark set. The following sections will go
through all parts of a typical runscript and show what is possible, so you can adapt
an existing runscript to your needs or create a new one from scratch.

Some example runscripts can be found [here](../../examples/index.md#runscripts)

## Folder Structure

When running `bgen` a folder structure is created. The name of the first folder in the tree is given by the root element in the runscript:

```xml
<runscript output="output-folder">
    ...
</runscript>
```

In this case, the name of the folder is "output-folder". It is recommended that the name should be changed to something meaningful and representative of the benchmark you are running.

The name of the folder second in the hierarchy represents the project, which will be explained later.

The folder third in the hierarchy corresponds to the name of the machine the benchmark was run on. A machine is defined in the runscript as seen below:

```xml
<machine name="hpc" cpu="24x8xE5520@2.27GHz" memory="24GB"/>
```

!!! info
    The *cpu* and *memory* attributes are currently unused.

    Any number of machines can be defined.


In this folder you will find the start scripts to start the benchmark and the results afterwards.
The results are structured as follows:
```
./results/<benchmark-name>/<system-name>-<system-version>-<setting>/<benchclass>/<instance>/<run>
```

## Configuration

At the moment a configuration is only used to reference a run template. Any number of configurations can be defined as below:

```xml
<conifg name="seq-generic" template="templates/seq-generic.sh"/>
```

For more information regarding run templates check [here](templates.md#run-templates).

## System

The following line shows, how a system is defined.
```xml
<system name="clingo" version="5.8.0" measures="clingo" config="seq-generic" cmdline="--stats">
    ...
</system>
```

The values of *name* and *version* work together to describe the name of a bash script named `<name>-<version>`, which has to be placed inside the `./programs` directory. In the case of the example above, the solver given to the [run template](./templates.md#run-templates) described in the configuration is `./programs/clingo-4.5.4`. Since this is a regular bash script, feel free to modify it to your heart's content.

The *measure* attribute describes a name of a [result parser](../beval/index.md#resultparser), which will be used to evaluate the results during the `beval` call. This has no effect on `bgen`.

The *config* attribute refers to the name of a configuration, which should be used to run this system.

The *cmdline* attribute is optional and can be any string, which will be passed to the system regardless of the setting.

A runscript can contain any number of systems, which in turn can contain any number of settings.

### Setting

Settings are identified by their name and define additional arguments and encodings used by the system.

```xml
<setting name="setting-1" cmdline="--quiet=1,0" tag="basic">
    <encoding file="encodings/default.lp"/>
    <encoding file="extra.lp" tag="extra"/>
</setting>
```
 The value of the *cmdline* attribute can be any valid string, which will be passed to the system via the run template when this setting is selected.

 The *tag* attribute is another identifier, which is only valid inside this runscript and is used to select multiple setting at once.

 Each setting can also contain any number of encoding elements. The *file* attribute is a relative path from the directory, where `bgen` is run, to the encoding. If no *tag* is defined the encoding is passed to the system via the run template for all instances when this setting is selected. A *tag* can be provided to make the encoding usage instance dependant. Multiple encodings can be selected by using the same tag.

 The setting element additionaly supports an optional attribute *disttemplate*. The default value is `"templates/single.dist"` which is a reference to [single.dist](https://github.com/potassco/benchmark-tool/blob/master/templates/single.dist). This attribute is only relevant for distjobs. More information to dist templates can be found [here](templates.md#dist-templates).

 Another optional attribute only used for distjobs is *distopts*, which allows the user to add additional options for distributed jobs. *distopts* expects a string of comma separated options. For example `distopts="#SBATCH --hint=compute_bound,#SBATCH --job-name="my_benchmark_run"` results in the following lines being added to the script:

 ```
 #SBATCH --hint=compute_bound
 #SBATCH --job-name="my_benchmark_run"
 ```

The default template for distributed jobs uses SLURM. A list of available SLURM options can be found [here](https://slurm.schedmd.com/sbatch.html).

## Job

A job is used to define additional arguments for individual runs. Any number of jobs can be defined. There are two types of jobs, 'default' sequential *seqjob*s and *distjob*s for running the benchmarks on a cluster.

```xml
<seqjob name="seq-gen" timeout="900" runs="1" parallel="1"/>
```
A seqjob is identified by its name and sets the *timeout* in seconds for a single run, the number of *runs* for each instance and the number of runs performed in *parallel*.

```xml
<distjob name="dist-gen" timeout="900" runs="1" script_mode="timeout" walltime="23h 59m 59s" cpt="4"/>
```
A distjob is also identified by its name and defines a *timeout* and the number of *runs*. *walltime* sets an overall time limit for all runs in the `[<D>d] [<H>h] [<M>m] [<S>s]` format. Each value is optional can be any integer value e.g., `12d 350s` is valid. Additionally a only single value without an unit can be provided, which will be interpreted as seconds (as seen in the timeout attribute above).

The *script_mode* attribute, defines how runs are grouped and dispatched to the cluster. 'multi' dispatches all runs individually to the cluster for maximum possible parallelization.
'timeout' dispatches groups of runs depending on the set *timeout* and *walltime*. If it is not possible to execute all runs sequentially inside the *walltime* specified, they will be split into as many groups as necessary so that the *walltime* is never surpassed. For example, if the *walltime* is 25 hours and you have 100 instances with a *timeout* of 1 hour each and 1 run each, there will be 4 groups, each with 25 runs, which will be dispatched.

!!! info
        If you have a lot of runs *script_mode* 'multi' can cause issues with the cluster scheduler. Either use 'timeout' or dispatch the generated `.dist` jobs using the `./dispatcher.py`.

A last optional attribute for distjobs is *partition*, which is the name of the partition used on the cluster. The default value is 'kr'. Other values for this argument can be "short" and "long". If short is used the walltime can not exceed 24 hours.

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
