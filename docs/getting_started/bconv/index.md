---
title: "bconv"
icon: "material/play-outline"
---

# bconv

The bconv entry point can be used to convert the results obtained by *beval* into an ods file, which can be opened using LibreOffice, OpenOffice or Excel. 

```bash
$ bconv benchmark-results.xml -m "time:t,choices" -o results.ods
```

The -m option selects all measures which should be included in the table. Which measure are available depends on the previously used [resultparser](../beval/index.md#resultparser) during evaluation. Each measure can also include a optional formatting argument after a ':'. The only formatting options supported at the moment are 't' and 'to'. Both can be used to mark best and worst values of float measures. While 't' works for most measures, 'to' should be used for float measures representing booleans, such as 'timeout'.

## ODS Generation

When generating the ods file two sheets are created. The first 'instance sheet' contains all runs on all benchmark instances (rows) and their results of the selected measures grouped by system/setting (columns). 

Additionally a summary for each run is created, this includes min, max and the median value for each float measure. 

A summary for each column containing float measures is created as well, including the sum, average, standard deviation and distance from the minimum and the number of best, better, worse and worst values.

The second sheet created 'class sheet' summarizes all runs of a benchmark class and so allows for a comparison between benchmark classes.

!!! info
    While all summaries are written as formulas into the ods file, the values are also calculated and can be accessed via the *content* attribute of the *Sheet* object.

    Both the ods representation and the true content are stored inside [pandas](https://pandas.pydata.org/) DataFrames for easier handling and future modifications.
