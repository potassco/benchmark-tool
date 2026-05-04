
# Runscript Examples

A collection of example runscripts to help you get started can be found in the  
`./runscripts` directory after executing `btool init`.  
Alternatively you can also find them below.

`runscript-example.xml` gives a small example on how basic sequential
and cluster benchmarks can be defined.

<details>
  <summary>
    runscript-example.xml
  </summary>
  ```xml
  <runscript output="output-folder">

    <machine name="hpc" cpu="24x8xE5520@2.27GHz" memory="24GB"/>

      <config name="seq-generic" template="templates/seq-generic.sh"/>

    <system name="clasp" version="3.4.0" measures="clasp" config="seq-generic">

        <setting name="setting-1" cmdline="--stats --quiet=1,0" tag="basic">
        <!-- value: 'float,float,float' -> range: start,end,step -->
        <variable cmd="--time-limit={}" value="30,600,30"/>
        <!-- value: 'any;any;...' -> pool of values -->
        <variable cmd="--memory-limit={}" value="1024;2048"/>
      </setting>

      </system>

    <seqjob name="seq-gen" timeout="900s" runs="1" parallel="1"/>

    <distjob name="dist-gen" timeout="1200s" runs="1" template_options="--single" script_mode="timeout" walltime="23h 59m 59s" cpt="4"/>

    <benchmark name="no-pigeons">
      <folder path="benchmarks/clasp/">
        <ignore prefix="pigeons"/>
      </folder>
      <files path="benchmarks/clasp">
        <add file="pigeons/pigeonhole10-unsat.lp" cmdline="--text"/>
      </files>
    </benchmark>

    <project name="clasp-seq-job" job="seq-gen">
      <runtag machine="hpc" benchmark="no-pigeons" tag="basic"/>
    </project>

    <project name="clasp-dist-job" job="dist-gen">
      <runtag machine="hpc" benchmark="no-pigeons" tag="basic"/>
    </project>

  </runscript>
  ```
</details>

`runscript-seq.xml` and `runscript-dist.xml` show more possibilities and
additional features.

<details>
  <summary>
    runscript-seq.xml
  </summary>
  ```xml
  <runscript output="output">

    <machine name="houat" cpu="8xE5520@2.27GHz" memory="24GB"/>

    <config name="seq-generic" template="templates/seq-generic.sh"/>
    <system name="clasp" version="3.4.0" measures="clasp" config="seq-generic" cmdline="--stats">
      <setting name="default"  cmdline="1" tag="basic"/>
      <setting name="vsids"    cmdline="--heu=vsids 1"/>
    </system>

    <seqjob name="seq-generic" timeout="120s" runs="1" parallel="4"/>

    <benchmark name="seq-suite">
      <folder path="benchmarks/clasp">
        <ignore prefix="pigeons"/>
      </folder>
      <files path="benchmarks/clasp">
        <add file="pigeons/pigeonhole10-unsat.lp"/>
        <add file="pigeons/pigeonhole11-unsat.lp"/>
      </files>
    </benchmark>

    <project name="clasp-big" job="seq-generic">
      <runtag machine="houat" benchmark="seq-suite" tag="*all*"/>
    </project>

  </runscript>
  ```
</details>

<details>
  <summary>
    runscript-dist.xml
  </summary>
  ```xml
  <runscript output="output">

    <machine name="hpc" cpu="24x8xE5520@2.27GHz" memory="24GB"/>

    <config name="dist-generic" template="templates/seq-generic.sh"/>
    <system name="clasp" version="3.4.0" measures="clasp" config="dist-generic">
      <setting name="one-as" tag="one-as" cmdline="--stats 1" dist_template="templates/single.dist"/>
    </system>

    <distjob name="dist-generic" timeout="1200s" runs="1" template_options="--single" script_mode="timeout" walltime="23h 59m 59s" cpt="4"/>

    <benchmark name="dist-suite">
      <folder path="benchmarks/clasp"/>
    </benchmark>

    <project name="clasp-one-as" job="dist-generic">
      <runtag machine="hpc" benchmark="dist-suite" tag="*all*"/>
    </project>

  </runscript>
  ```
</details>

`runscript-all` is a try to create a runscript using all available features.

<details>
  <summary>
    runscript-all.xml
  </summary>
  ```xml
  <runscript output="outputdist">

    <machine name="houat" cpu="8xE5520@2.27GHz" memory="24GB"/>
    <machine name="hpc" cpu="24x8xE5520@2.27GHz" memory="24GB"/>

    <config name="seq-generic" template="templates/seq-generic.sh"/>
    <system name="clasp" version="3.4.0" measures="clasp" config="seq-generic" cmdline="--stats" cmdline_post="--configuration=auto">
      <setting name="default"  tag="seq" cmdline="-q" cmdline_post="1"/>
      <setting name="tlimits"  tag="seq">
        <variable cmd="--time-limit" value="1800,3600,600"/>
        <encoding file ="encodings/setting_enc.lp"/>
        <encoding file ="encodings/setting_inst_enc.lp" encoding_tag="use-enc"/>
      </setting>
      <setting name="models"   tag="seq">
        <variable cmd="{}" value="2;4;6" post="true"/>
      </setting>
    </system>

    <config name="dist-generic" template="templates/seq-generic.sh"/>
    <system name="clingo" version="5.8.0" measures="clasp" config="dist-generic">
      <setting name="one-as" tag="one-as" cmdline="--stats 1" dist_template="templates/single.dist" dist_options="#SBATCH --hint=compute_bound"/>
      <setting name="all-as" tag="all-as" cmdline="--stats -q 0"/>
    </system>

    <seqjob name="seq-generic" timeout="120s" runs="1" memout="1000" parallel="8"/>
    <distjob name="dist-generic" timeout="120s" runs="1" memout="1000" template_options="--single" script_mode="timeout" walltime="23h 59m 59s" cpt="4" partition="short"/>

    <benchmark name="seq-suite">
      <folder path="benchmarks/clasp" group="true" cmdline="--restarts=no">
        <ignore prefix="pigeons"/>
        <encoding file="encodings/folder_enc.lp"/>
      </folder>
      <files path="benchmarks/clasp" encoding_tag="use-enc">
        <add file="pigeons/pigeonhole10-unsat.lp" cmdline="--heu=vsids 1"/>
        <add file="pigeons/pigeonhole11-unsat.lp" group="unsat"/>
        <encoding file="encodings/files_enc.lp"/>
      </files>
    </benchmark>
    <benchmark name="dist-suite">
      <spec path="benchmarks/dist" instance_tag="set1"/>
    </benchmark>

    <project name="clasp-seq" job="seq-generic">
      <runtag machine="houat" benchmark="seq-suite" tag="seq"/>
    </project>
    <project name="clingo-all-as" job="dist-generic">
      <runtag machine="houat" benchmark="dist-suite" tag="par one-as"/>
    </project>
    <project name="clingo-one-as" job="dist-generic">
      <runspec machine="hpc" benchmark="dist-suite" system="clingo" version="5.8.0" setting="one-as"/>
    </project>

  </runscript>
  ```
</details>

Examples for the encoding support feature can be found [here](../reference/encoding_support.md).

For a more detailed explanation of a runscript and its components check
[here](../getting_started/gen/runscript.md)
