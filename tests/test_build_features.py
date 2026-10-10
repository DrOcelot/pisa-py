import polars as pl
from polars.testing import assert_frame_equal

from pisa_py.build_features_parquet import (
    make_fdr_flag_expr,
    make_fee_flag_expr,
    make_mdr_flag_expr,
    make_mp_flag_expr,
)


def test_mptroll():
    mptroll_test_values = pl.LazyFrame(
        {
            "gender": 
                [
                    "Male","Male","Male",
                    "Female","Female","Female",
                    None,None,None, 
                ],
            "missed_school_pregnancy": 
                [
                    "Yes", "No", None,
                    "Yes", "No", None,
                    "Yes", "No", None,
                ]
        }
    )
    mptroll_expected = pl.LazyFrame(        
        {
            "mptroll": 
                [
                    1, -1, 0,
                    0, 0, 0,
                    0, 0, 0,
                ]
        },
        schema={"mptroll":pl.Int8},
    )
    result = mptroll_test_values.with_columns(make_mp_flag_expr())

    assert_frame_equal(result.select("mptroll").collect(), mptroll_expected.collect())

def test_mdrtroll():
    mdrtroll_test_values = pl.LazyFrame(
        {
            "mother_education_highest": 
                [
                    "<ISCED level 3.4>", "<ISCED level 3.4>", "<ISCED level 3.4>",
                    "<ISCED level 3.3>", "<ISCED level 3.3>", "<ISCED level 3.3>",
                    "<ISCED level 2>", "<ISCED level 2>", "<ISCED level 2>",
                    "<ISCED level 1>", "<ISCED level 1>", "<ISCED level 1>",
                    "She did not complete <ISCED level 1>.", 
                    "She did not complete <ISCED level 1>.", 
                    "She did not complete <ISCED level 1>.",
                    None, None, None
                ],
            "mother_has_phd": 
                [
                    "Yes", "No", None,
                    "Yes", "No", None,
                    "Yes", "No", None,
                    "Yes", "No", None,
                    "Yes", 
                    "No", 
                    None,
                    "Yes", "No", None,
                ]
        }
    )
    mdrtroll_expected = pl.LazyFrame(        
        {
            "mdrtroll": 
                [
                    -1, -1, 0,
                    1, -1, 0,
                    1, -1, 0,
                    1, -1, 0,
                    1,
                    -1,
                    0,
                    0, 0, 0,
                ]
        },
        schema={"mdrtroll":pl.Int8},
    )
    result = mdrtroll_test_values.with_columns(make_mdr_flag_expr())

    assert_frame_equal(result.select("mdrtroll").collect(), mdrtroll_expected.collect())

def test_fdrtroll():
    fdrtroll_test_values = pl.LazyFrame(
        {
            "father_education_highest": 
                [
                    "<ISCED level 3.4>", "<ISCED level 3.4>", "<ISCED level 3.4>",
                    "<ISCED level 3.3>", "<ISCED level 3.3>", "<ISCED level 3.3>",
                    "<ISCED level 2>", "<ISCED level 2>", "<ISCED level 2>",
                    "<ISCED level 1>", "<ISCED level 1>", "<ISCED level 1>",
                    "He did not complete <ISCED level 1>.", 
                    "He did not complete <ISCED level 1>.", 
                    "He did not complete <ISCED level 1>.",
                    None, None, None
                ],
            "father_has_phd": 
                [
                    "Yes", "No", None,
                    "Yes", "No", None,
                    "Yes", "No", None,
                    "Yes", "No", None,
                    "Yes", 
                    "No", 
                    None,
                    "Yes", "No", None,
                ]
        }
    )
    fdrtroll_expected = pl.LazyFrame(        
        {
            "fdrtroll": 
                [
                    -1, -1, 0,
                    1, -1, 0,
                    1, -1, 0,
                    1, -1, 0,
                    1,
                    -1,
                    0,
                    0, 0, 0,
                ]
        },
        schema={"fdrtroll":pl.Int8},
    )
    result = fdrtroll_test_values.with_columns(make_fdr_flag_expr())

    assert_frame_equal(result.select("fdrtroll").collect(), fdrtroll_expected.collect())

def test_feetroll():
    feetroll_test_values = pl.LazyFrame(
        {
            "missed_school_fees": 
                [
                    "Yes", "Yes", "Yes", "Yes",
                    "No", "No", "No", "No", 
                    None, None, None, None,
                ],
            "school_fee_percentage": 
                [
                    10.0, 0.0, -10.0, None,
                    10.0, 0.0, -10.0, None,
                    10.0, 0.0, -10.0, None,
                ]
        }
    )
    feetroll_expected = pl.LazyFrame(        
        {
            "feetroll": 
                [
                    -1, 1, 1, 0,
                    -1, -1, -1, 0,
                    0, 0, 0, 0,
                ]
        },
        schema={"feetroll":pl.Int8},
    )
    result = feetroll_test_values.with_columns(make_fee_flag_expr())

    assert_frame_equal(result.select("feetroll").collect(), feetroll_expected.collect())