---
title: "bconv"
icon: "material/play-outline"
---

# bconv

The bconv entry point can be used to convert the results obtained by *beval* into an ods file, which can be opened using LibreOffice, OpenOffice or Excel.

```bash
$ bconv benchmark-results.xml -m "time:t,choices" -o results.ods -j plots.ipynb
```

The name of the resulting ods file is specified by the `-o` option.

The `-m` option selects all measures that should be included in the table. Which measures are available depends on the previously used [resultparser](../beval/index.md#resultparser) during evaluation. Each measure can also include an optional formatting argument after a ':'. The only formatting options supported at the moment are 't' and 'to'. Both can be used to mark the best and worst values of float measures. While 't' works for most measures, 'to' should be used for float measures representing booleans, such as 'timeout'.

The `-x` option can be used to export the dataframe containing the instance results to a parquet file. The file name will be the same as the argument given to the `-o` option e.g., `-o results.ods -x` will result in the files results.ods and results.parquet.

`-j` can be used to specify the name of a jupyter notebook (.ipynb), which will be generated and contain some visualization of the instance data. To run this notebook, some additional packages are required, which can be installed using `$ pip install .[plot]` inside the benchmark-tool directory. The notebook can be started using `$ jupyter notebook <notebook.ipynb>`. If you are using conda, jupyter should already be installed; otherwise you have to install it yourself.

Since the notebook reads the instance data via the exported .parquet file, the `-j` option also automatically sets the `-x` option, without the need to do so manually.

## ODS Generation

When generating the ods file two sheets are created. The first 'instance sheet' contains all runs on all benchmark instances (rows) and their results of the selected measures grouped by system/setting (columns).

Additionally a summary for each run is created, this includes min, max and the median value for each float measure.

A summary for each column containing float measures is created as well, including the sum, average, standard deviation and distance from the minimum and the number of best, better, worse and worst values.

The second sheet created 'class sheet' summarizes all runs of a benchmark class and so allows for a comparison between benchmark classes.

!!! info
    While all summaries are written as formulas into the ods file, the values are also calculated and can be accessed via the *content* attribute of the *Sheet* object.

    Both the ods representation and the true content are stored inside [pandas](https://pandas.pydata.org/) DataFrames for easier handling and future modifications.
