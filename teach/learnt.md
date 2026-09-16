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
