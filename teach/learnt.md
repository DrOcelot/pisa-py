# Learning log

Where I am in learning Python, followed by reference notes on concepts
covered so far, ordered from most fundamental to most niche.

## Progress

**Background:** comes to Python from R (tidyverse pipes, dplyr, `NA`) and
some JavaScript, so new ideas land best when compared to those (`|>`,
`OVER (PARTITION BY)`, JS `...` and `? :`). Learning through a real data
project (survey data, Polars, parquet) rather than standalone exercises.

**Journey so far** (started Sept 2026):
1. **Reading existing code.** Walked through working modules line by line
   to learn core syntax (paths, comprehensions, unpacking, walrus, f-strings)
   and the Polars mental model: expressions vs frames, lazy plans,
   `group_by`/`agg`, `.over()`.
2. **Exploring in Jupyter.** Plotting and debugging blank results; learnt to
   narrow a problem down step by step and to check the data before the code.
3. **Writing pipeline code.** Rewrote a pandas data build in Polars, which
   meant chasing down a memory crash (dtypes, Enums, batched
   `.with_columns()`, streaming engines) and opening a PR on an upstream
   library. Then wrote new scripts: selecting and renaming columns from a
   schema, and building derived flag columns with chained `when/then`.
   Picked up list/dict mechanics and null logic along the way.
4. **Code quality.** Tidying the project: `main()` and import
   side effects, package layout, naming, refactoring into testable
   functions, first pytest tests, mypy, and uv/VS Code tooling.
5. **Batched build (current).** Rewrote the `.sav` → parquet build to read
   in chunks with a generator and write a folder of part files. Hit (and
   fixed) all-null chunks being typed `Null` by casting each chunk to the
   metadata's dtypes. Discussed, but chose not to build, a process pool for
   speed (not worth it for a build run a couple of times).

**Comfortable with:** everyday syntax, lists/dicts, reading and writing
Polars pipelines, reading tracebacks, basic pytest, consuming generators in
a `for` loop.

**Not yet covered:** classes and OOP, writing `try`/`except` handling,
writing your own generators (`yield`), decorators, context managers
(`with`) beyond using them, fixtures and parametrised tests, logging, type
hints beyond the basics, `concurrent.futures` / multiprocessing in practice.

---

## 1. Python language

### Comments, strings and docstrings
- `#` is a true comment: discarded by the parser, never exists at runtime.
- `"""..."""` is a real string literal, not a comment. In docstring position
  (first statement of a module/function/class) it becomes `.__doc__`.
- `f"..."` evaluates any `{expr}` inside as real Python and stringifies the
  result; without the `f`, `"{expr}"` is just literal text.
- `.strip()` removes whitespace from both ends; `.lstrip(char)` removes a
  specific character from the left only (e.g. a UTF-8 BOM, `"﻿"`).
- `repr()` gives the unambiguous, developer-facing form of a value, showing
  what `str()`/`print()` hide: `repr("Germany ")` is `'Germany '`, revealing
  the trailing space.

### Syntax gotchas
- `=` assigns; `==` compares. Inside a call's parentheses `name=value` is a
  keyword argument, so `f(x = "a")` where a comparison was meant fails with
  "expected a parameter name".
- Python has no `===`/`!==` (JavaScript) and no `&&`/`||`; it has `==`/`!=`
  and `and`/`or`/`not`.
- `and`/`or`/`not` work on single True/False values. `&`/`|`/`~` are bitwise
  operators that libraries like Polars overload to work element by element.
  They bind more tightly than `==`, so each side needs its own parentheses:
  `(a == 1) & (b == 2)`.
- Python ignores indentation inside open brackets, so badly indented
  arguments still run; formatters fix the look.

### Expressions vs statements
- Conditional (ternary) expression: `value_if_true if condition else
  value_if_false`, like JS's `condition ? a : b` reordered to read like a
  sentence.
- Walrus operator `:=` (3.8+) assigns and evaluates to the value in one
  expression: `if missing := [...]:` assigns `missing`, tests it, and leaves
  it available inside the `if` block.
- A `for` loop or assignment is a statement: it has no value.

### Names, objects and binding
- `a = b` doesn't copy; both names point at the *same* object. Mutating it
  (`.append()`) is visible through both names. Rebinding (`a = a + [...]`)
  builds a new object and points only `a` at it; `b` is untouched.
