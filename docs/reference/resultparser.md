---
title: "Modifying Resultparser"
icon: "material/text-box-check-outline"
---

# Modifying the Resultparser

The default resultparser provided is [clasp.py](https://github.com/potassco/benchmark-tool/blob/master/src/benchmarktool/resultparser/clasp.py), which supports many of clingo's statistics. However, sometimes we will need access to other statistics that the script doesn't retrieve. We could also be running a program that has its own set of statistics.

We will now take a look at how the scripts work, how to change them to fit your own goals and how to write your own.

Lets look at [clasp.py](https://github.com/potassco/benchmark-tool/blob/master/src/benchmarktool/resultparser/clasp.py) as an example. All resultparser **must** define a `parse()`function, which takes 3 arguments. The first argument is the path to the root directory of the benchmark and where the results are saved. The second argument, runspec, gives us access to the data that we defined in the runscript file. The third argument is an instance class that includes information such as the location and the name of the instance.

The function is applied to every benchmark 'run' individually. It gathers the data for a particular run in basically three steps:

- Read the relevant input files
- Extract the data using regular expressions
- Do some post-processing on the data if needed

The `parse()` function always has to return a list of triples where each triple has the type `tuple[str, str, Any]` and the format `(<name>, <data type>, <value>)`.

## Adding your own statistics

Adding more statistics to parse is fairly simple. We will illustrate how, with an example. Suppose that our output includes the following line: `Time to run function: 20.23s`.

The first step is to add an entry to the regex dictionary:
```python
"function_time" : ("float", re.compile(r"^Time to run function:[ ]*(?P<val>[0-9]+(\.[0-9]+)?)$"))
```
The second step would be to read the entry from the *res* variable as save it into the *result* variable in the correct format. For standard float values this is already done.

Suppose that we don't really care about how long the function runs, we only care that the time it takes is less than half of the total clingo runtime. In this case, we have to do some extra processing. After the regular expressions are applied to the files, we will have a 'function_time' entry in the *res* variable. We can now compare the values by referencing the *res* dictionary:
```python
if (res["time"][1] / res["function_time"][1]) < 2:
	result.append("function_time", "string", "acceptable")
else:
	result.append("function_time", "string", "unacceptable")
```
Afterwards, we have to delete the 'function_time' entry from *res* so that it is not added to *result* later on:
```python
del res["function_time"]
```
