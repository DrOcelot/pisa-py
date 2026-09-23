'''Convert SPSS .SAV files to parquet. 
'''

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

sch_22_path = Path(__file__).resolve().parents[2] / "data" / "spss" / "CY08MSP_SCH_QQQ.SAV"
stu_22_path = Path(__file__).resolve().parents[2] / "data" / "spss" / "CY08MSP_STU_QQQ.SAV"
out_path = Path(__file__).resolve().parents[2] / "data" / "built"

# This line chooses which dataset to use.
sav = pyreadstat.read_sav(sch_22_path, metadataonly=False, user_missing=True)

def add_missing_reasons(df: pd.DataFrame, var: str) -> pd.DataFrame:
    """Add missing reasons to the school survey data."""
    # grab data and metadata from whole spss file
    data, meta = df

    # gets key value pairs for "lo" and "hi" indicating the range of the data's missing range
    meta_missing_ranges = meta.missing_ranges[var] 

    # extracts the lowest value that indicates missingness
    lo = meta_missing_ranges[0]["lo"]

    # add an NaN column with missing reason to be populated later.
    data[f"{var}_missing_reason"] = np.nan

    # makes a dictionary of all labels the variable has
    # if the var is numeric labels will be NaN for real values
    # if the var is categoric labels will not be NaN, instead they will match the categoric answer
    labels_dict = meta.variable_value_labels[var]
    data[f"{var}_missing_reason"] = np.where(data[var]<lo, np.nan, data[var].map(labels_dict))
    data[var] = np.where(data[var]>=lo, np.nan, data[var].map(labels_dict).fillna(data[var]))
    return data

pimp = add_missing_reasons(sav, "SC016Q02TA")
print(pimp["SC016Q02TA"])
#add_missing_reasons(stu_22_path, "ST261Q03JA")