# pisa-py

Analysis of disengaged and inconsistent responding in the PISA 2022 student
survey — pupils whose answers look unserious, contradictory or impossible, and
whether that concentrates among low-performing pupils.

## Setup

```bash
git clone https://github.com/DrOcelot/pisa-py.git
cd pisa-py
uv sync --extra dev
```

## Data

None of the data is tracked in git. Download the PISA 2022 student and school
questionnaire files in SPSS format from the
[OECD PISA 2022 database](https://www.oecd.org/pisa/data/2022database/) and
put them in `data/spss/`:

```
data/spss/CY08MSP_STU_QQQ.sav   Student questionnaire, ~2 GB
data/spss/CY08MSP_SCH_QQQ.sav   School questionnaire, ~20 MB
```

Then build the parquet files in order:

```bash
uv run python -m pisa_py.build_parquet           # .sav -> student_22, school_22
uv run python -m pisa_py.build_sub_parquet       # -> sch_stu_sub
uv run python -m pisa_py.build_features_parquet  # -> troll
```

| Output (`data/built/`) | Built by | Contents |
| --- | --- | --- |
| `student_22.parquet` | `build_parquet` | Full OECD student file |
| `school_22.parquet` | `build_parquet` | Full OECD school file |
| `sch_stu_sub.parquet` | `build_sub_parquet` | Student variables of interest joined to their school |
| `troll.parquet` | `build_features_parquet` | `sch_stu_sub` plus inconsistency flags |

### Missing values

SPSS codes several kinds of missing value (not administered, invalid, no
response, …) as numbers above each variable's real range. `build_parquet`
splits these out: the variable itself holds only real answers (null
otherwise), and a companion `<var>_missing_reason` column records why it is
missing.

### Inconsistency flags

Each flag pairs two answers that cannot both be true:

| Flag | Contradiction |
| --- | --- |
| `mptroll` | Male pupil says he missed school because he was pregnant |
| `mdrtroll` | Mother's highest schooling is below ISCED 3.4, but she has a PhD |
| `fdrtroll` | Father's highest schooling is below ISCED 3.4, but he has a PhD |
| `feetroll` | Pupil missed school over fees at a school that charges none |

`1` means the answers contradict, `-1` means both were answered consistently,
and `0` means the check doesn't apply (an answer is missing, or for
`mptroll`, the pupil isn't male).

## Layout

```
src/pisa_py/build_parquet.py           SPSS -> parquet, missing-value handling
src/pisa_py/build_sub_parquet.py       Column selection, renaming, school join
src/pisa_py/build_features_parquet.py  Inconsistency flags
teach/learnt.md                        Learning notes
```

## Development

```bash
uv run ruff check src     # lint
uv run mypy src           # type check (strict)
```
