"""
Created on Mar 20, 2026

@author: Tom Schmidt
"""

from typing import TYPE_CHECKING, Any

import numpy as np

from benchmarktool.result.xlsx_gen.result_sheets.instance_sheet import InstanceSheet
from benchmarktool.result.xlsx_gen.result_sheets.result_sheet import ResultSheet
from benchmarktool.result.xlsx_gen.spreadsheet import Formula, SystemBlock, get_cell_index

if TYPE_CHECKING:
    from benchmarktool.result import result  # nocoverage


class ClassSheet(ResultSheet):
    """
    A sheet displaying benchmark class summaries.
    """

    def __init__(
        self, name: str, benchmark: "result.BenchmarkMerge", measures: dict[str, Any], ref_sheet: InstanceSheet
    ):
        self.ref_sheet = ref_sheet
        super().__init__(name, benchmark, measures)

    def prepare(self) -> None:
        """
        Prepare the sheet.
        """
        # first column
        self.content[0] = None
        # setup rows for instances/benchmark classes
        row = 2
        for benchclass in self.benchmark:
            self.content.loc[row] = benchclass.name
            row += 1

        self.result_offset = row
        self._set_col_summary_headers(self.result_offset + 1)

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
        key = (getattr(runspec, "setting", None), getattr(runspec, "machine", None))
        block = self.system_blocks.setdefault(
            key, SystemBlock(getattr(runspec, "setting", None), getattr(runspec, "machine", None))
        )
        if block.machine:
            self.machines.add(block.machine)

        for benchclass_result in runspec:
            benchclass_summary: dict[str, Any] = {}
            for instance_result in benchclass_result:
                self._add_instance_results_to_benchclass_summary(instance_result, benchclass_summary)
                for m in block.columns:
                    if m not in self.types or self.types[m] in {"None", "empty"}:
                        self.types[m] = block.columns[m]
                    # should never occur, all mixed columns are treated as None or classresult
                    elif block.columns[m] not in {self.types[m], "None", "empty"}:  # nocoverage
                        self.types[m] = "None"
            self._add_benchclass_summary(block, benchclass_result, benchclass_summary)
            for m in block.columns:
                if m not in self.types or self.types[m] in {"None", "empty"}:
                    self.types[m] = block.columns[m]

    def _add_instance_results_to_benchclass_summary(
        self,
        instance_result: "result.InstanceResult",
        benchclass_summary: dict[str, Any],
    ) -> None:
        """
        Aggregate instance results to benchmark class summary.

        Attributes:
            instance_result (InstanceResult): Instance result.
            benchclass_summary (dict[str, Any]): Benchmark class summary.
        """
        for run in instance_result:
            for name, value_type, value in run.iter(self.measures):
                self.measures.setdefault(name, None)
                if value_type == "int":
                    value_type = "float"
                elif value_type not in {"float", "None", "empty"}:
                    value_type = "string"
                if value_type == "float" and self.ref_sheet.types.get(name, "") == "float":
                    if benchclass_summary.get(name) is None:
                        benchclass_summary[name] = (0.0, 0)
                    benchclass_summary[name] = (
                        float(value) + benchclass_summary[name][0],
                        1 + benchclass_summary[name][1],
                    )
                else:
                    if name not in benchclass_summary:
                        benchclass_summary[name] = None

    def _add_benchclass_summary(
        self, block: SystemBlock, benchclass_result: "result.ClassResult", benchclass_summary: dict[str, Any]
    ) -> None:
        """
        Add benchmark class summary to a system block.

        Attributes:
            block (SystemBlock): System block.
            benchclass_result (ClassResult): Benchmark class result.
            benchclass_summary (dict[str, Any]): Benchmark class summary.
        """
        for name, value in benchclass_summary.items():
            if value is not None:
                temp_res = value[0] / value[1]
                if name == "timeout":
                    temp_res = value[0]
                block.add_cell(
                    benchclass_result.benchclass.values["row"],
                    name,
                    "classresult",
                    {
                        "inst_start": benchclass_result.benchclass.values["inst_start"],
                        "inst_end": benchclass_result.benchclass.values["inst_end"],
                        "value": temp_res,
                    },
                )
            else:
                block.add_cell(benchclass_result.benchclass.values["row"], name, "None", np.nan)

    def _finalize_results(self) -> None:
        """
        Finalize the results of the sheet.
        """
        for column in self.content.loc[:, 1:]:
            name = self.content.at[1, column]
            if self.types.get(name, "") == "classresult":
                for row in range(2, self.result_offset):
                    op = "SUM" if name == "timeout" else "AVERAGE"
                    if isinstance(self.content.at[row, column], dict):
                        self.values.at[row, column] = self.content.at[row, column]["value"]
                        self.content.at[row, column] = Formula(
                            f"{op}(Instances!{get_cell_index(column, self.content.at[row, column]['inst_start'] + 2)}:"
                            f"Instances!{get_cell_index(column, self.content.at[row, column]['inst_end'] + 2)})"
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
        for col in self.content.loc[:, 1:]:
            name = self.content.at[1, col]
            if self.types.get(name, "") == "classresult":

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
                self._add_default_col_summary_values(col, name, values)
