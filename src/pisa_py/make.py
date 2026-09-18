'''Pull together the school and student surveys 
into a single lazyframe that contains all the variables of use
and then export it to a parquet file.'''

from pathlib import Path
import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

STUDENT_SURVEY_FULL = DATA_DIR / "PISA_2022_student.parquet"
SCHOOL_SURVEY_FULL = DATA_DIR / "PISA_2022_school.parquet"

PV_COLS: list[str] = [
    f"PV{i}{domain}" for domain in ("MATH", "READ", "SCIE") for i in range(1, 11)
]

WT_COLS: list[str] = [
    f"W_FSTURWT{i}" for i in range(1, 81)
]
WT_COLS.append("W_FSTUWT")  # Final student weight

ID_COLS: list[str] = [
    "CNT",       # Country name
    "CNTSCHID",  # Unique school id
    "CNTSTUID",  # Unique student id
]

DEMOGRAPHIC_COLS: list[str] = [
    "ST004D01T",  # Student (standardised) gender
    "ESCS",       # Economic, social and cultural status (standardised)
]

PARENTAL_EDUCATION_COLS: list[str] = [
    "ST005Q01JA",  # Mother's highest level of schooling (ISCED)
    "ST006Q01JA",  # Mother has a PhD
    "ST007Q01JA",  # Father's highest level of schooling (ISCED)
    "ST008Q01JA",  # Father has a PhD
]

FACTOR_COLS: list[str] = [
    "ST261Q03JA",  # Missed school because I was pregnant
    "ST261Q10JA",  # Missed school because I couldn't pay fees
]

SCHOOL_COLS: list[str] = [
    "CNTSCHID",
    "SC016Q02TA"   # percentage fees
]
