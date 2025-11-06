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

You can install all required packages for this notebook by using the following command
inside the benchmark-tool directory.
```bash
$ pip install .[plot]
```
"""

    data_heading = """\
### Obtain data
"""

    data_code = f'''\
from typing import Any

import ipywidgets as widgets
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from ipywidgets.widgets.interaction import fixed

df_in = pd.read_parquet("{parquet_file}")

settings: set[str] = set()
measures: set[str] = set()


def get_metadata(df: pd.DataFrame) -> dict[str, Any]:
    """
    Extract metadata from dataframe.

    Attributes
        df (pd.DataFrame): DataFrame.
    """
    meta: dict[str, Any] = {{}}
    for col in df.columns:
        if col[0] == "_metadata":
            meta[col[1]] = list(df.loc[df[col[0]][col[1]] != "nan", (col[0], col[1])])
        elif col[0] != "":
            measures.add(col[0])
            settings.add(col[1])
    df.drop("_metadata", axis=1, level=0, inplace=True)
    return meta


metadata = get_metadata(df_in)

df_fill = (
    df_in.loc[: int(float(metadata["offset"][0])), [("", "instance")]]
    .replace("<NA>", np.nan)
    .ffill()
    .combine_first(df_in.drop(columns=("", "instance")))
    .loc[: int(float(metadata["offset"][0])),]
)
'''

    funcs_heading = """\
