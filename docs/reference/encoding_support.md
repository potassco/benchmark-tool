---
title: "Encoding Support"
icon: "material/file-code"
---

# Encoding Support


Given a basic template:

```bash
{run.solver} {sys_cmd} {setting_cmd} {run.file} {runs.encodings}
```

The default behaviour of a benchmark is to simply execute the system with each instance:

```bash
<system> <arguments> <instance>
```

## Instance-dependent encodings

It is possible to use specific encodings depending on the instance by defining them
inside the corresponding [`benchmark`](../getting_started/gen/runscript.md#benchmark-sets)
element in the runscript, more specifically inside the `folder` and `files` child-elements.

Any number of `encoding` elements can be defined. These encodings will be used together
with all instances inside the given `folder` or `files`.

For example, consider the following benchmark element:
```xml
<benchmark name="bench">
    <folder path="default-folder"/>
    <folder path="with-encoding">
        <encoding file="folder-encoding.lp"/>
        <encoding file="helper.lp"/>
    </folder>
    <files path="other-folder">
        <add file="some-file.lp"/>
        <encoding file="file-encoding.lp"/>
    </files>
</benchmark>
```
There are three cases to distinguish:

- All instances inside the default folder are run as above.
- All instances inside the `with-encoding` directory are executed as:  
  `<system> <arguments> <instance> folder-encoding.lp helper.lp`
- The instance `other-folder/some-file.lp` is executed as:  
  `<system> <arguments> <instance> file-encoding.lp`

!!! info
    The examples above use simplified paths for readability.



## Setting-dependent encodings

It is also possible to use specific encodings depending on the setting used by defining
them inside the corresponding [`setting`](../getting_started/gen/runscript.md#setting)
element and referencing them inside the
[`benchmark`](../getting_started/gen/runscript.md#benchmark-sets) element.

Any number of `encoding` elements can be defined. These will be used with all
instances using the given setting, or—if an `encoding_tag` is given—only with
instances that have a matching tag.

Consider the following example settings:
```xml
<system name="clingo" version="1.0.0" measures="clasp" config="seq-generic">
    <setting name="s0"/>
    <setting name="s1">
        <encoding file="def.lp"/>
        <encoding file="enc11a.lp" encoding_tag="tag"/>
        <encoding file="enc11b.lp" encoding_tag="tag"/>
    </setting>
    <setting name="s2">
        <encoding file="enc21.lp" encoding_tag="tag"/>
        <encoding file="enc22.lp" encoding_tag="tag2"/>
    </setting>
</system>
```
And a slightly modified benchmark element:
```xml
<benchmark name="bench">
    <folder path="default-folder"/>
    <folder path="with-encoding" encoding_tag="tag">
        <encoding file="folder-encoding.lp"/>
        <encoding file="helper.lp"/>
    </folder>
    <files path="other-folder" encoding_tag="tag2">
        <add file="some-file.lp"/>
        <encoding file="file-encoding.lp"/>
    </files>
</benchmark>
```
This results in the following runs:

- With setting `s0`, nothing changes compared to the instance-dependent example.
- With setting `s1`:
    - For all instances inside the `default-folder`:  
      `clingo-1.0.0 <arguments> <instance> def.lp`
    - For all instances inside the `with-encoding` directory (tag: `tag`):  
      `clingo-1.0.0 <arguments> <instance> folder-encoding.lp helper.lp def.lp enc11a.lp enc11b.lp`
    - For instance `other-folder/some-file.lp` (tag: `tag2`):  
      `clingo-1.0.0 <arguments> <instance> file-encoding.lp def.lp`
- With setting `s2`:  
    - For all instances inside the default folder:  
      `clingo-1.0.0 <arguments> <instance>`
    - For all instances inside the `with-encoding` directory (tag: `tag`):  
      `clingo-1.0.0 <arguments> <instance> folder-encoding.lp helper.lp enc21.lp`
    - For instance `other-folder/some-file.lp` (tag: `tag2`):  
      `clingo-1.0.0 <arguments> <instance> file-encoding.lp enc22.lp`

!!! info
    The examples above use simplified paths for readability.