- Rebinding a loop's source name inside `for x in xs:` doesn't affect the
  loop: the iterator was created over the original object when the loop
  started.
- Functions are first-class objects: they can be bound to another name
  (`hog = print`), stored in a list/dict, or passed into another function
  (`sorted(words, key=len)`, like R's `sapply(x, mean)`).
- `obj.method` (no brackets) is the method object itself, not a result; the
  `()` is what calls it. Forgetting them often errors later and confusingly
  (e.g. Polars: "cannot create expression literal for value of type method").
- Method chaining (`.a().b()`) reads like R's `|>` pipes, but each call is a
  method defined on the object returned by the previous one, not syntactic
  rewriting.

### Lists
- `list + list` concatenates into a new list; `list + "str"` raises
  `TypeError: can only concatenate list (not "str") to list`. Wrap a single
  item: `xs + [item]`.
- `.append(item)` adds one item in place; `.extend(iterable)` adds each item
  *of* a collection in place. `.extend()` on a non-iterable fails with
  `TypeError: '...' object is not iterable`.
- List comprehension: `[<expression> for <item> in <iterable> if <condition>]`.
  The leading expression can be anything, not just the loop variable.
- Every comprehension needs: the result expression, `for`, the loop
  name(s), `in`, the iterable. Putting the iterable where the names go gives
  mypy's confusing "Cannot assign to function call".

### Dicts and sets
- Dict comprehension: `{key: value for k, v in d.items()}`. The key is the
  *address* (e.g. which column); the value is what it maps to.
- A plain dict is the tool for "look up X, get Y" in Python
  (`{"double": pl.Float64, "string": pl.String}`); Polars dtypes are just
  objects and can be dict values. `when/then` is for per-row *data* inside a
  frame, not for translating Python values.
- Chaining two dicts through a comprehension:
  `{name: sounds[animal] for name, animal in pets.items()}` turns
  name → animal and animal → sound into name → sound.
- `dict.fromkeys(iterable)` makes each element a key (value `None`). Keys are
  unique and keep insertion order (3.7+), so `list(dict.fromkeys(xs))` is the
  standard "dedupe while keeping order" idiom.
- `for k in d:` gives keys only. `.items()` gives `(key, value)` pairs,
  `.keys()`/`.values()` one side each.
- `d.update({...})` adds or overwrites entries in place. Naming a dict
  (rather than writing it inline as a literal) lets you read it back and
  derive new entries from it in a loop.
- `set`: unordered, duplicate-free, built for fast (~O(1)) membership tests
  (`x in s`), unlike a list (O(n)).

### Unpacking
- `[*a, *b]` spreads iterables into a list literal (like JS `...`), so
  `list(dict.fromkeys([*a, *b]))` = concatenate then dedupe.
- `**d` spreads a dict into a dict literal or into keyword arguments
  (`f(**{"a": 1})` is `f(a=1)`).
- Loops over pairs unpack in the header: `for k, v in d.items():`,
  `for x, y in zip(a, b):`, `for i, x in enumerate(xs):`.
- `zip(...)` pairs iterables element by element into tuples (lazily);
  `strict=True` (3.10+) raises on mismatched lengths instead of silently
  truncating.
- `a, b = x` iterates over `x` and needs *exactly* 2 items: 1 item gives
  "not enough values to unpack (expected 2, got 1)", 3 gives "too many
  values to unpack". Check *what level* you're unpacking: the whole
  collection or each item in it.
- `enumerate(xs)` yields `(count, item)` pairs, counting from 0
  (`start=1` to change). Like R's `seq_along` but giving the item too.
- Nested unpacking mirrors the shape with brackets:
  `for i, (df, meta) in enumerate(pairs):`.

### Generators and iterators
- A generator function uses `yield` instead of `return`. Calling it runs
  *nothing*; it returns a generator object (a "dispenser"). Each time a
  `for` loop asks for the next item, it runs up to the next `yield`, hands
  that value over and pauses. Same idea as JS `function*`.
- Memory win: only the current item needs to exist. When the loop name is
  rebound to the next item, the old one can be freed.
- Generators are sequential (one reader moving forward), so they can't be
  shared out between parallel workers.
- In docs, a **Yields:** heading (instead of **Returns:**) and a type hint
  like `Iterator[tuple[A, B]]` mean "this is a generator; loop over it, and
  each item looks like this".

### Functions
- A function defined inside another function is a local name, unreachable
  from outside. Module-level functions are importable. (`global` is a
  separate keyword for reassigning module-level variables.)
- Mutable default trap: defaults are evaluated once at `def` time, so
  `def f(x=[])` shares one list across calls. Use `x: list | None = None`,
  then `if x is None: x = [...]` inside.

### Exceptions
- `raise SomeError(...)` aborts normal execution and propagates up the call
  stack (unless caught by `try`/`except`); it's not just a printed message.
- Pick the conventional error type for the meaning, e.g. `KeyError` for
  "requested thing not found", even without a literal dict lookup.

### Three-valued logic with null
- Plain Python: `None == "x"` is `False`, `None != "x"` is `True`.
- SQL, R's `NA` and Polars treat null as "unknown": any comparison with null
  gives null. `&`/`|` follow "does the unknown matter?": `null | True` →
  `True`, `null | False` → null, `null & False` → `False`, `null & True` →
  null.
- `.is_null()` / `.is_not_null()` are the way to get a definite True/False.

## 2. Modules, imports and project structure

- Importing a module runs every top-level statement in it. Definitions
  (constants, paths, `def`s) belong at module level; actions (reading data,
  computing, writing files) belong inside `main()`, otherwise any import
  triggers them (and breaks if, say, an input file doesn't exist yet).
- `__name__` is `"__main__"` when a file is run directly (`python -m ...`) and
  the import name otherwise, so `if __name__ == "__main__": main()` means
  "only run when executed directly".
- `import` takes a dotted module name, not a path: with a `src/` layout,
  `src/pkg/mod.py` is imported as `pkg.mod`.
- A distribution name (pip/uv) can use hyphens (`my-pkg`); the import name
  can't (`my_pkg`).
- Import order: standard library, then third-party, then your own code, with
  blank lines between groups. `ruff check --fix` sorts them.
- `pathlib.Path`: object-oriented paths; creating one doesn't touch disk.
  `/` joins segments (operator overloading via `__truediv__`).
  `Path(__file__)` is the current module's file; `.parent`/`.parents[n]` walk
  up; `.resolve()` makes it absolute; `.name` is just the filename;
  `.exists()` and `.mkdir(parents=True, exist_ok=True)` touch the disk.
  Storing full `Path`s (rather than building strings in a loop) keeps code
  simpler.
- A `Path` doesn't know whether it's a file or a folder; that's only found
  out from disk (`.is_dir()`). Trailing slashes are stripped
  (`Path("a/") == Path("a")`), so write `DATA_DIR / "built" / "school_22"`.

## 3. Writing readable code

- Name = what it holds + what kind: `survey_df`, `survey_lf`,
  `survey_metadata`. Don't name by type alone (`lazy_data`, `path_dict`);
  type hints already say that.
- Name dicts for the key → value relationship (`in_paths_out_paths`, "values
  by key"). Check loop variable names against what they really hold.
- Derive values from the source of truth instead of hardcoding them (e.g.
  check a real schema for which columns exist) so code doesn't silently go
  stale when the data changes.
- YAGNI ("you aren't gonna need it"): don't add flexibility (extra optional
  parameters etc.) until a real need shows up.
- Refactor = same behaviour from outside, different structure inside.
  Restructuring so code *can* be tested is fine (e.g. one function per
  concern); changing behaviour to make a test pass isn't. Check: "would this
  change make sense if the tests didn't exist?"
- A code comment isn't needed when the code is self-explanatory; the *why* of
  a change belongs in the commit message / PR description.
- Fix bad data "at the door": correct it right after reading (e.g. casting
  dtypes) rather than patching each downstream function, which can then
  trust its input. Patching downstream also misses columns that never pass
  through that function.
- Weigh automation against how often it runs: halving a 10-minute build run
  a couple of times isn't worth an hour of extra code and complexity.

## 4. Errors, debugging and checking your work

- Reading a traceback: start at the bottom `E` line for the actual error,
  then find the last line in *your* file for where it was triggered. Library
  frames in between can usually be skipped, though the `>` line sometimes
  shows the exact rule that was broken.
- "Runs without error" isn't "correct" or "efficient". Check actual values
  and dtypes, not just the absence of an exception; wasteful choices (like a
  bad dtype) can run fine for months.
- Look at the real data before writing logic for it (e.g. list a column's
  distinct values with counts before reaching for regex). It's often simpler
  than assumed, and the source documentation (codebooks) defines what values
  actually mean.
- Work outward from the smallest suspect piece: test the raw operation
  before blaming a wrapper, `repr()` a value before assuming a string
  mismatch, check upstream data for nulls before blaming plotting code. The
  "bug" is sometimes a genuine gap in the source data.
- Change one variable at a time, using synthetic data at a matching scale,
  rather than changing several things and guessing which mattered.
- A library's benchmark claims may come from a simpler case than yours;
  verify on your own data's shape.
- If the last line of *your* file in a traceback is just a call (e.g. the
  `for` line), and everything below it is library code, the failure is
  inside the library, not in your logic.
- An error that changes when you change a parameter (e.g. chunk size) is a
  clue: work out what the parameter changes (e.g. how many items there are)
  and compare it with the message.
- Sparse data is often clustered: in a file sorted by country, a question
  asked in only 4 countries has values in a few tight clumps, with huge
  empty gaps between them. Any slice that lands in a gap is entirely null.

## 5. Testing and type checking

### pytest
- pytest finds `test_*.py` files (in `tests/`) and runs functions named
  `test_*`. A plain `assert` is the check; without one, a test only checks
  "didn't crash".
- Shape: arrange (tiny hand-made input + expected output), act (call the
  code), assert (compare). Keep input inside the test so it reads on its
  own; *fixtures* are for genuinely shared setup.
- The most valuable test cases are ones that would fail if one specific
  condition were removed from the code (each row proves one condition is
  needed).
- Change a test when the *intended* behaviour changes, never just to make it
  go green.

### mypy
- Python lets a name be rebound to any type; mypy gives each variable one type
  for its whole scope. `data = data.lazy()` (DataFrame → LazyFrame) is an
  error, and mypy then also flags later uses.
- Fix with one name per kind of thing (`survey_df` → `survey_lf`), not a
  union annotation that pushes the problem downstream.

## 6. Polars

### Expressions vs frames
- `pl.col(...)`, `pl.lit(...)`, `pl.when(...)`, `pl.mean_horizontal(...)` etc.
  return an **expression** (`pl.Expr`): a plan for one column's worth of
  computation. It can't be collected on its own; it means something only when
  passed into a frame method.
- Heuristic: frame methods are table-shaped (`.filter()`, `.select()`,
  `.with_columns()`, `.group_by()`, `.join()`, `.drop()`); expression methods
  are column-shaped (`.cast()`, `.alias()`, `.is_null()`, `.qcut()`,
  `.over()`). Anything passed *into* a frame method is an expression.
- Expressions are values, so helper functions can take and return them.
- Methods on an expression return another expression, e.g. `.is_null()` is a
  per-row boolean mask, not one True/False.
- Namespace accessors (`.str`, `.dt`, `.list`) group type-specific
  operations; they're not casts.

### Selecting and adding columns
- `select()` picks columns; `filter()` picks rows using a boolean mask (one
  bool per row, not stored as a column), like dplyr/SQL. pandas' `.filter()`
  is different: it picks by *label*.
- `.with_columns(expr.alias("name"))` returns a new frame with that column
  added (or overwritten if the name exists); everything else passes through.
- Expressions in the *same* `.with_columns(a, b)` call are evaluated
  independently against the input frame; they can't see each other's
  output. Two with the same alias raise `DuplicateError`.
- Collect expressions in a list and call `.with_columns(*exprs)` once rather
  than chaining one `.with_columns()` per column in a loop: logically the
  same, but the chained version builds a much deeper plan that's slower and
  more memory-hungry at scale.

### Conditionals and constants
- `pl.when(c1).then(v1).when(c2).then(v2).otherwise(default)` is a row-wise
  if/elif/else (a vectorised switch). `.then()`/`.otherwise()` accept any
  expression, like `np.where(cond, a, b)`.
- **First match wins**: later `.when()`s only see unclaimed rows, so they
  don't need to repeat earlier checks (e.g. null checks). A null condition
  counts as no match.
- `.otherwise(value)` instead of a final explicit `.when()` is shorter, but
  unexpected values silently get that value; an explicit final branch plus
  `.otherwise(None)` leaves them as visible nulls.
- `pl.lit(x)` inserts a constant; `pl.concat_str(a, b, ...)` joins string
  expressions row-wise.
- `Expr.replace_strict(mapping, default=..., return_dtype=...)` maps values
  through a dict (pandas' `.map(dict)`); the older `.replace()` implicit
  dtype behaviour and `map_dict` are deprecated.

### Dtypes
- A plain `String` column stores the full text per row; for a few values
  repeated across many rows, `pl.Enum(categories)` (fixed, ordered
  vocabulary) or `pl.Categorical` is several times smaller.
- `pl.Enum` needs a unique category list (`list(dict.fromkeys(values))`).
- Mixing dtypes across `when/then/otherwise` branches forces Polars to
  reconcile types, sometimes via a deprecated implicit cast. Set
  `default=`/`return_dtype=` so each branch has the right type, rather than
  suppressing the warning.
- A column with no non-null values gets dtype `Null` (nothing to infer
  from). It can't hold any value, so mapping (`replace_strict`) fails
  ("conversion from `f64` to `null` failed"), and so does stacking it with
  a `Float64` piece ("type Float64 is incompatible with expected type
  Null").
- `df.cast({col: dtype, ...})` casts many columns at once. Like most frame
  methods it returns a *new* frame, so reassign: `df = df.cast(...)` (fine
  for mypy, since the type stays `DataFrame`).
- Python ints become Int64 by default, but integer literals in
  `when/then/otherwise` land on Int32. Pin dtypes deliberately with
  `.cast()` at the end (e.g. Int8 for -1/0/1; it must be signed, since UInt8
  can't hold -1).

### Grouping and window functions
- `frame.group_by([...])` returns an intermediate `GroupBy`: "piles of rows"
  per unique key combination, not a frame (piles have different sizes).
- `.agg(...)` reduces each pile to one row: `pl.len()` (row count, like SQL
  `COUNT(*)`; `pl.count()` is deprecated), `.mean()`, `.sum()`,
  `.min()`/`.max()`, `.n_unique()`, `.first()`, or a bare `pl.col(...)` for a
  list-typed cell of the whole pile. Several aggregates can be passed at once.
- `.over(group)` is SQL's `OVER (PARTITION BY ...)`: it re-evaluates
  everything to its left in the chain within each group and maps results
  back to the original rows, without collapsing them. Placement matters:
  `pl.col("x").qcut(10).over(g)` is per group; `pl.col("x").over(g).qcut(10)`
  is global.
- `.qcut(n, labels=[...])` splits a numeric column into `n` equal-sized
  quantile buckets.
- Percentage within group: `group_by([key, group]).agg(pl.len().alias("n"))`
  then `(pl.col("n") / pl.col("n").sum().over(group) * 100)`. Needed when
  groups have different totals, so raw counts aren't comparable.

### Lazy vs eager execution
- `pl.scan_parquet(...)` returns a `LazyFrame`: a plan over the file, not
  loaded data, so column selection and filters can be pushed down to the
  reader.
- `.collect()` runs the plan (letting the optimiser skip unneeded work) and
  returns a `DataFrame`. Convention: functions returning a `LazyFrame` are
  meant to be chained further; a function that collects is a pipeline
  endpoint.
- `.sink_parquet(...)` executes a plan and writes to disk. Its
  `engine="auto"` default can silently pick the in-memory engine (no disk
  writes until near the end); pass `engine="streaming"` to stream. Even then,
  some operations may not stream efficiently for unusual shapes (e.g. very
  wide schemas).
- Wrapping already-loaded data in `pl.LazyFrame(...)` only makes later
  operations lazy; the source is still fully in memory. A genuine lazy
  *source* (`scan_*`) is different.
- Converting from pandas (`pl.from_dataframe`, `pl.LazyFrame(pandas_df)`)
  isn't always zero-copy: one incompatible column (e.g. `object` dtype)
  makes Polars copy the *entire* frame.

### Batched parquet (folder datasets)
- To keep memory bounded: read a chunk, transform it, write it as its own
  file (`folder / f"part-{n}.parquet"`), move on. Peak memory is about one
  chunk.
- `pl.scan_parquet(folder)` reads every parquet file in it as one table;
  downstream code can't tell the difference from a single file.
- All parts must have identical schemas, so cast each chunk to a fixed
  dtype per column rather than trusting per-chunk inference.
- Rerunning only overwrites parts with the same names. If the chunk size
  changes and there are fewer parts, the old extras stay and get read twice.
  Clear the folder first.
- Delete superseded output files so a missed path fails loudly rather than
  silently reading stale data.

### Schema and file metadata
- `lf.collect_schema().names()` lists column names cheaply; use it to check a
  column exists before selecting it.
- Row counts aren't free metadata: `lf.select(pl.len()).collect().item()` is
  a real (if cheap) computation.
- `pyarrow.parquet.ParquetFile(path).metadata` gives per-column-chunk detail;
  summing `.total_compressed_size` across row groups shows which columns
  dominate file size. When a file "feels too big", break it down by column
  group first; a few wide, repetitive groups often account for most of it.

### Comparing frames in tests
- `LazyFrame == LazyFrame` isn't allowed (plans, not data).
  `DataFrame == DataFrame` gives a frame of bools, so `assert` on it raises
  "truth value is ambiguous".
- Use `polars.testing.assert_frame_equal(actual, expected)`: one pass/fail, a
  clear diff, nulls in the same place count as equal, and dtypes are checked
  (`check_dtypes=False` to skip, but usually you want it).
- When building test frames, `schema=` must name *every* column;
  `schema_overrides=` sets only the ones listed. `10.0` gives Float64 without
  either. Make test input dtypes match the real data.

### Reading SPSS with pyreadstat
- `pyreadstat.read_file_in_chunks(read_sav, path, chunksize=..., limit=...,
  **kwargs)` is a generator of `(df, meta)` chunks; extra keyword arguments
  pass through to `read_sav`. `limit=` stops early for quick test runs.
- `meta` describes the whole file (labels, missing ranges, column names), so
  it's the same for every chunk. `read_sav(path, metadataonly=True)` reads
  only that, cheaply.
- `meta.readstat_variable_types` maps column → `"double"` / `"string"`: the
  intended type, regardless of what's in a given slice.
- `multiprocess=True` splits each chunk *again* across workers and stacks
  the pieces back together. On sparse columns, tiny pieces come back
  all-null and the stacking fails, and the crash happens before your code
  ever sees the chunk.
- `apply_value_formats=True` replaces codes with their labels (numbers
  become text categories). Not wanted when your own code needs the raw
  codes (e.g. to separate missing codes from real values).
- Parallelising safely means one *whole* chunk per worker
  (`read_sav(row_offset=..., row_limit=...)` → cast → transform → write its
  own part), so nothing is ever stacked. `ProcessPoolExecutor` needs the
  worker function at module level, and memory scales with the number of
  workers. (Discussed, not built.)

## 7. Jupyter / IPython

- IPython is the interactive shell Jupyter's kernel is built on (rich output,
  tab completion, magics).
- A cell auto-displays only the value of its last top-level statement, and
  only if it's a bare expression. Objects created inside a `for` loop are
  never displayed.
- `IPython.display.display(obj)` triggers that rich rendering manually,
  anywhere and any number of times (e.g. inside a loop).

## 8. Tooling

### uv
- `uv run <program>` runs it in the project environment: `uv run pytest`,
  `uv run python -m pkg.module`.
- `uv add`/`uv remove` update `pyproject.toml`, `uv.lock` and `.venv`
  together; hand-editing the toml leaves them out of sync until `uv sync`
  (and leftover comments need deleting by hand).
- `[project.optional-dependencies]` extras only install when requested
  (`--extra dev`), so a sync can silently uninstall dev tools.
  `[dependency-groups] dev` installs by default.
- `.python-version` pins the interpreter (`uv python pin 3.12`); without it
  uv may pick its own downloaded Python.
- Virtual environments store absolute paths: after moving a project,
  recreate `.venv` (`uv sync`) and open new terminals (old ones show a stale
  `VIRTUAL_ENV` warning).

### VS Code
- `.vscode/settings.json` only applies from the folder that's open, so a
  nested project doesn't get its settings.
- F2 (Rename Symbol) renames by meaning, respecting scope and updating
  imports across files (skips comments/strings); Shift+Enter previews.
  Shift+F12 finds all references.

### Git / GitHub
- `git add` stages (silent on success; check with `git status`), `git commit`
  records. Splitting them lets you choose exactly what goes in a commit.
- Contributing via PR: fork → clone *your fork* → branch → commit → push to
  `origin` (your fork), not `upstream` → open the PR from your fork's branch
  against `upstream`'s main.
