"""Loading and subsetting of the PISA 2022 student file.

The raw OECD student file is far too large to keep in version control (a 4.1 GB
SAS export, or 736 MB once converted to parquet), so it is gitignored and only
the derived subset built here is committed. Re-create the raw file by
downloading it from the OECD PISA 2022 database.

The subset is stored with Git LFS (see .gitattributes), which keeps the parquet
out of the git pack itself: history holds a small pointer file, and the bytes
live in LFS storage. Rebuilding and committing the subset therefore adds a new
LFS object rather than growing the history every clone must download.
"""

from pathlib import Path

import polars as pl

# Anchored to the repository rather than the working directory, so notebooks and
# scripts resolve the same files wherever they are run from. This assumes an
# editable install (`pip install -e .`), which is how the project is used.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"

RAW_PARQUET = DATA_DIR / "PISA_2022_student.parquet"
SUBSET_PARQUET = DATA_DIR / "pisa_2022_subset.parquet"
SCHOOL_PARQUET = DATA_DIR / "PISA_2022_school.parquet"
CODEBOOK_CSV = DATA_DIR / "Codebook.csv"
VARLABELS_CSV = DATA_DIR / "pisa_varlabels.csv"

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

# All ten plausible values per domain. PISA estimates must be computed across
# every plausible value and averaged; using only PV1 understates uncertainty.
PV_COLS: list[str] = [
    f"PV{i}{domain}" for domain in ("MATH", "READ", "SCIE") for i in range(1, 11)
]

WEIGHT_COLS: list[str] = [
    "W_FSTUWT",  # Final student weight
]

# The variables named directly in this module, before the codebook's
# disengagement flags are folded in by `subset_columns`.
CORE_COLS: list[str] = list(
    dict.fromkeys(
        [
            *ID_COLS,
            *DEMOGRAPHIC_COLS,
            *PARENTAL_EDUCATION_COLS,
            *FACTOR_COLS,
            *PV_COLS,
            *WEIGHT_COLS,
        ]
    )
)

def load_school(path: Path = SCHOOL_PARQUET) -> pl.LazyFrame:
    """Scan the OECD school file as a Polars LazyFrame.

    The scan stays lazy, so selecting a handful of columns from the result
    reads only those columns off disc.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. If you have just cloned, run `git lfs pull` to "
            "fetch it; otherwise rebuild it with the `make-subset` command."
        )
    schldf = pl.scan_parquet(path)
    schldf = schldf.select("CNTSCHID","SC016Q02TA")
    return schldf

def read_codebook(path: Path = CODEBOOK_CSV) -> pl.DataFrame:
    """Read the reviewer-annotated codebook, normalising its column names."""
    codebook = pl.read_csv(path, infer_schema_length=0, encoding="utf8-lossy")
    return codebook.rename({name: name.strip().lstrip("﻿") for name in codebook.columns})

def subset_columns(codebook: Path = CODEBOOK_CSV) -> list[str]:
    """Every column the committed subset carries, in a stable order."""
    return list(dict.fromkeys([*CORE_COLS]))


def variable_labels(path: Path = VARLABELS_CSV) -> dict[str, str]:
    """Map PISA variable names to their question text.

    Example:
        >>> variable_labels()["ST004D01T"]
        'Student (Standardized) Gender'
    """
    labels = pl.read_csv(path)
    return dict(
        zip(labels.get_column("name"), labels.get_column("label"), strict=True)
    )


def build_subset(
    source: Path = RAW_PARQUET,
    dest: Path = SUBSET_PARQUET,
    columns: list[str] | None = None,
) -> Path:
    """Write the analysis subset from the full raw student file.

    Args:
        source: The full PISA 2022 student parquet file.
        dest: Where to write the subset.
        columns: Columns to keep. Defaults to `subset_columns()`.

    Returns:
        The path written to.

    Raises:
        FileNotFoundError: If `source` is missing.
        KeyError: If any requested column is absent from `source`.
    """
    if not source.exists():
        raise FileNotFoundError(
            f"{source} not found. It is gitignored; download the PISA 2022 "
            "student file from the OECD and convert it to parquet first."
        )

    keep = subset_columns() if columns is None else columns
    frame = pl.scan_parquet(source)
    available = set(frame.collect_schema().names())
    if missing := [column for column in keep if column not in available]:
        raise KeyError(f"Columns absent from {source}: {missing}")

    dest.parent.mkdir(parents=True, exist_ok=True)
    frame.select(keep).sink_parquet(dest, compression="zstd")
    return dest


def load_subset(path: Path = SUBSET_PARQUET) -> pl.LazyFrame:
    """Scan the committed analysis subset as a Polars LazyFrame.

    The scan stays lazy, so selecting a handful of columns from the result
    reads only those columns off disc.
    """
    if not path.exists():
        raise FileNotFoundError(
            f"{path} not found. If you have just cloned, run `git lfs pull` to "
            "fetch it; otherwise rebuild it with the `make-subset` command."
        )
    return pl.scan_parquet(path)


def main() -> None:
    """Build the subset and report what was written."""
    destination = build_subset()
    size_mb = destination.stat().st_size / 1_000_000
    rows = pl.scan_parquet(destination).select(pl.len()).collect().item()
    columns = len(subset_columns())
    print(f"Wrote {destination} ({rows:,} rows, {columns} columns, {size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
