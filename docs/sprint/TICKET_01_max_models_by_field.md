# Ticket 01 — Implement `max_models_by_field` Auth Constraint

**Branch:** `improve-sosh-net-ui`

## Overview

Implement `max_models_by_field` in the model auth spec, similar to `max_models_per_user`. This allows limiting the number of models a user can create where a specific field value is the same — e.g., "only 1 reaction per user per post".

Also implement the `unique` field-level constraint so that the DB enforces only one row with a given value per column (e.g., one `username` per profile table).

## Background

The updated `sosh-net.yaml` on `improve-sosh-net-ui` defines:

```yaml
reaction:
  auth:
    require_login: true
    max_models_by_field:
      post_id: 1  # only allow one reaction per user per post
```

And for profile:

```yaml
username:
  type: str
  unique: true
```

## Implementation

### `max_models_by_field`

1. **`src/mspec/core.py`** — In `load_generator_spec`, initialise `max_models_by_field` to `{}` in the auth block alongside `max_models_per_user`

1. **`src/mapp/module/model/db.py` — `db_model_create`** — After the existing `max_models_per_user` check, iterate `max_models_by_field`:
   ```python
   for field_name, max_count in model_spec['auth']['max_models_by_field'].items():
       if max_count >= 0:
           field_value = getattr(obj, field_name)
           count = ctx.db.cursor.execute(
               f'SELECT COUNT(*) FROM {model_snake_case} WHERE user_id = ? AND "{field_name}" = ?',
               (user['value']['id'], field_value)
           ).fetchone()[0]
           if count >= max_count:
               raise MappUserError('MAX_MODELS_BY_FIELD_EXCEEDED',
                   f'Maximum models ({max_count}) for field {field_name} exceeded.')
   ```

### `unique` field constraint

1. **`src/mapp/module/model/db.py` — `db_model_create_table`** — Append `UNIQUE` to the column definition string for any non-list field with `unique: true` in the field spec

## Tests

- Add a model to `src/mspec/data/generator/model-type-testing.yaml` with `max_models_by_field` set; verify a second model with the same field value returns HTTP 400
- Add a field with `unique: true` to the test yaml; verify duplicate values are rejected with a DB constraint error
- Update `src/mapp/test.py` to cover the `MAX_MODELS_BY_FIELD_EXCEEDED` error case (pattern: existing `max_models_per_user` test at line ~309)

## Documentation

- Update `docs/LINGO_MAPP_SPEC.md`:
  - Document `auth.max_models_by_field` under the auth section
  - Document the `unique` field attribute under the fields section

## References

- Existing `max_models_per_user` implementation: `src/mapp/module/model/db.py:107`
- `db_model_create_table` for unique constraint: `src/mapp/module/model/db.py:19`
- Spec loading: `src/mspec/core.py:376`
