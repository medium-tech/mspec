# Ticket 06 — Custom Forum Instance Page

**Branch:** `improve-sosh-net-ui`

## Overview

Create a custom lingo page for viewing an individual forum. The page shows forum metadata, a paginated list of top-level posts in that forum, the ability to expand a post and page through its replies (hardcoded to 1 level deep), and forms to add a new post or reply.

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
5. Provide an inline form to add a new post to the forum
6. Provide an inline form to add a reply to a specific post

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

3. **Show replies** — Show replies to posts by expanding/collapsing driven by a per-post boolean in state.

## Tests

- Playwright tests (`templates/sosh-net/tests/`):
  - Navigate to a forum instance page
  - Verify forum topic/description are shown
  - Verify post list is visible and paginated
  - Expand a post to show replies
  - Submit the add-post form and verify the new post appears
  - Submit a reply form and verify the reply appears under the correct post

## Documentation

- Add `sosh-forum-instance.yaml` inline comments explaining the page structure
- Note the 1-level nesting limitation in any sosh-net user-facing documentation

## References

- `src/mspec/data/lingo/pages/` — existing page examples
- `src/mspec/data/generator/sosh-net.yaml` — forum and post model definitions
- Ticket 07 — Chatter page (similar pattern, different context)
