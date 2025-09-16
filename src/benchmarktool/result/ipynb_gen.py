"""
Generate jupyter notebook for result visualization
"""

import nbformat as nbf


# mypy: disable-error-code="no-untyped-call"
def gen_ipynb(parquet_file: str, file_name: str) -> None:
    """
    Generate jupyter notebook for result visualization.

    Attributes
        parquet_file (str): Name of the parquet file containing the data.
        file_name (str): Name of the Jupyter notebook file.
    """
    intro = """\
# Visualization of results

You can install all required packages by using the following command inside the benchmark-tool directory.
```bash
$ pip install .[plot]
```
"""

    heading1 = """\
### Obtain data
"""

    code1 = f'''\
import pandas as pd
import ipywidgets as widgets
from ipywidgets import interact
from ipywidgets.widgets.interaction import fixed
import matplotlib.pyplot as plt
import numpy as np
from typing import Any
import warnings

df = pd.read_parquet("{parquet_file}")

settings: set[str] = set()
measures: set[str] = set()

def get_metadata(df: pd.DataFrame) -> dict:
    """
    Extract metadata from dataframe.

    Attributes
        df (pd.DataFrame): DataFrame.
    """
    metadata: dict[str, Any] = {{}}
    for col in df.columns:
        if col[0] == "_metadata":
            metadata[col[1]] = df[col[0]][col[1]][0]
        elif col[0] != "":
            measures.add(col[0])
            settings.add(col[1])
    df.drop("_metadata", axis=1, level=0, inplace=True)
    return metadata

metadata = get_metadata(df)

df_fill = (
            df.loc[: float(metadata["offset"]), [("", "instance")]]
            .replace("<NA>", np.nan)
            .ffill()
            .combine_first(df.drop(columns=("", "instance")))
            .loc[: float(metadata["offset"]),]
        )
'''

    heading2 = """\
### Helper functions
"""
    code2 = '''\
def multi_checkbox_widget(options_dict: dict):
    """
    Widget with a search field and lots of checkboxes.
    Based on 'https://gist.github.com/MattJBritton/9dc26109acb4dfe17820cf72d82f1e6f'.

    Attributes:
        options_dict (dict): Widget options.
    """
    search_widget = widgets.Text()
    output_widget = widgets.Output()
    options = [x for x in options_dict.values()]
    options_layout = widgets.Layout(
        overflow='auto',
        border='1px solid black',
        width='300px',
        height='300px',
        flex_flow='column',
        display='flex'
    )
    
    #selected_widget = wid.Box(children=[options[0]])
    options_widget = widgets.VBox(options, layout=options_layout)
    #left_widget = wid.VBox(search_widget, selected_widget)
    multi_select = widgets.VBox([search_widget, options_widget])

    @output_widget.capture()
    def on_checkbox_change(change):
        
        selected_recipe = change["owner"].description
        #print(options_widget.children)
        #selected_item = wid.Button(description = change["new"])
        #selected_widget.children = [] #selected_widget.children + [selected_item]
        options_widget.children = sorted([x for x in options_widget.children], key = lambda x: x.value, reverse = True)
        
    for checkbox in options:
        checkbox.observe(on_checkbox_change, names="value")

    # Wire the search field to the checkboxes
    @output_widget.capture()
    def on_text_change(change):
        search_input = change['new']
        if search_input == '':
            # Reset search field
            new_options = sorted(options, key = lambda x: x.value, reverse = True)
        else:
            # Filter by search field using difflib.
            #close_matches = difflib.get_close_matches(search_input, list(options_dict.keys()), cutoff=0.0)
            close_matches = [x for x in list(options_dict.keys()) if str.lower(search_input.strip('')) in str.lower(x)]
            new_options = sorted(
                [x for x in options if x.description in close_matches], 
                key = lambda x: x.value, reverse = True
            ) #[options_dict[x] for x in close_matches]
        options_widget.children = new_options

    search_widget.observe(on_text_change, names='value')
    display(output_widget)
    return multi_select

%matplotlib ipympl
def get_vals(df: pd.DataFrame, measure: str, setting: str) -> dict[str, list[float]]:
    """
    Get values for a specific measure and setting from dataframe.

    Attributes
        df (pd.DataFrame): DataFrame.
        measure (str): Measure name.
        setting (str): Setting name.
    """
    val: dict[str, list[float]] = {}
    for i, row in df.loc[:float(metadata["offset"])].iterrows():
        ins = row[""]["instance"]
        if ins not in val:
            val[ins] = [float(row[measure][setting])]
        else:
            val[ins].append(float(row[measure][setting]))
    return val
            
def select_mode(measure: str) -> None:
    """
    Select comparison mode.

    Attributes
        measure (str): Measure name.
    """
    z = widgets.ToggleButtons(
        options=["comp-settings","comp-runs"],
        description='Mode:',
        disabled=False,
        button_style='', # 'success', 'info', 'warning', 'danger' or ''
        tooltips=["Compare settings", "Compare runs"],
    )
    interact(select_mode_mode, measure=fixed(measure), mode=z);

def select_mode_mode(measure: str, mode: str) -> None:
    """
    Choose secondary selection.

    Attributes
        measure (str): Measure name.
        mode (str): Comparison mode.
    """
    if mode == "comp-settings":
        z = widgets.ToggleButtons(
            options=["median","mean"],
            description='Merge:',
            disabled=False,
            button_style='', # 'success', 'info', 'warning', 'danger' or ''
            tooltips=["Merge runs using median", "Merge runs using mean"],
        )
        interact(select_selection, measure=fixed(measure), mode=fixed(mode), sub_mode=z)
    elif mode == "comp-runs":
        def f(sub_mode):
            plot(measure, mode, sub_mode, [])
        z = widgets.RadioButtons(
            options=sorted(settings),
        #    layout={'width': 'max-content'}, # If the items' names are long
            description='Setting:',
            disabled=False
        )
        out = widgets.interactive_output(f, {"sub_mode":z})
        display(widgets.HBox([z, out]))
    else:
        raise RuntimeError("Invalid mode")
    
def select_selection(measure: str, mode:str, sub_mode: str) -> None:
    """
    Select plotted settings for comp-settings mode.

    Attributes:
        measure (str): Measure name.
        mode (str): Comparison mode.
        sub_mode (str): Secondary mode.
    """
    if mode == "comp-settings":
        def f(**args):
            results = [key for key, value in args.items() if value]
            plot(measure, mode, sub_mode, results)
            
        options_dict = {
            x: widgets.Checkbox(
                description=x, 
                value=False,
                style={"description_width":"0px"}
            ) for x in sorted(settings)
        }
        ui = multi_checkbox_widget(options_dict)
        out = widgets.interactive_output(f, options_dict)
        display(widgets.HBox([ui, out]))
    elif mode == "comp-runs":
        plot(measure, mode, sub_mode, "")
    else:
        raise RuntimeError("Invalid selection")

def plot(measure: str, mode: str, sub_mode: str, select: list[str] = []) -> None:
    """
    Simplified plot function for better readability and maintainability.

    Attributes
        measure (str): Measure name.
        mode (str): Comparison mode.
        sub_mode (str): Secondary mode.
        select (list[str]): Selection.
    """
    plt.close('all')  # Close previous figures to avoid memory issues
    values: dict[str, dict[str, float]] = {}

    if mode == "comp-settings":
        values = {
            setting: {x: getattr(np, sub_mode)(y) for x, y in get_vals(df_fill, measure, setting).items()}
            for setting in select
        }
        title = f"Comparison of settings: {measure}"
        labels = select
        legend_cols = 1
    elif mode == "comp-runs":
        values = {}
        for ins, runs in get_vals(df_fill, measure, sub_mode).items():
            for run, val in enumerate(runs, start=1):
                values.setdefault(str(run), {})[ins] = val
        title = f"Comparison of runs: {measure}, {sub_mode}"
        labels = values.keys()
        legend_cols = 3
    else:
        raise RuntimeError("Invalid mode")
    ins: pd.DataFrame = df.replace("<NA>", np.nan).dropna().loc[: float(metadata["offset"]), [("", "instance")]].squeeze()
    y = np.arange(len(ins))
    height = 1 / (len(labels) + 1)
    multiplier = 0

    fig, ax = plt.subplots(layout='constrained')
    for label, res in values.items():
        offset = height * multiplier
        rects = ax.barh(y + offset, res.values(), height, label=label)
        ax.bar_label(rects, padding=3)
        multiplier += 1

    ax.set_xlabel("Value")
    ax.set_title(title)
    ax.set_yticks(y + height / 2 * (len(labels) - 1), ins)
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncols=legend_cols)
    ax.invert_yaxis()
    plt.show()
'''

    heading3 = """\
# Interactive data viewer

Buckaroo provides an improved data viewer for data frames.  
For more information, check the documentation [here](https://buckaroo-data.readthedocs.io/en/latest/using.html).
"""
    code3 = """\
import buckaroo
# buckaroo causes issues with matplotlib plots -> ignore warnings
import warnings ; warnings.warn = lambda *args,**kwargs: None
df_fill
"""

    heading4 = """\
# Compare selected results

The first row of buttons selects which measure will be compared.

The second row selects if different settings or runs of the same setting should be compared with each other.

If settings should be compared, the third row of buttons selects how different runs should be merged.  
Which settings will be compared can be search through and selected using the winfow left of the plot.

If runs should be compared, the corresponding setting has to be selected. 

---

All plots below are interactive. When hovering over a plot, a sidebar will appear, which can be used to zoom, move, and save the plot.
You can show the full output, without a scrollbar, by clicking the gray bar to the left of the output cell.
"""
    code4 = """\
w = widgets.ToggleButtons(
    options=sorted(measures),
    description='Measure:',
    disabled=False,
)

interact(select_mode, measure=w)
pass
"""
    nb = nbf.v4.new_notebook()
    nb["cells"] = [
        nbf.v4.new_markdown_cell(intro),
        nbf.v4.new_markdown_cell(heading1),
        nbf.v4.new_code_cell(code1),
        nbf.v4.new_markdown_cell(heading2),
        nbf.v4.new_code_cell(code2),
        nbf.v4.new_markdown_cell(heading3),
        nbf.v4.new_code_cell(code3),
        nbf.v4.new_markdown_cell(heading4),
        nbf.v4.new_code_cell(code4),
    ]
    fname = file_name
    nb.cells[1]["metadata"]["jp-MarkdownHeadingCollapsed"] = True
    nb.cells[3]["metadata"]["jp-MarkdownHeadingCollapsed"] = True
    nb.cells[6]["metadata"]["jupyter"] = {"source_hidden": True}
    nb.cells[8]["metadata"]["jupyter"] = {"source_hidden": True}

    try:
        nbf.validate(nb)
    except nbf.validator.NotebookValidationError as e:  # nocoverage
        raise RuntimeError("Generated notebook is invalid") from e

    with open(fname, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
