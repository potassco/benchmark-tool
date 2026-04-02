"""
Created on Mar 20, 2026

@author: Tom Schmidt
"""

from typing import TYPE_CHECKING, Any

import numpy as np

from benchmarktool.result.xlsx_gen.result_sheets.instance_sheet import InstanceSheet
from benchmarktool.result.xlsx_gen.result_sheets.result_sheet import ResultSheet
from benchmarktool.result.xlsx_gen.spreadsheet import DataValidation, Formula, SystemBlock, get_cell_index

if TYPE_CHECKING:
    from benchmarktool.result import result  # nocoverage


class MergedRunSheet(ResultSheet):
    """
    A sheet displaying merged runs.
    """

    def __init__(
        self, name: str, benchmark: "result.BenchmarkMerge", measures: dict[str, Any], ref_sheet: InstanceSheet
    ):
        self.ref_sheet = ref_sheet
        self.run_refs: dict[int, dict[str, Any]] = {}
        super().__init__(name, benchmark, measures)

    def prepare(self) -> None:
        """
        Prepare the merged run sheet.
        """
        self.content[0] = None
        self.content.loc[0] = "Merge criteria:"
        # selection
        self.content.loc[1] = DataValidation(
            {
                "validate": "list",
                "source": ["average", "median", "min", "max", "diff"],
                "input_message": "Select merge criteria",
            },
            "median",
            "input",
        )
        row = 2
        for benchclass in self.benchmark:
            for instance in benchclass:
                self.content.loc[row] = instance.benchclass.name + "/" + instance.name
                row += 1

        self.result_offset = row
        self._set_col_summary_headers(self.result_offset + 1)

        # fill missing rows
        self.content = (
            self.content.astype(object).reindex(list(range(self.content.index.max() + 1))).replace({np.nan: None})
        )

    def add_runspec(self, runspec: "result.Runspec") -> None:
        """
        Add results to their respective blocks.

        Attributes:
            runspec (Runspec): Run specification
        """
        key = (runspec.setting, runspec.machine)
        block = self.system_blocks.setdefault(key, SystemBlock(runspec.setting, runspec.machine))
        if block.machine:
            self.machines.add(block.machine)

        for benchclass_result in runspec:
            instance_summary: dict[result.InstanceResult, dict[str, Any]] = {}
            for instance_result in benchclass_result:
                self._add_instance_results_to_instance_summary(instance_result, instance_summary)
                for m in block.columns:
                    if m not in self.types or self.types[m] in {"None", "empty"}:
                        self.types[m] = block.columns[m]
                    # should never occur, all mixed columns are treated as None or merged_runs
                    elif block.columns[m] not in {self.types[m], "None", "empty"}:  # nocoverage
                        self.types[m] = "None"
            for instance_result in benchclass_result:
                self._add_merged_instance_results(block, instance_result, instance_summary)
            for m in block.columns:
                if m not in self.types or self.types[m] in {"None", "empty"}:
                    self.types[m] = block.columns[m]

    def _add_instance_results_to_instance_summary(
        self,
        instance_result: "result.InstanceResult",
        instance_summary: dict["result.InstanceResult", dict[str, Any]],
    ) -> None:
        """
        Add instance results to summary.

        Attributes:
            instance_result (InstanceResult):    InstanceResult.
            instance_summary (dict[InstanceResult, dict[str, Any]]): Summary of instance results.
        """
        instance_summary[instance_result] = {}
        for run in instance_result:
            for name, value_type, _ in run.iter(self.measures):
                self.measures.setdefault(name, None)
                instance_summary[instance_result].setdefault(name, False)
                if value_type == "int":
                    value_type = "float"
                elif value_type not in {"float", "None", "empty"}:
                    value_type = "string"
                if value_type == "float" and self.ref_sheet.types.get(name, "") == "float":
                    instance_summary[instance_result][name] = True

    def _add_merged_instance_results(
        self,
        block: SystemBlock,
        instance_result: "result.InstanceResult",
        instance_summary: dict["result.InstanceResult", dict[str, Any]],
    ) -> None:
        """
        Add merged instance results to SystemBlock.

        Attributes:
            block (SystemBlock):              SystemBlock to which results are added.
            instance_result (InstanceResult): InstanceResult.
            instance_summary (dict[result.InstanceResult, dict[str, Any]]): Summary of benchmark class.
        """
        for name, value in instance_summary[instance_result].items():
            inst_val = instance_result.instance.values
            # check if any run has a float value
            if value:
                # value just to signal non empty cell
                block.add_cell(
                    (inst_val["row"] + inst_val["max_runs"]) // inst_val["max_runs"] - 1,
                    name,
                    "merged_runs",
                    {
                        "inst_start": inst_val["row"],
                        "inst_end": inst_val["row"] + inst_val["max_runs"] - 1,
                        "value": 1,
                    },
                )
            else:
                block.add_cell(
                    (inst_val["row"] + inst_val["max_runs"]) // inst_val["max_runs"] - 1, name, "None", np.nan
                )

    def _finalize_results(self) -> None:
        """
        Finalize the results of the sheet.
        """
        for column in self.content:
            name = self.content.at[1, column]
            if self.types.get(name, "") == "merged_runs":
                for row in range(2, self.result_offset):
                    if isinstance(self.content.at[row, column], dict):
                        # value just to signal non empty cell
                        self.values.at[row, column] = self.content.at[row, column]["value"]
                        self.run_refs[row - 1] = {
                            "inst_start": self.content.at[row, column]["inst_start"],
                            "inst_end": self.content.at[row, column]["inst_end"],
                        }
                        cell_range = (
                            f'(Instances!{get_cell_index(column, self.content.at[row, column]["inst_start"] + 2)}:'
                            f'Instances!{get_cell_index(column, self.content.at[row, column]["inst_end"] + 2)})'
                        )
                        self.content.at[row, column] = Formula(
                            f"SWITCH($A$2,"
                            f'"average", AVERAGE{cell_range},'
                            f'"median", MEDIAN{cell_range},'
                            f'"min", MIN{cell_range},'
                            f'"max", MAX{cell_range},'
                            f'"diff", MAX{cell_range}-MIN{cell_range}'
                            ")"
                        )
                self.float_occur.setdefault(name, set()).add(column)
            # defragmentation (temporary workaround)
            self.content = self.content.copy()
            self.values = self.values.copy()

    def _obtain_values(self) -> None:
        """
        Obtain values from the sheet.
        """
        self.values = self.values.reindex(index=self.content.index, columns=self.content.columns)
        self.values = self.values.combine_first(self.content)

    def add_col_summary(self) -> None:
        """
        Add column summary if applicable to column type.
        """
        for col in self.content:
            name = self.content.at[1, col]
            if self.types.get(name, "") == "merged_runs":

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

                self._add_default_col_summary_formulas(col, summaries)
