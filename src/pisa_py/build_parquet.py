'''Convert SPSS .SAV files to parquet. 
'''

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat
import time

sch_22_path = Path(__file__).resolve().parents[2] / "data" / "spss" / "CY08MSP_SCH_QQQ.SAV"
stu_22_path = Path(__file__).resolve().parents[2] / "data" / "spss" / "CY08MSP_STU_QQQ.SAV"
out_path = Path(__file__).resolve().parents[2] / "data" / "built"

def add_missing_reasons(df: pd.DataFrame, var: str) -> pd.DataFrame:
    """Add missing reasons to the school survey data."""
    # grab data and metadata from whole spss file
    data, meta = df

    if(not (lo := meta.missing_ranges.get(var, [{'lo':False}])[0]["lo"])):
        return data

    # add an NaN column with missing reason to be populated later.
    data.insert(data.columns.get_loc(var)+1, f"{var}_missing_reason", np.nan )

    # makes a dictionary of all labels the variable has
    # if the var is numeric labels will be NaN for real values
    # if the var is categoric labels will not be NaN, instead they will match the categoric answer
    labels_dict = meta.variable_value_labels[var]
    data[f"{var}_missing_reason"] = np.where(data[var]<lo, np.nan, data[var].map(labels_dict))
    data[var] = np.where(data[var]>=lo, np.nan, data[var].map(labels_dict).fillna(data[var]))
    return data

t0 = time.perf_counter()
# This line chooses which dataset to use.
sav = pyreadstat.read_sav(stu_22_path, metadataonly=False, user_missing=True)
print(time.perf_counter()-t0)

t1 = time.perf_counter()
for var in sav[0]:
    add_missing_reasons(sav, var)
print(time.perf_counter()-t1)

n=0
for col in sav[0].columns:
    if col.endswith("missing_reason"):
        n=n+1
print(n)