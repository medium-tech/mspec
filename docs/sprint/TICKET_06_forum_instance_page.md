# Ticket 06 — Custom Forum Instance Page

**Branch:** `improve-sosh-net-ui`

## Overview

Create a custom lingo page for viewing an individual forum. The page shows forum metadata, a paginated list of top-level posts in that forum, the ability to expand a post and page through its replies (hardcoded to a few levels deep), and forms to add a new post or reply.

The **forum list/index page** can use the built-in model page with pagination and create widget; only the **forum instance page** needs a custom implementation.

## Background

The `sosh_net` module has:
- `forum` model — `topic`, `description`, `tags`, `user_id`
- `post` model — `forum_id` (links post to a forum, or `-1` for chatter), `reply_to` (links reply to a post, or `-1`), `message`, `attachments`, `web_images`, `raw_images`, `related_posts`

A forum instance page should:
1. Show forum metadata (topic, description, tags)
2. Show a paginated list of top-level posts (`forum_id = <this_forum_id>` AND `reply_to = -1`)
3. Allow expanding a post to show replies (`reply_to = <post_id>`, first level)
4. Allow expanding a reply to show its replies (second level)
5. Support one or two more nested levels (hardcode the nesting depth to 3–4 levels max)
6. Provide an inline form to add a new post to the forum
7. Provide an inline form to add a reply to a specific post

## Implementation

1. **`src/mspec/data/lingo/pages/sosh-forum-instance.yaml`** — New page file:

   ```yaml
   lingo:
     version: page-beta-1
     title: 'sosh net :: forum'

   params:
     forum_id:
       type: int
     post_page:
       type: int
       default: 0

   state:
     forum:
       type: struct
       calc:
         call: db.read
         args:
           model_type: 'sosh_net.forum'
           model_id: {params: {forum_id: {}}}

     posts:
       type: struct
       calc:
         call: db.list_filtered     # new function — see notes
         args:
           model_type: 'sosh_net.post'
           filters:
             forum_id: {params: {forum_id: {}}}
             reply_to: '-1'
           offset: ...
           size: 10

   output:
     - forum metadata (topic, description, tags)
     - paginated post list
     - for each post: show message, expand/collapse replies (nested)
     - add-post form (wired to POST /api/sosh-net/post)
   ```

2. **`src/mspec/data/generator/sosh-net.yaml`** — Add `forum.page` (instance page) pointing to `sosh-forum-instance.yaml`

3. **Nested replies** — Hardcode UI to 3 levels deep using repeated lingo branch blocks. Each level loads replies using `db.list_filtered` with the parent post's ID. Expanding/collapsing is driven by a per-post boolean in state.

4. **New lingo function `db.list_filtered`** (or extend `db.read` / `db.unique_counts`):
   - Args: `model_type`, `filters` (dict), `offset`, `size`
   - Returns a `ModelListResult`-shaped struct (items list + total)
   - May be implemented in `src/mapp/module/model/db.py` and wired in `src/mspec/lingo.py`

   > **Note:** If `db.list_filtered` adds significant scope, it can be a sub-task of Ticket 02.

## Tests

- Playwright tests (`templates/sosh-net/tests/`):
  - Navigate to a forum instance page
  - Verify forum topic/description are shown
  - Verify post list is visible and paginated
  - Expand a post to show replies
  - Expand a reply to show nested replies (up to 3 levels)
  - Submit the add-post form and verify the new post appears
  - Submit a reply form and verify the reply appears under the correct post

## Documentation

- Add `sosh-forum-instance.yaml` inline comments explaining the page structure
- Document the `db.list_filtered` function in `docs/LINGO_FUNCTIONS.md`
- Note the 3-level nesting limitation in any sosh-net user-facing documentation

## References

- `src/mspec/data/lingo/pages/` — existing page examples
- `src/mspec/data/generator/sosh-net.yaml` — forum and post model definitions
- Ticket 02 — `db.read`, `db.unique_counts` (and potentially `db.list_filtered`)
- Ticket 07 — Chatter page (similar pattern, different context)
