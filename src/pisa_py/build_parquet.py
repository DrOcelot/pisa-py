'''Convert SPSS .SAV files to parquet. 
'''

from pathlib import Path

import numpy as np
import pandas as pd
import pyreadstat

sch_path = Path(__file__).resolve().parents[2] / "data" / "spss" / "CY08MSP_SCH_QQQ.SAV"
stu_path = Path(__file__).resolve().parents[2] / "data" / "spss" / "CY08MSP_STU_QQQ.SAV"

data, meta = pyreadstat.read_sav(sch_path, metadataonly=False, user_missing=True)
values = pd.DataFrame(meta.variable_value_labels)
meta_missing_ranges = meta.missing_ranges["SC014Q01TA"]
org = values[values["SC014Q01TA"].notna()]
#print(org["SC014Q01TA"])
#print(meta_missing_ranges[0]["lo"]) 

def add_missing_reasons(path: Path, var: str) -> pd.DataFrame:
    """Add missing reasons to the school survey data."""
    # grab data and metadata from whole spss file
    data, meta = pyreadstat.read_sav(path, metadataonly=False, user_missing=True) 

    #gets key value pairs for "lo" and "hi" indicating the range of the data's missing range
    meta_missing_ranges = meta.missing_ranges[var] 

    #extracts the missing low and high values
    lo = meta_missing_ranges[0]["lo"]
    hi = meta_missing_ranges[0]["hi"]

    #makes a dictionary of all labels the variable has
    #if the var is numeric labels will be NaN for real values
    #if the var is categoric labels will not be NaN, instead they will match the categoric answer
    labels_dict = meta.variable_value_labels[var]
    print(labels_dict)
    print(lo)
    print(data[data[var] >= lo][var])
    
        

    #missing_labels =  labels_dict.filter(value >= lo)
    #print(missing_labels)

    #add an NaN column with missing reason to be populated later.
    data[f"{var}_missing_reason"] = np.nan

#add_missing_reasons(sch_path, "SC014Q01TA")
add_missing_reasons(stu_path, "ST261Q03JA")