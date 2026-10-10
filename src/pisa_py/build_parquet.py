"""Convert SPSS .SAV files to parquet."""

import os
from pathlib import Path

import polars as pl
import pyreadstat

DATA_DIR = Path(__file__).resolve().parents[2] / "data"

sch_in_path = DATA_DIR / "spss" / "CY08MSP_SCH_QQQ.sav"
sch_out_path = DATA_DIR / "built" / "school_22.parquet"
stu_in_path = DATA_DIR / "spss" / "CY08MSP_STU_QQQ.sav"
stu_out_path = DATA_DIR / "built" / "student_22.parquet"

in_paths_out_paths = {
    sch_in_path: sch_out_path,
    stu_in_path: stu_out_path,
}


def add_missing_reasons(meta: pyreadstat.metadata_container, var: str) -> list[pl.Expr]:
    """Create missing reason expressions for the given survey data."""

    # gets the low end of the missing ranges if it exists.
    # If there is no missing datathere's nothing to do so returns an epmty list.
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
                default=(None),
                return_dtype=(pl.Enum(list(dict.fromkeys(labels_dict.values())))),
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
                default=(None if any(label < lo for label in labels_dict) else pl.col(var)),
                return_dtype=(
                    pl.Enum(list(dict.fromkeys(labels_dict.values())))
                    if any(label < lo for label in labels_dict)
                    else pl.Float64
                ),
            )
        )
        .alias(var)
    )
    return [missing_col_expr, update_col_expr]


def main() -> None:
    for in_path, out_path in in_paths_out_paths.items():
        # read sav
        survey_df, survey_metadata = pyreadstat.read_file_multiprocessing(
            pyreadstat.read_sav,
            in_path,
            num_processes=((os.cpu_count() or 2) - 1),
            metadataonly=False,
            user_missing=True,
            output_format="polars",
        )

        assert isinstance(survey_df, pl.DataFrame)
        survey_lf = survey_df.lazy()

        # generate expressions list
        exprs: list[pl.Expr] = []
        for col in survey_lf.collect_schema().names():
            exprs.extend(add_missing_reasons(survey_metadata, col))
        survey_lf = survey_lf.with_columns(*exprs)

        # output parquet
        survey_lf.sink_parquet(
            out_path,
            engine="streaming",
            mkdir=True,
        )


if __name__ == "__main__":
    main()
