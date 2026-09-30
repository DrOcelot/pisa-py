# Learning log

Concepts covered while reading through `src/pisa_py/io.py`.

## `pathlib.Path`
- Object-oriented filesystem paths; `Path(...)` doesn't touch disk on its own.
- `/` joins path segments (`Path.__truediv__`, operator overloading — not division).
- `Path(__file__)` is the path to the current module's own file.
- `.parent` / `.parents[n]` walk up the directory tree; `.parents[0] == .parent`.
- `.resolve()` makes a path absolute.
- `.exists()`, `.mkdir(parents=True, exist_ok=True)` for filesystem checks/setup.

## Strings and comments
- `"""..."""` is a real string literal, not a comment. In docstring position
  (first statement of a module/function/class) it becomes `.__doc__`.
- `#` is a true comment, discarded by the parser, never exists at runtime.
- `.strip()` removes whitespace from both ends; `.lstrip(char)` removes a
  specific character from the left only (e.g. a UTF-8 BOM, `"﻿"`).

## `dict` and unpacking
- `dict.fromkeys(iterable)` builds a dict with each element as a key
  (value `None`) — dedupes because dict keys are unique, and preserves
  insertion order (Python 3.7+).
- `*x` inside a list literal (`[*x, *y]`) unpacks/spreads `x`'s elements in
  place, rather than nesting `x` as a single item — same idea as JS `...`.
- Pattern used repeatedly in this file: `list(dict.fromkeys([*a, *b, ...]))`
  = concatenate several lists, then dedupe while keeping order.

## List comprehensions
- Shape: `[<expression> for <item> in <iterable> if <condition>]`.
- The leading expression and the loop variable are separate things — the
  expression can be anything, not just the bare loop variable.

## The walrus operator `:=`
- Assigns and evaluates to that value in one expression, e.g.
  `if missing := [...]:` assigns `missing` and uses it as the condition,
  so it's still available inside the `if` block. Python 3.8+.

## Conditional (ternary) expression
- `value_if_true if condition else value_if_false` — an expression, not a
  statement. Equivalent in spirit to JS's `condition ? a : b`, reordered
  to read like a sentence.

## Exceptions
- `raise SomeError(...)` immediately aborts normal execution and propagates
  up the call stack — not a console print, a real interruption (unless
  caught by `try`/`except`).
- `KeyError` conventionally means "lookup not found"; reused here for
  "requested column missing" even without a literal dict lookup.

## Polars-specific
- Expressions (`pl.col(...)`) are lazy — they describe a plan, and only run
  when passed to something that executes it (e.g. `.filter()`, `.collect()`).
- Namespace accessors like `.str` (also `.dt`, `.list`) group type-specific
  operations on an expression/column — not a type cast.
- `.filter(...)` uses a boolean mask (one bool per row) to select rows;
  the mask isn't stored as a column.
- `pl.scan_parquet(...)` returns a `LazyFrame` — a plan over the file,
  not loaded data. Lets column selection get pushed down to the reader.
- `.sink_parquet(...)` executes a lazy plan and streams the result straight
  to disk, without materializing the full result in memory first.
- Row counts aren't free metadata like column names are — getting them
  (`.select(pl.len()).collect().item()`) is a real, if cheap, computation.

## `set`
- `set` as a noun: an unordered, duplicate-free collection type, built for
  fast (~O(1)) membership testing (`x in a_set`), unlike `list` (O(n)).

## `zip`
- Pairs up multiple iterables element-by-element into tuples; lazy, usually
  wrapped in `list(...)` or fed into `dict(...)`.
- `strict=True` (3.10+) raises if the iterables have mismatched lengths,
  instead of silently truncating.

## Method chaining
- `.method().method()` reads similarly to R's `|>`/`%>%` pipelines, but the
  mechanism differs — each `.method()` is a call defined on that object's
  class, not syntactic rewriting.

## Concepts covered while reading `src/pisa_py/features.py`

### f-strings
- `f"..."` evaluates any `{expr}` inside as real Python and stringifies the
  result; without the `f` prefix, `"{expr}"` is just a literal 9-character
  string, no evaluation at all.

### Expressions vs LazyFrames
- `pl.col(...)`, `pl.lit(...)`, `pl.when(...)`, `pl.mean_horizontal(...)` all
  return an **expression** (`pl.Expr`) — a plan for one column's worth of
  computation, not data and not a frame. It can't be `.collect()`-ed on its
  own; it only means something once passed into a frame method.