### Helper functions
"""
    funcs_code = '''\
def multi_checkbox_widget(options_dict: dict[str, widgets.Checkbox]) -> widgets.VBox:
    """
    Widget with a search field and lots of checkboxes.
    Based on 'https://gist.github.com/MattJBritton/9dc26109acb4dfe17820cf72d82f1e6f'.

    Attributes:
        options_dict (dict): Widget options.
    """
    search_widget = widgets.Text()
    output_widget = widgets.Output()
    options = list(options_dict.values())
    options_layout = widgets.Layout(
        overflow="auto", border="1px solid black", width="300px", height="300px", flex_flow="column", display="flex"
    )

    # selected_widget = wid.Box(children=[options[0]])
    options_widget = widgets.VBox(options, layout=options_layout)
    # left_widget = wid.VBox(search_widget, selected_widget)
    multi_select = widgets.VBox([search_widget, options_widget])

    @output_widget.capture()
    def on_checkbox_change(change):
        """
        Helper function to sort checkboxes based on selection.
        """
        # change["owner"].description
        # print(options_widget.children)
        # selected_item = wid.Button(description = change["new"])
        # selected_widget.children = [] #selected_widget.children + [selected_item]
        options_widget.children = sorted(list(options_widget.children), key=lambda x: x.value, reverse=True)

    for checkbox in options:
        checkbox.observe(on_checkbox_change, names="value")

    @output_widget.capture()
    def on_text_change(change):
        """
        Helper function to filter checkboxes based on search field.
        """
        search_input = change["new"]
        if search_input == "":
            # Reset search field
            new_options = sorted(options, key=lambda x: x.value, reverse=True)
        else:
            # Filter by search field using difflib.
            # close_matches = difflib.get_close_matches(search_input, list(options_dict.keys()), cutoff=0.0)
            close_matches = [x for x in list(options_dict.keys()) if str.lower(search_input.strip("")) in str.lower(x)]
            new_options = sorted(
                [x for x in options if x.description in close_matches], key=lambda x: x.value, reverse=True
            )  # [options_dict[x] for x in close_matches]
        options_widget.children = new_options

    search_widget.observe(on_text_change, names="value")
    display(output_widget)
    return multi_select


def prepare_data(data: pd.DataFrame, merge: str) -> pd.DataFrame:
    """
    Prepare data for plotting.

    Attributes:
        data_frame (pd.DataFrame): Input data.
        merge (str): How to merge runs (none, mean, median).
    """
    measure = "time"

    cs =  list(data["time"].columns)
    df_plot = pd.DataFrame()
    df_plot["instance"] = data.loc[:, ("", "instance")]
    for c in cs:
        df_plot[c] = pd.to_numeric(data.loc[:, (measure, c)], errors="coerce")

    if merge == "median":
        df_plot = df_plot.groupby(
            "instance", dropna=False).median().reset_index()
    elif merge == "mean":
        df_plot = df_plot.groupby(
            "instance", dropna=False).mean().reset_index()

    df_plot = df_plot.drop(["instance"], axis=1)
    df_plot.loc[-1] = [0 for x in range(len(df_plot.columns))]
    df_plot.sort_index(inplace=True)
    df_plot.index = df_plot.index + 1

    res = pd.DataFrame()
    for c in cs:
        s = df_plot[c].sort_values(ignore_index=True).drop_duplicates(keep="last")
        key = "_to_" + c
        if key in metadata:
            tl = max(map(float, metadata[key]))
            s.mask(s.ge(tl), inplace=True)
        res = pd.concat([res, s], axis=1)
    return res.sort_index()


def prepare_plots(
    data: pd.DataFrame, mode: str, merge: str, width: int, height: int
) -> tuple[go.FigureWidget, dict[str, int]]:
    """
    Prepare plotly figure and traces.
    Attributes:
        data (pd.DataFrame): Input data.
        mode (str): Plot mode (cactus, cdf).
        merge (str): How to merge runs (none, mean, median).
        width (int): Plot width.
        height (int): Plot height.
    """
    plot_data = prepare_data(data, merge)

    fig = go.Figure()
    colors = px.colors.qualitative.G10
    switch_xy = False

    # set up multiple traces
    i = 0
    lookup = {}
    for col in plot_data.columns:
        val = plot_data[[col]].dropna()
        if mode == "Survivor":
            x_vals = val[col].cumsum()
            y_vals = val.index
            switch_xy = False
        elif mode == "Cactus":
            x_vals = val.index
            y_vals = val[col]
            switch_xy = True
        else:
            x_vals = val[col]
            y_vals = val.index
            switch_xy = False
        fig.add_trace(
            go.Scatter(
                x=x_vals,
                y=y_vals,
                name=col,
                visible=False,
                line={"shape": "hv"},
                marker=dict(color=colors[i % len(colors)], size=15),
            )
        )
        lookup[col] = i
        i += 1

    if switch_xy:
        fig.update_layout(
            xaxis={"title": {"text": "# of instances"}},
            yaxis={"title": {"text": "Time in s"}},
            updatemenus=[
                {
                    "buttons": [
                        {"label": "Linear", "method": "relayout", "args": [{"yaxis.type": "linear"}]},
                        {"label": "Log", "method": "relayout", "args": [{"yaxis.type": "log"}]},
                    ]
                }
            ],
        )
    else:
        fig.update_layout(
            xaxis={"title": {"text": "Time in s"}},
            yaxis={"title": {"text": "# of instances"}},
            updatemenus=[
                {
                    "buttons": [
                        {"label": "Linear", "method": "relayout", "args": [{"xaxis.type": "linear"}]},
                        {"label": "Log", "method": "relayout", "args": [{"xaxis.type": "log"}]},
                    ]
                }
            ],
        )

    fig.update_layout(
        title={"text": f"{mode} plot"},
        autosize=False,
        width=width,
        height=height,
        # font=dict(
        #    family="Courier New, monospace",
        #    size=18,
        #    color="RebeccaPurple"
        # ),
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": -0.4 * 500 / height,
            "xanchor": "center",
            "x": 0.5,
            "maxheight": 0.1,
            "title_text": "Setting",
        },
        margin={
            "l": 50,
            "r": 50,
            "b": 50,
            "t": 50,
            "pad": 10,
        },
    )
    fig.update_yaxes(automargin=True)
    fig.update_xaxes(automargin=True)
    return go.FigureWidget(fig), lookup


def plot(
    data: pd.DataFrame, mode: str, merge: str, width: int, height: int, opts: dict[str, Any], sets: dict[str, list[str]]
) -> None:
    """
    Prepare plot and traces.
    Attributes:
        data (pd.DataFrame): Input data.
        mode (str): Plot mode (cactus, cdf).
        merge (str): How to merge runs (mean, median).
        width (int): Plot width.
        height (int): Plot height.
        opts (dict): Widget options.
        sets (dict): System:Settings association
    """

    def f(**args: Any) -> None:
        """
        Update trace visibility based on selected options.
        Attributes:
            args: Should contain selected settings, figure widget, lookup table, and sets.
        """
        figure_widget = args.pop("fig")
        lookup = args.pop("lookup")
        sets = args.pop("sets")
        s = sorted([key for key, value in args.items() if value])
        select = []
        for ss in s:
            if ss in sets:
                select += sets[ss]
            else:
                select.append(ss)

        for col, i in lookup.items():
            if col in select:
                figure_widget.data[i].visible = True
            else:
                figure_widget.data[i].visible = False

        display(figure_widget)

    fig, lookup = prepare_plots(data, mode, merge, width, height)
    opts["fig"] = fixed(fig)
    opts["lookup"] = fixed(lookup)
    opts["sets"] = fixed(sets)

    out = widgets.interactive_output(f, opts)
    display(out)


def get_gui(data: pd.DataFrame) -> tuple[widgets.HBox, widgets.Output]:
    """
    Create GUI for plotting.

    Attributes:
        data (pd.DataFrame): Input data.
    """
    # Create sets for system selection
    sets: dict[str, list[str]] = {}
    for setting in settings:
        system_setting = setting.split("/")
        if system_setting[0] in sets:
            sets[system_setting[0]].append(setting)
        else:
            sets[system_setting[0]] = [setting]

    options_dict = {
        x: widgets.Checkbox(description=x, value=False, style={"description_width": "0px"})
        for x in sorted(list(settings) + list(sets.keys()))
    }

    ui = multi_checkbox_widget(options_dict)

    select_mode = widgets.ToggleButtons(
        options=["Survivor", "Cactus", "CDF"],
        description="Mode:",
        disabled=False,
        button_style="",  # 'success', 'info', 'warning', 'danger' or ''
        tooltips=["Cactus plot", "CDF plot"],
    )

    select_merge = widgets.ToggleButtons(
        options=["do not merge", "median", "mean"],
        description="Merge:",
        disabled=False,
        button_style="",  # 'success', 'info', 'warning', 'danger' or ''
        tooltips=["Merge runs using median", "Merge runs using mean"],
    )
    width_slider = widgets.IntSlider(
        value=1000,
        min=500,
        max=1500,
        step=100,
        orientation="horizontal",
        continuous_update=False,
    )
    height_slider = widgets.IntSlider(
        value=500,
        min=500,
        max=1500,
        step=100,
        orientation="horizontal",
        continuous_update=False,
    )
    sliders = widgets.VBox(
        [
            widgets.Label("Width of the plot in px"),
            width_slider,
            widgets.Label("Height of the plot in px"),
            height_slider,
        ]
    )

    out = widgets.interactive_output(
        plot,
        {
            "mode": select_mode,
            "merge": select_merge,
            "width": width_slider,
            "height": height_slider,
            "opts": fixed(options_dict),
            "data": fixed(data),
            "sets": fixed(sets),
        },
    )

    return widgets.HBox([widgets.VBox([select_mode, select_merge, sliders]), ui]), out
'''

    plot_heading = """\
