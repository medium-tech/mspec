# Ticket 03 — Implement `sosh_net.get_post_and_reactions` Backend Op

**Branch:** `improve-sosh-net-ui`

## Overview

The `get_post_and_reactions` op is already fully specified in `sosh-net.yaml` on `improve-sosh-net-ui`. This ticket covers ensuring the lingo interpreter and the mapp server correctly execute it end-to-end once the `db.read` and `db.unique_counts` functions (Ticket 02) are available.

## Background

The op spec in `sosh-net.yaml`:

```yaml
ops:
  get_post_and_reactions:
    name:
      lower_case: 'get post and reactions'
    description: 'Get a post and its reactions by id'
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
    params:
      post_id:
        name:
          lower_case: 'post id'
        type: foreign_key
        references:
          module: 'sosh_net'
          table: 'post'
          field: 'id'
        examples:
          - "1"
          - "2"
          - "3"
    result:
      name:
        lower_case: 'get post result'
      type: struct
      value:
        post:
          type: struct
          value:
            id: int
            user_id: int
            forum_id: int
            reply_to: int
            message: str
            attachments: list
            web_images: list
            raw_images: list
            related_posts: list
        reactions:
          type: list
          element_type: struct
          value:
            reaction_type: str
            count: int
```

## Implementation

**Depends on Ticket 02** (`db.read` and `db.unique_counts`).

1. **`src/mapp/module/op/run.py`** — Ensure the lingo op runner passes the `MappContext` (including model registry) through to the `lingo_execute` call so that `db.read` and `db.unique_counts` can resolve model types
2. **`src/mspec/core.py`** — In `load_generator_spec`, validate and normalise `ops` definitions (params, result type shapes) if not already done
3. **`src/mapp/module/op/server.py`** — Verify that the op HTTP endpoint is registered and returns the correct JSON structure matching the `result` spec
4. **`src/mtemplate/core.py`** — If the mtemplate cache step processes ops, ensure `get_post_and_reactions` is handled; otherwise the op is registered dynamically at server start time

## Tests

- Write an integration test in `src/mapp/test.py` (or a dedicated test module) that:
  1. Seeds a post and several reactions of different types
  2. Calls `GET /api/sosh-net/get-post-and-reactions?post_id=<id>`
  3. Verifies the response contains the post fields and a `reactions` list with correct counts per `reaction_type`
- Test that a missing `post_id` param returns 400
- Test that an invalid `post_id` returns 404

## Documentation

- Add the op to any generated API documentation or OpenAPI spec (if applicable)
- Add a usage example to `docs/LINGO_MAPP_SPEC.md` under an "ops" section showing how `db.read` and `db.unique_counts` compose into a struct result

## References

- `src/mapp/module/op/run.py` — op callable creation
- `src/mapp/module/op/server.py` — HTTP op routes
- `src/mspec/data/generator/sosh-net.yaml` — full op definition on `improve-sosh-net-ui` branch
- Ticket 02 — `db.read` and `db.unique_counts`