- Heuristic for telling expression vs. frame apart while reading: frame
  methods are table-shaped (`.filter()`, `.select()`, `.with_columns()`,
  `.group_by()`, `.join()`, `.drop()`); expression methods are column-shaped
  (`.cast()`, `.alias()`, `.is_null()`, `.qcut()`, `.over()`). Anything passed
  *as an argument into* a frame method is an expression.
- `.with_columns(expr.alias("name"))` returns a new frame with that column
  added (or overwritten if the name already exists) — everything else in the
  frame passes through unchanged.

### `.over(group)`
- Like SQL's `OVER (PARTITION BY ...)`. Wraps *everything to its left in the
  chain* and re-evaluates that expression separately within each group,
  mapping results back to the original rows — it does not run "backwards" or
  out of order, chaining is still strictly left-to-right, `.over()` just
  changes the grouping context of what preceded it rather than transforming
  a value like most chained calls do.
- Placement matters: `pl.col("x").qcut(10, ...).over(g)` computes qcut
  per-group; `pl.col("x").over(g).qcut(10, ...)` would (for a plain column
  ref) leave qcut running globally, since `.over()` only wraps `pl.col("x")`.

### `pl.when` / `pl.lit` / `pl.concat_str`
- `pl.when(cond).then(val).when(cond2).then(val2).otherwise(default)` is
  Polars' row-wise if/elif/else.
- `pl.lit(x)` inserts a constant value into an expression (as opposed to
  reading a column).
- `pl.concat_str(expr1, expr2, ...)` glues string expressions together
  row-wise.

### `.qcut(n, labels=[...])`
- "Quantile cut" — splits a numeric column into `n` equal-sized buckets by
  value and assigns each row the matching label (lowest values get the first
  label, etc).

### `group_by` / `.agg`
- `frame.group_by([...])` alone does not return a LazyFrame — it returns an
  intermediate `LazyGroupBy` object, conceptually "piles of rows" bucketed by
  unique combinations of the group-by columns. Ragged/variable pile sizes
  exist only transiently here; it can't be visualized as a frame because a
  frame requires every column to line up row for row.
- `.agg(...)` is what turns those piles back into a proper rectangular
  table: it asks each pile a question that *reduces* it down to one row
  (`pl.len()` for row count, `.mean()`, `.sum()`, `.min()`/`.max()`,
  `.n_unique()`, `.first()`, or a bare `pl.col(...)` with no reducer to get a
  list-typed cell holding the whole pile). A list of expressions can be
  passed to compute several aggregates over the same groups at once.
- `pl.len()` is row count (like SQL `COUNT(*)`), not the length of a
  specific column.

### `.collect()` and return-type conventions in this file
- Functions that stay lazy (return `pl.LazyFrame`) are meant to be chained
  further by the caller; a function that calls `.collect()` and returns
  `pl.DataFrame` is written as a pipeline *endpoint* — actual numbers, not a
  plan to extend. `.collect()` is also where Polars' query optimizer decides
  the efficient execution plan (e.g. avoiding materializing columns that end
  up dropped later), matching the earlier `sink_parquet` lesson from `io.py`.

## Jupyter/IPython display
- A cell only auto-displays the value of its last top-level statement, and
  only if that statement is a bare expression. A `for` loop is a statement,
  not an expression — it has no value to display, so plot objects created
  inside a loop body are silently discarded, not just the last one.
- `IPython` is the interactive shell Jupyter's kernel is built on; it adds
  rich output rendering, tab completion, magics, etc. on top of plain Python.
- `IPython.display.display(obj)` manually triggers the same rich-rendering
  Jupyter does automatically for a cell's last expression — usable anywhere,
  any number of times, e.g. inside a loop: `display(plot_factor(...))`.

## `repr()` vs `print()`/`str()`
- `repr()` gives the unambiguous, "developer-facing" representation of a
  value, showing things `str()`/`print()` hide — e.g. quote boundaries, so
  `repr("Germany ")` reveals the trailing space as `'Germany '` where
  `print("Germany ")` would just show `Germany `.

