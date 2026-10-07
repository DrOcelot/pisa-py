'''Convert SPSS .SAV files to parquet. 
'''

import os
import time
from pathlib import Path

import polars as pl
import pyreadstat

sch_22_path = Path(__file__).resolve().parents[2] / "data" / "spss" / "CY08MSP_SCH_QQQ.sav"
stu_22_path = Path(__file__).resolve().parents[2] / "data" / "spss" / "CY08MSP_STU_QQQ.sav"
out_path_dir = Path(__file__).resolve().parents[2] / "data" / "built"

in_paths = {
    "school_22": sch_22_path, 
    "student_22": stu_22_path, 
    }

def add_missing_reasons(meta: pyreadstat.metadata_container, var: str) -> list[pl.Expr]:
    """Add missing reasons to the school survey data."""

    # gets the low end of the missing ranges if it exists. 
    # If there is no missing datathere's nothing to do so returns 'data'.
    ranges = meta.missing_ranges.get(var)
    if not ranges or not isinstance(first := ranges[0], dict):
        return []
    lo = first["lo"]

    # makes a dictionary of all labels the variable has
    # if the var is numeric labels will be NaN for real values
    # if the var is categoric labels will not be NaN, instead they will match the categoric answer
    labels_dict = meta.variable_value_labels[var]
    
    missing_col_expr = (
        pl.when(pl.col(var) < lo)
        .then(None)
        .otherwise(
            pl.col(var).replace_strict(
                labels_dict, 
                default= (None),
                return_dtype= (
                    pl.Enum(list(dict.fromkeys(labels_dict.values())))
                    )
            )
        )
        .alias(f"{var}_missing_reason")
        )
    update_col_expr = (
        pl.when(pl.col(var) >= lo)
        .then(None)
        .otherwise(
            pl.col(var).replace_strict(
                labels_dict, 
                default= (
                    None
                    if any(label < lo for label in labels_dict) 
                    else pl.col(var)
                    ),
                return_dtype= (
                    pl.Enum(list(dict.fromkeys(labels_dict.values()))) 
                    if any(label < lo for label in labels_dict) 
                    else pl.Float64
                    )
            )
        )
        .alias(var)
    )    
    return [missing_col_expr,update_col_expr]

def main() -> None:
    for path in in_paths:
        in_path = in_paths[path]
        out_path = path
        # read sav 
        t0 = time.perf_counter()
        data, meta = pyreadstat.read_file_multiprocessing(
            pyreadstat.read_sav, 
            in_path,
            num_processes= ((os.cpu_count() or 2) - 1), 
            metadataonly=False,
            user_missing=True,
            output_format="polars",
            )
        print(f"{in_path.name} read time: ", time.perf_counter()-t0)

        assert isinstance(data, pl.DataFrame)
        data = data.lazy()

        # generate expressions list
        t1 = time.perf_counter()
        exprs: list[pl.Expr] = []
        for col in data.collect_schema().names():
            exprs.extend(add_missing_reasons(meta, col))
        data = data.with_columns(*exprs)
        print("For loop time: ", time.perf_counter()-t1)

        #output parquet
        t2 = time.perf_counter()
        data.sink_parquet(
            f"{out_path_dir}/{out_path}.parquet",
            engine="streaming",
            mkdir=True,
            )
        print(f"built/{out_path}.parquet sink time: ", time.perf_counter()-t2)

if __name__ == "__main__":
    main()