# Ticket 07 — Custom Chatter Page

**Branch:** `improve-sosh-net-ui`

## Overview

Create a custom lingo page for **chatter** — posts not tied to any forum (`forum_id = -1`). The chatter page should feel distinct from the forum instance page (Ticket 06): it represents an open stream of conversation rather than a topic-organised forum, but it still supports nested replies.

## Background

The `post` model uses `forum_id`:
- `forum_id = -1` → the post is **chatter** (not tied to a forum)
- `forum_id = <id>` → the post belongs to a specific forum

Chatter posts can still have replies via `reply_to`. The chatter page should:
1. Show a paginated, reverse-chronological stream of top-level chatter posts (`forum_id = -1` AND `reply_to = -1`)
2. Allow expanding a post to view and page through its replies (nested, hardcoded to 3–4 levels)
3. Provide an inline form to create a new chatter post
4. Provide inline reply forms under each post

The UI should feel more like a social feed than a structured forum — consider a card-based or stream layout rather than a table.

## Implementation

1. **`src/mspec/data/lingo/pages/sosh-chatter.yaml`** — New page file:

   ```yaml
   lingo:
     version: page-beta-1
     title: 'sosh net :: chatter'

   params:
     page:
       type: int
       default: 0

   state:
     posts:
       type: struct
       calc:
         call: db.list_filtered
         args:
           model_type: 'sosh_net.post'
           filters:
             forum_id: '-1'
             reply_to: '-1'
           offset:
             call: mul
             args:
               a: {params: {page: {}}}
               b: 20
           size: 20
           order: desc   # most recent first

   output:
     - heading: 'sosh net'
       level: 1
     - heading: ':: chatter'
       level: 2
     - breadcrumbs: [home, sosh-net, chatter]
     - add-post form (collapsed by default, expand on click)
     - break: 1
     - for each post in state.posts:
         - post card: username (linked to profile), message, timestamp, reaction counts
         - expand/collapse replies (3 levels deep, same pattern as forum instance)
         - reply form (inline, collapsed by default)
     - pagination: prev/next
   ```

2. **`src/mspec/data/generator/sosh-net.yaml`** — Add a `chatter` page reference in the `sosh_net` module (e.g. under `pages: chatter: 'sosh-chatter.yaml'`) and add a link to it in the sosh-net navigation page

3. **Navigation** — Update `src/mspec/data/lingo/pages/sosh-network-page.yaml` to add a `chatter` link in the nav block

4. **Reaction display** — Each post card should display reaction counts. This requires calling `get_post_and_reactions` (Ticket 03) or a lightweight reaction count endpoint per post. Consider a `db.unique_counts`-based state entry per post or a batch approach.

5. **Ordering** — Chatter should default to newest-first. If `db.list_filtered` does not support ordering yet, extend it (or add a `db.list_ordered` variant) as part of this ticket or Ticket 02.

## Key Differences from Forum Instance Page

| Feature | Forum Instance | Chatter |
|---|---|---|
| Context | Single forum, topic-organised | Open stream, no topic |
| Layout | Table of posts | Card/feed layout |
| Filter | `forum_id = <id>` | `forum_id = -1` |
| Order | Ascending (thread-like) | Descending (newest first) |
| Create form | Add post to forum | Add freeform post |
| Header | Forum topic/description | "Chatter" heading only |

## Tests

- Playwright tests (`templates/sosh-net/tests/`):
  - Navigate to `/sosh-net/chatter`
  - Verify post stream is visible and paginated
  - Submit a new chatter post and verify it appears at the top of the stream
  - Expand a post to show replies; submit a reply; verify it appears
  - Expand a nested reply (level 2); verify it renders correctly
- Verify that posts with `forum_id != -1` do NOT appear in chatter

## Documentation

- Add `sosh-chatter.yaml` inline comments
- Document the chatter concept (vs forum) in a sosh-net usage document or README
- Update `docs/LINGO_FUNCTIONS.md` if any new lingo functions are added for ordering/filtering

## References

- `src/mspec/data/lingo/pages/sosh-network-page.yaml` — add chatter link
- `src/mspec/data/generator/sosh-net.yaml` — post model (`forum_id`, `reply_to`)
- Ticket 02 — `db.read`, `db.unique_counts`, `db.list_filtered`
- Ticket 03 — `get_post_and_reactions` op (for reaction counts on post cards)
- Ticket 06 — Forum instance page (similar nested reply pattern)
