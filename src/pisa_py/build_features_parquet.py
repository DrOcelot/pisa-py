from pathlib import Path

import polars as pl

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

JOINED_SURVEY_SUB = DATA_DIR / "built" / "sch_stu_sub.parquet"

joined_lf = pl.scan_parquet(JOINED_SURVEY_SUB)

def add_troll_flags(lf: pl.LazyFrame) -> pl.LazyFrame:
    troll_lf = lf
    exprs = []

    ''' 
    if pupil is male and says missed school because pregnant
    then flag mptroll = 1. If they weren't asked the question
    or they are female then flag mptroll = 0. if they were male
    and asked the question but said no then flag mptroll = -1
    (gender)(missed_school_pregnancy)
    '''
    mp_expr = (
        pl.when(
            (pl.col("gender") == pl.lit("Male"))
            & 
            (pl.col("missed_school_pregnancy") == pl.lit("Yes"))
        )
        .then(+1)
        .when(
            (pl.col("gender") != pl.lit("Male"))
            | 
            (pl.col("gender").is_null())
            | 
            (pl.col("missed_school_pregnancy").is_null())
        )
        .then(0)
        .otherwise(-1)
        .alias("mptroll")
    )
    exprs.append(mp_expr)

    '''
    if pupil said their mother's highest education is less than ISCED3.3 
    which is leaving school with a route that does not lead to higher education
    and that their mother has a phd then mdrtroll = 1. if they
    weren't asked either questions mdrtroll = 0. if they were asked the question
    but were consistent mdrtroll = -1 
    (mother_education_highest)(mother_has_phd)
    '''
    mdr_expr = (
        pl.when(
            (pl.col("mother_education_highest") != pl.lit("<ISCED level 3.4>"))
            & 
            (pl.col("mother_has_phd") == pl.lit("Yes"))
        )
        .then(+1)
        .when(
            (pl.col("mother_education_highest").is_null())
            | 
            (pl.col("mother_has_phd").is_null())
        )
        .then(0)
        .otherwise(-1)
        .alias("mdrtroll")
    )
    exprs.append(mdr_expr)
    
    '''
    ddrtroll flagging done the same as mdrtroll
    (father_education_highest)(father_has_phd)
    '''
    fdr_expr = (
        pl.when(
            (pl.col("father_education_highest") != pl.lit("<ISCED level 3.4>"))
            & 
            (pl.col("father_has_phd") == pl.lit("Yes"))
        )
        .then(+1)
        .when(
            (pl.col("father_education_highest").is_null())
            | 
            (pl.col("father_has_phd").is_null())
        )
        .then(0)        
        .otherwise(-1)
        .alias("fdrtroll")
    )
    exprs.append(fdr_expr)
    
    '''
    if a pupil said they missed school because they couldn't afford fees
    and their school recived 0% of funding from school fees then
    feetroll = 1. if the pupil or school weren't asked the question then feetroll = 0
    if pupil and school were asked the question but the pupil was consistent feetroll = -1
    (missed_school_fees)(school_fee_percentage)
    '''
    fee_expr = (
            pl.when(
                (pl.col("missed_school_fees") == pl.lit("Yes"))
                & 
                (pl.col("school_fee_percentage") <= 0.0)
            )
            .then(+1)
            .when(
                (pl.col("missed_school_fees").is_null())
                | 
                (pl.col("school_fee_percentage").is_null())
            )
            .then(0)
            .otherwise(-1)
            .alias("feetroll")
        )
    exprs.append(fee_expr)

    troll_lf = troll_lf.with_columns(*exprs)
    return troll_lf

troll = add_troll_flags(joined_lf)

troll.sink_parquet(
    f"{DATA_DIR}/built/troll.parquet",
    engine="streaming",
)