## Debugging a blank/empty result
- Work outward from the smallest suspect piece rather than guessing: check
  the raw filter alone before blaming a wrapper function, `repr()` a value
  before assuming a string mismatch, and check upstream data
  (`is_not_null()` on the specific column) before assuming the plotting
  code is wrong. Sometimes the "bug" is a genuine gap in the source data
  (e.g. a survey question not asked in a particular country).

## Polars `group_by` / percentage-within-group pattern
- `frame.group_by([key, group]).agg(pl.len().alias("n"))` counts rows per
  combination of `key` and `group`.
- `.with_columns((pl.col("n") / pl.col("n").sum().over(group) * 100).alias("pct"))`
  turns those counts into percentages *within* each `group` (`.over(...)`
  computes the denominator per group without collapsing rows) — needed
  whenever groups (e.g. countries) have different total respondent counts,
  so raw counts alone aren't comparable.
- `pl.count()` is deprecated in favour of `pl.len()`.

## Concepts covered while reading `src/pisa_py/build_parquet.py`

### Eager vs lazy conversion
- `pl.from_dataframe(pandas_df)` / `pl.LazyFrame(pandas_df)` isn't always
  zero-copy — if even one column has an incompatible memory layout (e.g. a
  pandas `object`/string column mixed among float64 columns), Polars falls
  back to copying the *entire* frame, not just the incompatible columns.
- Wrapping an already-fully-loaded pandas DataFrame in `pl.LazyFrame(...)`
  doesn't make the underlying data lazy — laziness only covers operations
  from that point forward; the source is already fully materialized. A
  genuine lazy *source* (e.g. `scan_parquet`, or a purpose-built file
  scanner) is a different thing from lazily wrapping already-eager data.

### `Expr.replace_strict()`
- The current Polars way to map values through a dict (pandas' `.map(dict)`
  equivalent); plain `.replace()`'s implicit-dtype behavior and the older
  `map_dict` are both deprecated/being phased out.
- `default=` controls what happens for values not found in the mapping;
  `return_dtype=` fixes the output type explicitly when branches would
  otherwise produce mismatched types (e.g. raw numbers vs. category labels).

### `pl.when/then/otherwise` composing with other expressions
- `.then()`/`.otherwise()` accept any expression, not just literals — a
  whole `pl.col(...).replace_strict(...)` chain can sit inside a branch,
  mirroring `np.where(cond, a, b)`'s three-part shape.
- Multiple expressions passed to the *same* `.with_columns(expr1, expr2, ...)`
  call are evaluated independently against the same input frame — they
  don't see each other's output, so argument order doesn't affect
  correctness, only column order in the result.

### `pl.Enum` vs `pl.Categorical` vs plain `Utf8`/`String`
- A plain string column stores full text per row, repeated — for a column
  with a small fixed set of repeated values (e.g. a handful of survey
  labels repeated across hundreds of thousands of rows), this can cost
  3-4x more memory than a compact/dictionary-style encoding.
- `pl.Enum(categories)` needs a *unique* list of category values —
  `list(dict.fromkeys(values))` dedupes while preserving order, reusing the
  dedup trick from `io.py`. The dedup only applies to the category
  vocabulary; the original mapping dict (which may have several keys
  sharing one label) is untouched and still works correctly.
- Mixing dtypes across `when/then/otherwise` branches (e.g. a numeric
  fallback vs. an Enum-typed match) forces Polars to reconcile types —
  sometimes via an implicit, deprecated cast. Choosing `default=`/
  `return_dtype=` conditionally per-branch, matching the actual shape of
  the data, avoids the deprecated path entirely rather than just
  suppressing the warning.

### Chained vs batched `.with_columns()`
- Calling `.with_columns()` once per column inside a loop builds a much
  deeper query plan than collecting all the expressions into one list and
  calling `.with_columns(*all_exprs)` a single time — measurably slower and
  more memory-hungry at scale, even though both are logically equivalent.

### `sink_parquet()` and its `engine=` parameter
- `sink_parquet` doesn't automatically guarantee streaming execution — its
  `engine="auto"` default can silently pick the in-memory engine,
  materializing the whole result before writing anything, which shows up as
  "no disk writes at all until near the end" on a live resource monitor.
- Forcing `engine="streaming"` explicitly doesn't guarantee every operation
  in a query plan actually streams either — a feature can still add far
  more memory overhead than expected even under a genuinely-streaming
  engine, if its own implementation isn't optimized for the shape of data
  involved (e.g. an unusually wide, many-column schema).

