# Ticket 02 — Implement `db.read` and `db.unique_counts` Lingo Functions

**Branch:** `improve-sosh-net-ui`

## Overview

Add two new database lingo functions to the Python lingo interpreter:

- `db.read` — fetch a single model instance by ID
- `db.unique_counts` — return counts of unique values for a given model field, with optional filters

These are required to implement the `sosh_net.get_post_and_reactions` op (see Ticket 03).

## Background

The updated `sosh-net.yaml` defines the op:

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
```

## Implementation

### `db.read`

Wrap `db_model_read` from `src/mapp/module/model/db.py`.

**Args:**
- `model_type: str` — dot-notation `module.model` (e.g. `sosh_net.post`)
- `model_id: str` — the record ID

**Returns:** the model as a struct dict (same format as existing read endpoint)

**Steps:**

1. **`src/mspec/lingo.py`** — Add a new `db_model_read_by_type` helper that accepts a `model_type` string (e.g. `'sosh_net.post'`) and calls `db_model_read`
2. **`src/mspec/lingo.py`** — Add a `db` function group to the `LINGO_BUILTIN_FUNCTIONS` dict:
   ```python
   'db': {
       'read': {'func': db_read, 'create_args': _db_read_function_args},
       'unique_counts': {'func': db_unique_counts, 'create_args': _db_unique_counts_function_args},
   }
   ```
3. Add argument builders (`_db_read_function_args`, `_db_unique_counts_function_args`) following the pattern of existing builders (e.g. `_current_user_function_args`)
4. The lingo functions must receive the `MappContext` (passed as `ctx` in `lingo_execute`) to access the DB and model registry

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

### Model registry access

The lingo interpreter needs access to the running server's model class registry to resolve `model_type` strings like `'sosh_net.post'`. Options:
- Pass the registry via the `LingoApp` or `ctx` parameter
- Access via the `MappContext` which is available in all lingo function calls

## Tests

- Add a lingo page/script test in `src/mspec/data/lingo/` that exercises `db.read` and `db.unique_counts`
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
  ```

## References

- `src/mapp/module/model/db.py` — `db_model_read`, `db_model_list`
- `src/mspec/lingo.py` — existing auth/file_system/media function implementations
- `src/mapp/module/op/run.py` — how lingo is executed for ops
