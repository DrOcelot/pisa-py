'''Pull together the school and student surveys 
into a single lazyframe that contains all the variables of use
and then export it to a parquet file. These variable conjunctions are ones that can explicitly be 
described as impossible to be true so indicate a pupil whol is "trolling" 
or not paying attention to the survey.'''

from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

STUDENT_SURVEY_FULL = DATA_DIR / "PISA_2022_student.parquet"
SCHOOL_SURVEY_FULL = DATA_DIR / "PISA_2022_school.parquet"

# region Column groupings
# PLausible values for all three domains
PV_COLS: list[str] = [
    f"PV{i}{domain}" for domain in ("MATH", "READ", "SCIE") for i in range(1, 11)
]

# weight columns and final student weight
WT_COLS: list[str] = [
    f"W_FSTURWT{i}" for i in range(1, 81)
]

# Final student weight
FINAL_WEIGHT: list[str] = ["W_FSTUWT"]  

# Country ID,Pupil ID and School ID Cols
ID_COLS: list[str] = [
    "CNT",       # Country name
    "CNTSCHID",  # Unique school id
    "CNTSTUID",  # Unique student id
]

# Gender and socio-economics status.
DEMOGRAPHIC_COLS: list[str] = [
    "ST004D01T",  # Student (standardised) gender
    "ESCS",       # Economic, social and cultural status (standardised)
]

# Parental education information. A parent with a PhD should have completed a degree.
PARENTAL_EDUCATION_COLS: list[str] = [
    "ST005Q01JA",  # Mother's highest level of schooling (ISCED)
    "ST006Q01JA",  # Mother has a PhD
    "ST007Q01JA",  # Father's highest level of schooling (ISCED)
    "ST008Q01JA",  # Father has a PhD
]

# Boy's cannot be pregnant. Pupils at non-fee paying schools should not be paying fees.
FACTOR_COLS: list[str] = [
    "ST261Q03JA",  # Missed school because I was pregnant
    "ST261Q10JA",  # Missed school because I couldn't pay fees
]

# School ID to match to pupil and an indicator of if the school is fee paying.
SCHOOL_COLS: list[str] = [
    "CNTSCHID",
    "SC016Q02TA"   # percentage fees
]
# endregion

def build_school(path: Path = SCHOOL_SURVEY_FULL) -> pl.LazyFrame:
    """Scan the OECD school file as a Polars LazyFrame.

    The scan stays lazy, so selecting a handful of columns from the result
    reads only those columns off disc.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. If you have just cloned, run `git lfs pull` to "
            "fetch it; otherwise rebuild it with the `make-subset` command."
        )
    schdf = pl.scan_parquet(path)
    schdf = (
        schdf.select(SCHOOL_COLS)
        .rename({"SC016Q02TA": "school_fee_percentage"})
    )
    return schdf

def build_student(path: Path = STUDENT_SURVEY_FULL) -> pl.LazyFrame:
    """Scan the OECD student file as a Polars LazyFrame.

    The scan stays lazy, so selecting a handful of columns from the result
    reads only those columns off disc.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. If you have just cloned, run `git lfs pull` to "
            "fetch it; otherwise rebuild it with the `make-subset` command."
        )
    studf = pl.scan_parquet(path)
    studf = (
        studf.select(
            ID_COLS
            + DEMOGRAPHIC_COLS
            + PARENTAL_EDUCATION_COLS
            + FACTOR_COLS
            + PV_COLS
            + WT_COLS
            + FINAL_WEIGHT
        )
        .rename(
            {"W_FSTUWT": "final_student_weight",
            **{f"W_FSTURWT{i}": f"replicate_student_weight_{i}" for i in range(1, 81)},
            "ST004D01T": "gender",
            "ST005Q01JA": "mother_education_highest",
            "ST006Q01JA": "mother_has_phd",
            "ST007Q01JA": "father_education_highest",
            "ST008Q01JA": "father_has_phd",
            "ST261Q03JA": "missed_school_pregnancy",
            "ST261Q10JA": "missed_school_fees"}
        )
    )
    return studf

jndf = build_student().join(build_school(), on="CNTSCHID", how="left")
print(jndf.columns)