# Plots

The first row on the left select which kind of plot will be created.

The second row on the left determines how multiple runs (if there are more than 1) will be mergedinto a single result.

The sliders can be used to adjust the size of the plot.

Finally, select individual settings or all settings of a system to plot using the checkboxes on the right. The input field at the top can be used to search through all possible selections.

The scale of the time axis can be selected to the left of the plot.
---

All plots below are interactive. When hovering over a plot, a toolbar will appear, which can be used to zoom, move, and save the plot.
You can show the full output, without a scrollbar, by clicking the gray bar to the left of the output cell.

"""
    plot_code = """\
gui, out_plot = get_gui(df_fill)
display(gui)
display(out_plot)
"""

    nb = nbf.v4.new_notebook()
    nb["cells"] = [
        nbf.v4.new_markdown_cell(intro),
        nbf.v4.new_markdown_cell(data_heading),
        nbf.v4.new_code_cell(data_code),
        nbf.v4.new_markdown_cell(funcs_heading),
        nbf.v4.new_code_cell(funcs_code),
        nbf.v4.new_markdown_cell(plot_heading),
        nbf.v4.new_code_cell(plot_code),
    ]
    fname = file_name
    nb.cells[1]["metadata"]["jp-MarkdownHeadingCollapsed"] = True
    nb.cells[3]["metadata"]["jp-MarkdownHeadingCollapsed"] = True
    # nb.cells[6]["metadata"]["jupyter"] = {"source_hidden": True}

    try:
        nbf.validate(nb)
    except nbf.validator.NotebookValidationError as e:  # nocoverage
        raise RuntimeError("Generated notebook is invalid") from e

    with open(fname, "w", encoding="utf-8") as f:
        nbf.write(nb, f)