### Debugging a memory crash methodically
- "Runs without error" isn't the same as "correct" or "efficient" — check
  actual dtypes and values (e.g. via a data viewer), not just the absence
  of an exception. The eventual root cause this session was exactly this:
  code that ran fine and produced correct values for months, just with a
  quietly wasteful dtype nobody had checked.
- Isolate variables one at a time (row batching vs. column batching,
  chained vs. batched calls, engine choice, individual library features)
  using synthetic data at matching scale, rather than changing several
  things at once and guessing which one mattered.
- A library's own benchmark claims (e.g. "under 1GB RAM for 500GB files")
  may be measured on a much simpler case than your own — don't assume it
  transfers without checking against your specific shape of data.

### Git / GitHub pull request workflow
- Fork → clone the fork (not the original repo) → create a branch → commit
  → push to `origin` (your fork), not `upstream` (the original repo) →
  open the PR from your fork's branch targeting `upstream`'s main branch.
- `git add` stages a change (silent on success — check with `git status`,
  not the absence of output); `git commit` is the separate step that
  actually records it. Splitting them lets you choose exactly what goes
  into a commit.
- A PR description carries the *why*; a code comment isn't needed when the
  diff itself is self-explanatory (e.g. a one-line consistency fix
  mirroring an existing pattern elsewhere in the same file).

## Concepts covered while writing `src/pisa_py/make.py`

### `LazyFrame.collect_schema().names()` for existence checks
- Same method used in `build_parquet.py`'s for-loop, reused here for a
  different purpose: check whether a *derived* column name
  (`f"{col}_missing_reason"`) actually exists in the file before trying to
  `.select()` it, rather than hardcoding which source columns happen to
  have missing-reason siblings (e.g. ID columns like `CNT` never do).
  Computing this from the real schema means the logic keeps working if the
  underlying data file changes, instead of silently going stale.

### List concatenation vs. plain addition
- `some_list + f"{x}"` raises `TypeError: can only concatenate list (not
  "str") to list` — `+` between a list and anything else requires both
  sides to be lists. Wrapping the single item in brackets
  (`some_list + [f"{x}"]`) makes it a one-element list, which concatenates
  fine. `list.append(x)` is the other option, but mutates in place instead
  of producing a new list.

### Name binding vs. copying for lists
- `schcols = SCHOOL_COLS` does not copy the list — `schcols` and the
  module-level `SCHOOL_COLS` point at the *same* list object. `schcols =
  schcols + [...]` doesn't mutate that shared object though: `+` builds a
  brand new list and rebinds the name `schcols` to it, leaving the original
  `SCHOOL_COLS` untouched. (`.append()` would have mutated the shared
  object in place instead — worth knowing which one a given pattern does.)
- Mutating the name bound inside a `for col in stucols:` loop (via
  reassignment, not in-place mutation) doesn't break the loop or cause
  infinite iteration — the loop's iterator was already created over the
  original list object when the loop started; rebinding the name `stucols`
  partway through doesn't change what the iterator walks.

### Deriving one rename dict from another
- Pattern: give the raw→friendly rename dict a variable name
  (`rename_map = {...}`) instead of writing it as an inline literal, so it
  can be read back later. Then loop over the columns being selected, and
  for any raw name that both (a) has a `_missing_reason` sibling in the
  schema and (b) already has an entry in `rename_map`, add a matching
  `f"{raw}_missing_reason": f"{friendly}_missing_reason"` entry via
  `rename_map.update(...)`. Keeps the derived columns' names in sync with
  their base column's friendly name without typing every pair by hand.

### Inspecting a parquet file's per-column size
- `pyarrow.parquet.ParquetFile(path).metadata` exposes row-group/column
  detail that plain `polars` schema/row-count calls don't — each column
  chunk's `.total_compressed_size` can be summed across row groups to see
  which columns actually dominate a file's size on disk.
- Applied here: in a 160MB export, the 80 replicate-weight columns
  (`W_FSTURWT*`) alone accounted for ~96MB (60%) — more than the 30
  plausible-value columns and far more than the handful of demographic
  columns and their `_missing_reason` siblings (~0.4MB total) combined.
  A file "feeling too big" is worth breaking down by column group before
  assuming something's wrong — sometimes it's just that a few wide,
  boilerplate column groups (replicate weights, here) genuinely dominate.
