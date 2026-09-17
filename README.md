# pisa-py

Analysis of disengaged and inconsistent responding in the PISA 2022 student
survey — pupils whose answers look unserious, contradictory or impossible, and
whether that concentrates among low-performing pupils.

## Setup

Git LFS is required **before cloning**, because the data file is stored as an
LFS object. Without it you get a 134-byte pointer instead of the parquet, and
Polars fails with a confusing parquet error.

```bash
sudo apt install git-lfs    # or: brew install git-lfs / winget install GitHub.GitLFS
git lfs install

git clone https://github.com/DrOcelot/pisa-py.git
cd pisa-py

python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
```

If you cloned before installing Git LFS, `git lfs pull` fetches the real file.

Then open `notebooks/eda.ipynb` and select the `.venv` interpreter.

## Data

| File | Tracked | Notes |
| --- | --- | --- |
| `data/pisa_2022_subset.parquet` | Git LFS | 613,744 pupils × 482 columns, 128 MB |
| `data/Codebook.csv` | git | Reviewer annotations; drives the column selection |
| `data/pisa_varlabels.csv` | git | Variable name → question text |
| `data/PISA_2022_student.parquet` | Git LFS | Full OECD student file, 702 MB |
| `data/PISA_2022_school.parquet` | Git LFS | Full OECD school file, 5 MB |
| `data/CY08MSP_STU_QQQ.SAS7BDAT` | ignored | Raw OECD student SAS export, 3.8 GB |
| `data/CY08MSP_SCH_QQQ.SAS7BDAT` | ignored | Raw OECD school SAS export, 40 MB |

The subset holds every variable under investigation: identifiers, gender,
parental education, all thirty plausible values, the final student weight,
every variable carrying a reviewer comment in `Codebook.csv`, and every
variable its `DISENGAGED` flag marks. The raw SAS exports are gitignored
(too large to be worth tracking even via LFS) and are available from the
[OECD PISA 2022 database](https://www.oecd.org/pisa/data/2022database/);
convert them to parquet to rebuild the full files above.

To change what the subset carries, edit the `DISENGAGED` column in
`Codebook.csv` (or the column lists in `src/pisa_py/io.py`) and rebuild:

```bash
make-subset
```

That needs the raw parquet present, and rewrites the committed subset —
so only do it when the selection actually changes. Each rebuild adds
another ~128 MB to LFS storage permanently. GitHub's free plan gives every
repository 10 GiB of LFS storage (2 GiB per individual file), so there's
plenty of headroom here.

## Layout

```
src/pisa_py/io.py        Column definitions, subset building, loading
src/pisa_py/features.py  Mean score, performance deciles, gender-ability groups
notebooks/eda.ipynb      Exploratory analysis
tests/                   pytest suite
```

## Development

```bash
ruff check src tests      # lint
mypy src tests            # type check (strict)
pytest                    # tests
```
