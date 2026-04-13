# Ticket 02 — Implement `db.read`, `db.unique_counts`, and `db.query` Lingo Functions

**Branch:** `improve-sosh-net-ui`

## Overview

Add three new database lingo functions to the Python lingo interpreter:

- `db.read` — fetch a single model instance by ID
- `db.unique_counts` — return counts of unique values for a given model field, with optional filters
- `db.query` — return all rows matching a set of field equality filters (supports `str` and `foreign_key` fields only)

`db.read` and `db.unique_counts` are required by the `sosh_net.get_post_and_reactions` op (Ticket 03). `db.query` is required by `get_current_user_profile` on the profiles page (Ticket 04).

## Background

The updated `sosh-net.yaml` defines two ops that use these functions:

```yaml
get_post_and_reactions:
  func:
    type: struct
    value:
      post:
        call: 'db.read'
        args:
          model_id:
            params: {post_id: {}}
          model_type: 'sosh_net.post'
      reactions:
        call: 'db.unique_counts'
        args:
          model_type: 'sosh_net.reaction'
          group_by: 'reaction_type'
          filters:
            post_id:
              params: {post_id: {}}

get_current_user_profile:
  func:
    type: struct
    value:
      call: 'db.query'
      args:
        model_type: 'sosh_net.profile'
        fields:
          type: struct
          value:
            user_id:
              call: 'key'
              args:
                key: 'id'
                object:
                  call: 'auth.current_user'
                  args: {}
```

## Implementation

### `db.read`

Wrap `db_model_read` from `src/mapp/module/model/db.py`.

**Args:**
- `model_type: str` — dot-notation `module.model` (e.g. `sosh_net.post`)
- `model_id: str` — the record ID

**Returns:** the model as a struct dict (same format as existing read endpoint)

**Steps:**

1. **`src/mspec/lingo.py`** — Add a `db` function group to the `LINGO_BUILTIN_FUNCTIONS` dict:
   ```python
   'db': {
       'read': {'func': db_read, 'create_args': _db_read_function_args},
       'unique_counts': {'func': db_unique_counts, 'create_args': _db_unique_counts_function_args},
       'query': {'func': db_query, 'create_args': _db_query_function_args},
   }
   ```
1. Add argument builders (`_db_read_function_args`, `_db_unique_counts_function_args`) following the pattern of existing builders (e.g. `_current_user_function_args`)
1. May need a new `db_model_read_by_type` helper that accepts a `model_type` string (e.g. `'sosh_net.post'`) and calls `db_model_read`. The argument builders have access to the function defintions in `app.spec` which has the model definitions and can lookup the `model_type`, from the args for `db_model_read` can be created w/ functions/classes in `src/mapp/types.py`.

### `db.unique_counts`

Execute a `SELECT {group_by}, COUNT(*) FROM {model_snake_case} WHERE ...` query.

**Args:**
- `model_type: str` — dot-notation `module.model`
- `group_by: str` — field name to group by
- `filters: dict` (optional) — `{field_name: value}` pairs for WHERE clause

**Returns:** list of structs `[{group_by_field: value, count: int}, ...]`

**Steps:**

1. **`src/mapp/module/model/db.py`** — Add `db_model_unique_counts(ctx, model_class, group_by, filters)` that runs the GROUP BY query and returns a list of dicts
2. **`src/mspec/lingo.py`** — Wire up args builder and register in the `db` function group

### `db.query`

Execute a `SELECT * FROM {table} WHERE field1 = val1 AND field2 = val2 ...` query. Only `str` and `foreign_key` field types are supported in the initial implementation; other field types must raise a clear error at call time.

**Args:**
- `model_type: str` — dot-notation `module.model` (e.g. `sosh_net.profile`)
- `fields: dict` — `{field_name: value}` pairs; each key must correspond to a `str` or `foreign_key` field on the model

**Returns:** list of matching model structs (same format as items returned by `db_model_list`)

**Steps:**

1. **`src/mapp/module/model/db.py`** — Add `db_model_query(ctx, model_class, fields)`:
   - Validates that each key in `fields` is a `str` or `foreign_key` column on `model_class`; raises `ValueError` for any unsupported field type
   - Builds a `WHERE` clause with `AND`-joined equality conditions
   - Returns all matching rows as a list of dicts (consistent with `db_model_list` item format)
1. **`src/mspec/lingo.py`** — Add arg builder `_db_query_function_args` and register `'query': {'func': db_query, 'create_args': _db_query_function_args}` in the `db` function group
1. The argument builders have access to the function defintions in `app.spec` which has the model definitions

**Scope limitation:** Only `str` and `foreign_key` fields are supported. Filtering on `int`, `float`, `bool`, or `list` fields is out of scope for this ticket and should raise a `ValueError` with a descriptive message.


## Tests

- Add a lingo page/script test in `src/mspec/data/lingo/` that exercises `db.read`, `db.unique_counts`, and `db.query`
- `db.query` — unit tests should cover:
  - Returns matching rows when filtering by a `str` field
  - Returns matching rows when filtering by a `foreign_key` field
  - Returns an empty list when no rows match
  - Returns multiple matching rows (e.g. all posts by a given `user_id`)
  - Raises `ValueError` when a filter key is an unsupported field type (e.g. `int`, `bool`)
- Run existing lingo tests to ensure no regressions: `python -m pytest tests/test_lingo.py`
- Add integration test in `src/mapp/test.py` or a new test file for the new DB functions

## Documentation

- Update `docs/LINGO_FUNCTIONS.md` — add a new `### Database Functions` section:
  ```
  db.read - Read a single model by ID
    args: model_type (str), model_id (str)
    return: struct

  db.unique_counts - Return unique value counts for a model field
    args: model_type (str), group_by (str), filters (struct, optional)
    return: list of structs [{<group_by_field>: value, count: int}]

  db.query - Return all rows matching field equality filters (str and foreign_key fields only)
    args: model_type (str), fields (struct: {field_name: value})
    return: list of structs
    note: raises ValueError if any filter field is not a str or foreign_key type
  ```

## References

- `src/mapp/module/model/db.py` — `db_model_read`, `db_model_list`
- `src/mspec/lingo.py` — existing auth/file_system/media function implementations
- `src/mapp/module/op/run.py` — how lingo is executed for ops
