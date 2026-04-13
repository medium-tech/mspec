# Final Production Sprint Plan — sosh-net

**Base branch:** `improve-sosh-net-ui`
**All PRs from/to:** `improve-sosh-net-ui`

This document is the index for the final production sprint tickets for sosh-net. Each ticket is in a separate file in this directory.

---

## Tickets

| # | Title | File | Depends On |
|---|-------|------|------------|
| 01 | `max_models_by_field` auth constraint + `unique` field constraint | [TICKET_01_max_models_by_field.md](TICKET_01_max_models_by_field.md) | — |
| 02 | `db.read` and `db.unique_counts` lingo functions | [TICKET_02_db_lingo_functions.md](TICKET_02_db_lingo_functions.md) | — |
| 03 | `sosh_net.get_post_and_reactions` backend op | [TICKET_03_get_post_and_reactions_op.md](TICKET_03_get_post_and_reactions_op.md) | 02 |
| 04 | Custom Profiles page (list + create/edit for current user via `get_current_user_profile`) | [TICKET_04_profiles_page.md](TICKET_04_profiles_page.md) | 01, 02 |
| 05 | Account page: keep generic, no profile coupling | [TICKET_05_account_page_profile.md](TICKET_05_account_page_profile.md) | 04 |
| 06 | Custom Forum instance page | [TICKET_06_forum_instance_page.md](TICKET_06_forum_instance_page.md) | 02, 03 |
| 07 | Custom Chatter page | [TICKET_07_chatter_page.md](TICKET_07_chatter_page.md) | 02, 03, 06 |
| 08 | Responsive CSS: mobile and desktop support | [TICKET_08_responsive_css.md](TICKET_08_responsive_css.md) | — |

---

## Feature Areas

### Model Spec (Ticket 01)

Two new model-level constraints:

- **`max_models_by_field`** — limits the number of models a user can create where a specific field has the same value. Used by `sosh_net.reaction` to enforce "one reaction per user per post":
  ```yaml
  reaction:
    auth:
      require_login: true
      max_models_by_field:
        post_id: 1
  ```
- **`unique`** field attribute — adds a `UNIQUE` constraint to the DB column, used by `profile.username`:
  ```yaml
  username:
    type: str
    unique: true
  ```

### Backend Lingo Functions (Ticket 02)

New `db.*` functions in the Python lingo interpreter:

- **`db.read`** — fetch a single model instance by ID and model type
- **`db.unique_counts`** — return a grouped count of unique values for a model field, with optional filters

### Backend Op (Ticket 03)

- **`sosh_net.get_post_and_reactions`** — already defined in `sosh-net.yaml`; returns a post and its reaction type counts. Requires Ticket 02.

### Custom Pages (Tickets 04–08)

| Page | URL | Purpose |
|------|-----|---------|
| Profiles | `/sosh-net/profile` | Public list + create/edit own profile (via `get_current_user_profile` op) |
| Account | `/sosh-net/account` | Auth only (login, logout, register, current-user) — no profile coupling |
| Forum instance | `/sosh-net/forum/<id>` | Forum metadata, pageable posts, nested replies, add post/reply |
| Chatter | `/sosh-net/chatter` | Open feed of non-forum posts, newest first, nested replies |
| All pages | — | Responsive CSS: mobile and desktop breakpoints |

---

## Recommended Implementation Order

1. **Ticket 01** — Model spec constraints (no dependencies; unblocks the account page and data integrity)
2. **Ticket 02** — DB lingo functions (no dependencies; unblocks the op and all custom pages)
3. **Ticket 08** — Responsive CSS (no dependencies; can be done in parallel with 01/02)
4. **Ticket 03** — Backend op (depends on 02)
5. **Ticket 04** — Profiles page: fix `get_current_user_profile` op + rewrite page with create/edit branch (depends on 01, 02)
6. **Ticket 05** — Account page cleanup: remove any profile coupling, add profile link (depends on 04)
7. **Ticket 06** — Forum instance page (depends on 02, 03)
8. **Ticket 07** — Chatter page (depends on 02, 03, 06 for shared patterns)
