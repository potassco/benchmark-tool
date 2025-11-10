---
title: "Encoding Support"
icon: "material/file-code"
---

# Encoding Support

Given a most basic template:
```bash
{run.solver} {run.file} {runs.encodings} {run.args}
```
The default behaviour of a benchmark is to simply execute the system with each instance.

```bash
$ <system> <instance> <arguments>
```

## Instance dependent

It is possible to use specific encodings depending on the instance by defining them inside the corresponding [*benchmark*](../getting_started/gen/runscript.md#benchmark-sets) element in the runscript, more specifically inside the *folder* and *files* child-elements.

Any amount of *encoding* elements can be defined, which will be called together with all instances inside the given *folder* or *files*.

As an example lets look at the following benchmark element:
```xml
<benchmark name="bench">
    <folder path="default-folder"/>
    <folder path="with-encoding">
        <encoding file="folder-encoding.lp">
        <encoding file="helper.lp">
    </folder>
    <files path="other-folder">
        <add file="some-file.lp">
        <encoding file="file-encoding.lp">
    </files>
</benchmark>
```
Here we have to differentiate three cases:

- All instances inside the default folder are run as above
- All instances inside the 'with-encoding' directory are executed as
 `$ <system> <instance> folder-encoding.lp helper.lp <arguments>`
- Instance 'other-folder/some-file.lp' is executed as
 `$ <system> <instance> file-encoding.lp <arguments>`

!!! info
    The examples above include simplified paths for readability purposes.


## Setting dependent

It is also possible to use specific encodings depending on the setting used by defining them inside the corresponding [*setting*](../getting_started/gen/runscript.md#setting) element and referencing them inside the [*benchmark*](../getting_started/gen/runscript.md#benchmark-sets) element.

Any amount of *encoding* elements can be defined, which will be called together with all instances using the given setting or, when given an 'enctag', only with similarly tagged instances.

Lets take the following setting elements as an example:
```xml
<system name="clingo" version="1.0.0" measures="clasp" config="seq-generic">
    <setting name="s0"/>
    <setting name="s1">
        <encoding file="def.lp"/>
        <encoding file="enc11a.lp" enctag="tag"/>
        <encoding file="enc11b.lp" enctag="tag"/>
    </setting>
    <setting name="s2" >
        <encoding file="enc21.lp" enctag="tag"/>
        <encoding file="enc22.lp" enctag="tag2"/>
    </setting>
</system>
```
With the slightly modified benchmark element from above:
```xml
<benchmark name="bench">
    <folder path="default-folder"/>
    <folder path="with-encoding" enctag="tag">
        <encoding file="folder-encoding.lp">
        <encoding file="helper.lp">
    </folder>
    <files path="other-folder" enctag="tag2">
        <add file="some-file.lp">
        <encoding file="file-encoding.lp">
    </files>
</benchmark>
```
This results in the following runs:

- When using setting 's0' nothing changes compared to the encoding dependent example
- When setting 's1' is used:
    - For all instances inside the default folder:
    `$ clingo-1.0.0 <instance> def.lp <arguments>`
    - For all instances inside the 'with-encoding' directory (tag: 'tag'):
    `$ clingo-1.0.0 <instance> folder-encoding.lp helper.lp def.lp enc11a.lp enc11b.lp <arguments>`
    - For instance 'other-folder/some-file.lp' (tag: 'tag2'):
    `$ clingo-1.0.0 <instance> file-encoding.lp def.lp <arguments>`
- When setting 's2' is used:
    - For all instances inside the default folder:
    `$ clingo-1.0.0 <instance> <arguments>`
    - For all instances inside the 'with-encoding' directory (tag: 'tag'):
    `$ clingo-1.0.0 <instance> folder-encoding.lp helper.lp enc21.lp <arguments>`
    - For instance 'other-folder/some-file.lp' (tag: 'tag2'):
    `$ clingo-1.0.0 <instance> file-encoding.lp enc22.lp <arguments>`

!!! info
    The examples above include simplified paths for readability purposes.
