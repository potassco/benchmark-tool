"""
Created on Mar 20, 2026

@author: Tom Schmidt
"""

from typing import TYPE_CHECKING, Any, Optional

import numpy as np
import pandas as pd  # type: ignore[import-untyped]

from benchmarktool.result.xlsx_gen.result_sheets.result_sheet import ResultSheet
from benchmarktool.result.xlsx_gen.spreadsheet import DataValidation, SystemBlock, get_cell_index

if TYPE_CHECKING:
    from benchmarktool.result import result  # nocoverage


# pylint: disable=too-many-instance-attributes
class InstanceSheet(ResultSheet):
    """
    A sheet displaying instance results.
    """

    def __init__(self, name: str, benchmark: "result.BenchmarkMerge", measures: dict[str, Any]):
        self.runs: Optional[int] = None
        super().__init__(name, benchmark, measures)

    def prepare(self) -> None:
        """
        Prepare the sheet.
        """
        # first column
        self.content[0] = None
        # setup rows for instances/benchmark classes
        run_summary = True
        row = 2
        for benchclass in self.benchmark:
            for instance in benchclass:
                self.content.loc[row] = instance.benchclass.name + "/" + instance.name
                row += instance.values["max_runs"]
                if self.runs is None:
                    self.runs = instance.values["max_runs"]
                elif self.runs != instance.values["max_runs"]:  # nocoverage
                    run_summary = False

        self.result_offset = row
        self._set_col_summary_headers(self.result_offset + 1)

        # run summary
        if run_summary and self.runs and self.runs > 1:
            selection = DataValidation(
                {
                    "validate": "list",
                    "source": list(range(1, self.runs + 1)),
                    "input_message": "Select run number",
                },
                1,
                "input",
            )

            self.content.loc[self.result_offset + 10] = "Select run:"
            self.content.loc[self.result_offset + 11] = selection
            self._set_col_summary_headers(self.result_offset + 12)

        # fill missing rows
        self.content = (
            self.content.astype(object).reindex(list(range(self.content.index.max() + 1))).replace({np.nan: None})
        )

    def add_runspec(self, runspec: "result.Runspec") -> None:
        """
        Add a run specification to the sheet.

        Attributes:
            runspec (Runspec): Run specification.
        """
        key = (runspec.setting, runspec.machine)
        block = self.system_blocks.setdefault(key, SystemBlock(runspec.setting, runspec.machine))
        if block.machine:
            self.machines.add(block.machine)

        for benchclass_result in runspec:
            for instance_result in benchclass_result:
                self._add_instance_results(block, instance_result)
                for m in block.columns:
                    if m not in self.types or self.types[m] in {"None", "empty"}:
                        self.types[m] = block.columns[m]
                    # mixed measure
                    elif block.columns[m] not in {self.types[m], "None", "empty"}:
                        self.types[m] = "string"

    def _add_instance_results(
        self,
        block: SystemBlock,
        instance_result: "result.InstanceResult",
    ) -> None:
        """
        Add instance results to SystemBlock.

        Attributes:
            block (SystemBlock):                 SystemBlock to which results are added.
            instance_result (InstanceResult):    InstanceResult.
        """
        for run in instance_result:
            for name, value_type, value in run.iter(self.measures):
                self.measures.setdefault(name, None)
                if value_type == "int":
                    value_type = "float"
                elif value_type not in {"float", "None", "empty"}:
                    value_type = "string"
                if value_type == "float":
                    block.add_cell(
                        instance_result.instance.values["row"] + run.number - 1, name, value_type, float(value)
                    )
                elif value_type in {"None", "empty"}:
                    block.add_cell(instance_result.instance.values["row"] + run.number - 1, name, value_type, np.nan)
                else:
                    block.add_cell(instance_result.instance.values["row"] + run.number - 1, name, value_type, value)

    def _finalize_results(self) -> None:
        """
        Finalize the results of the sheet.
        """
        for column in self.content:
            name = self.content.at[1, column]
            if self.types.get(name, "") == "float":
                self.float_occur.setdefault(name, set()).add(column)
            # defragmentation (temporary workaround)
            self.content = self.content.copy()
            self.values = self.values.copy()

    def _obtain_values(self) -> None:
        """
        Obtain values from the sheet.
        """
        self.values = self.content.copy()

    def add_col_summary(self) -> None:
        """
        Add column summary if applicable to column type.
        """

        def _get_run_select(ref: str, runs: int, col_idx: int, abs_col: bool = True) -> str:
            """
            Get run dependent row selection formula.

            Attributes:
                ref (str): Row range reference
                runs (int): Number of runs
                col_idx (int): Current column index
                abs_col (bool): Set '$' for new column reference
            """
            return (
                f"CHOOSE({ref},"
                + ",".join([f"ROW({get_cell_index(col_idx, 2 + i, abs_col, True)})" for i in range(runs)])
                + ")"
            )

        def _get_run_filter(base_range: str, choose_rows: str) -> str:
            """
            Get formula for filtered rows by run.

            Attributes:
                base_range (str): Row range to filter
                choose_rows (str): Run selection formula
            """
            return f"FILTER({base_range},MOD(ROW({base_range})-{choose_rows},{self.runs})=0)"

        run_select_cell = f"{get_cell_index(0, self.result_offset + 11, True, True)}"
        for col in self.content:
            name = self.content.at[1, col]
            if self.types.get(name, "") == "float":

                # skip empty columns
                values = np.array(self.values.loc[2 : self.result_offset - 1, col], dtype=float)
                if np.isnan(values).all():
                    continue

                ref_value = (
                    f"{get_cell_index(col, 2, False, True)}:{get_cell_index(col, self.result_offset - 1, False, True)}"
                )
                min_rows = self.summary_refs["min"][name][1]
                med_rows = self.summary_refs["median"][name][1]
                max_rows = self.summary_refs["max"][name][1]
                summaries = [(0, ref_value, min_rows, med_rows, max_rows)]

                # Add run summary formulas if applicable
                if self.runs is not None and self.runs > 1:
                    sel_runs = _get_run_select(run_select_cell, self.runs, col, False)
                    ref_runs = _get_run_filter(summaries[0][1], sel_runs)
                    min_runs = _get_run_filter(
                        summaries[0][2], _get_run_select(run_select_cell, self.runs, self.summary_refs["min"][name][0])
                    )
                    med_runs = _get_run_filter(
                        summaries[0][3],
                        _get_run_select(run_select_cell, self.runs, self.summary_refs["median"][name][0]),
                    )
                    max_runs = _get_run_filter(
                        summaries[0][4], _get_run_select(run_select_cell, self.runs, self.summary_refs["max"][name][0])
                    )
                    summaries.append((11, ref_runs, min_runs, med_runs, max_runs))

                self._add_default_col_summary_formulas(col, summaries)
                self._add_default_col_summary_values(col, name, values)

    # to be reworked
    def export_values(self, file_name: str, metadata: dict[str, list[Any]]) -> None:  # nocoverage
        """
        Export values to parquet file.

        Attributes:
            file_name (str): Name of the parquet file.
        """
        # fill settings
        self.values.iloc[0, :] = self.values.iloc[0, :].ffill()
        # group values by measure
        df = self.values.iloc[2:, [0]].reset_index(drop=True).astype("string")
        df.columns = pd.MultiIndex.from_tuples([("", "instance")], names=["measure", "setting"])
        for m, cols in self.float_occur.items():
            nf = self.values.iloc[2:, sorted(cols)].reset_index(drop=True).astype("float64")
            nf.columns = self.values.iloc[0, sorted(cols)].to_list()
            nf.columns = pd.MultiIndex.from_product([[m], nf.columns], names=["measure", "setting"])
            df = df.join(nf)
        # metadata
        # offset -2 (header) -1 (empty row)
        metadict = {**{"offset": [self.result_offset - 3]}, **metadata}
        metadf = pd.DataFrame({k: pd.Series(v) for k, v in metadict.items()})
        metadf.columns = pd.MultiIndex.from_product([["_metadata"], metadf.columns], names=["measure", "setting"])
        self.values = df.join(metadf)
        #! min,med,max no longer included
        self.values.astype(str).to_parquet(file_name)
