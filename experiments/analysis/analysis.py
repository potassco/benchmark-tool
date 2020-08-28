
# coding: utf-8

#get_ipython().magic(u'matplotlib notebook')
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from IPython.display import display, HTML, Markdown

pd.options.display.float_format = '{:,.1f}'.format

class Analyzer:

    def do_get_3df(self, df, runs):
        nans = np.where(df.index.isnull())[0]
        times = np.where(df.iloc[0] == 'time')[0]
        old_t = 0
        for t in times[1:-2]:
            run_df = pd.DataFrame(df.iloc[1:nans[1], old_t:t - 1])
            run_df.columns = df.iloc[0, old_t:t - 1]
            run_df.columns.name = 'measures'
            option = df.columns[old_t].split('/', 1)[1]
            runs[option] = run_df
            old_t = t
    
    # df is a list of DataFrames
    def get_3df(self, dfs):
        runs = {}
        for df in dfs:
            self.do_get_3df(df, runs)
        return pd.concat(runs.values(), keys=runs.keys())
    
    def cumulative(self, input, index):
        out = [0] * len(index)
        for i in range(len(index)):
            out[i] = np.count_nonzero(input < index[i])
        return out
    
    def cumulative_df(self, input, col, index):
        graph = {}
        for i in input.index.levels[0]:
            graph[i] = self.cumulative(input[col].loc[i], index)
        return pd.DataFrame(graph, index=index)
    
    def get_classes(self, df3):
        instances = df3.index.levels[1]
        tmp_classes = set([ins.rsplit('/', 1)[0] for ins in instances])
        classes = {
            c: [ins for ins in instances if ins.rsplit('/', 1)[0] == c]
            for c in tmp_classes
        }
        return {c: df3.loc[(slice(None), classes[c]), :] for c in classes.keys()}
    
    # from df3, select the instances _in _classes (if _in is true)
    # else, select the instances not _in _classes
    def select(self, df3, _in, _classes):
        instances = df3.index.levels[1]
        tmp_classes = set([ins.rsplit('/', 1)[0] for ins in instances])
        classes = {
            c: [ins for ins in instances if ins.rsplit('/', 1)[0] == c]
            for c in tmp_classes
        }
        ins = []
        for key, item in classes.items():
            if (_in and key in _classes) or (not _in and key not in _classes):
                ins += item
        return df3.loc[(slice(None), ins), :]
    
    # To select only the rows where timeout != 1 for all systems:
    # select_never_condition(df3, df3['timeout'] == 1)
    def select_never_condition(self, df3, df3_cond):
        chosen = set(df3.index[df3_cond].labels[1])
        all_instances = df3.index.levels[1]
        selected_instances = []
        for idx, item in enumerate(all_instances):
            if idx not in chosen:
                selected_instances.append(item)
        return df3.loc[(slice(None), selected_instances), :]
    
    def aggregate(self, df3, f):
        return pd.DataFrame({i: f(df3.loc[i]) for i in df3.index.levels[0]}).T
    
    def read_ods(self, _file):  # absolute path with .ods at the end
        import os
        os.system("soffice -env:UserInstallation=file:///$HOME/.libreoffice-headless/ --headless --convert-to xlsx " + _file)
        xlsx = "./" + _file.rsplit('/', 1)[1][:-3] + "xlsx"
        return pd.read_excel(xlsx, 0)
    
    def read_many_ods(self, files):
        return self.get_3df([self.read_ods(_file) for _file in files])

def run(files):

    a = Analyzer()

    df3 = a.read_many_ods(files)

    index = range(0, 900, 1)

    # SELECT SOME SYSTEMS, BENCHMARKS or VALUES

    # select some systems
    #df3 = df3.loc[(['newbasic-parallel-0', 'newbasic-410', 'newbasic-parallel-1', 'mg-foralli-shallow', 
    #               'mg-simple0-noshallow', 'newbasic-parallel-5', 'mg-sequential-shallow', 'newbasic-parallel-3' ],slice(None)), :]

    # select some benchmarks
    #df3 = a.select(df3, False, ['iscas85/instances/c3540'])

    # select some values
    # df3 = a.select_never_condition(df3, df3['timeout'] == 1)

    ### ALL INSTANCES

    # preprocessing
    df3.index = df3.index.remove_unused_levels()
    cdf3 = a.get_classes(df3)
    cdf3.keys()

    # cumulative plots
    display(Markdown("# Plots"))
    a.cumulative_df(df3, 'time', index).plot(title="All ({})".format(len(df3.index.levels[1])))
    for i in cdf3.keys():
        a.cumulative_df(cdf3[i], 'time', index).plot(title=i + " ({})".format(len(set(cdf3[i].index.labels[1]))))

    # tables
    display(Markdown("# Tables"))
    display(Markdown("### All ({})".format(len(df3.index.levels[1]))))
    display(a.aggregate(df3, pd.DataFrame.sum).sort_values('time'))
    for i in cdf3.keys():
        display(Markdown("### {} ({})".format(i,len(set(cdf3[i].index.labels[1])))))
        display(a.aggregate(cdf3[i], pd.DataFrame.sum).sort_values('time'))
        # sum, min, max, mean...

    ### INSTANCES WITHOUT TIMEOUTS

    # select
    df3 = a.select_never_condition(df3, df3['timeout'] == 1)
    df3.index = df3.index.remove_unused_levels()
    cdf3 = a.get_classes(df3)

    # cumulative plots
    display(Markdown("# No Timeouts Plots"))
    a.cumulative_df(df3, 'time', index).plot(title="No Timeouts All ({})".format(len(df3.index.levels[1])))
    for i in cdf3.keys():
        a.cumulative_df(cdf3[i], 'time', index).plot(title="No Timeouts " + i + " ({})".format(len(set(cdf3[i].index.labels[1]))))

    # tables
    display(Markdown("# No Timeout Tables"))
    display(Markdown("### All ({})".format(len(df3.index.levels[1]))))
    display(a.aggregate(df3, pd.DataFrame.sum).sort_values('time'))
    for i in cdf3.keys():
        display(Markdown("### {} ({})".format(i,len(set(cdf3[i].index.labels[1])))))
        display(a.aggregate(cdf3[i], pd.DataFrame.sum).sort_values('time'))
        # sum, min, max, mean...

    # uncomment for plotting from command line
    # plt.show()

if __name__ == "__main__": 
    run(["/home/davila/git/plasp/encodings/planner/experiments/asp_experiments/results/asp_belleile_900s_8GB_4cpu_basic/asp_belleile_900s_8GB_4cpu_basic.ods"])





