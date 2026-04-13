# Ticket 04 — Custom Profiles Page (Pagination Only, No Create Widget)

**Branch:** `improve-sosh-net-ui`

## Overview

Update the sosh-net profiles page so it only shows the paginated list of profiles. The create-profile form should be removed from this page — users will create their profile from the account page (Ticket 05).

## Background

Currently `sosh-profile.yaml` (at `src/mspec/data/lingo/pages/sosh-profile.yaml`) is a minimal placeholder. The model page for `profile` may also show a create widget by default. We want:

- The **profiles model page** — shows pagination only (no create/edit form)
- The **account page** — is where users create/edit their profile (see Ticket 05)

## Implementation

1. **`src/mspec/data/lingo/pages/sosh-profile.yaml`** — Rewrite as a full page that:
   - Shows a heading and breadcrumbs for `sosh-net > profile`
   - Has a `state` entry that calls `db.list` (or the existing model list endpoint) to fetch profiles with pagination
   - Renders a paginated table of profiles (username, bio, profile picture)
   - Does **not** include an inline create/edit widget; links or buttons on each row can navigate to the profile instance page
   - Shows a pagination widget (prev/next page controls)

2. **`src/mspec/data/generator/sosh-net.yaml`** — Confirm (or update) the `profile.page` reference points to the updated `sosh-profile.yaml`

3. **Browser JS client** (`templates/mapp-py/` or the sosh-net front-end) — Ensure the profile page route uses the custom page YAML instead of the builtin model page

## Page Structure (YAML outline)

```yaml
lingo:
  version: page-beta-1
  title: 'sosh net :: profiles'

params:
  page:
    type: int
    default: 0

state:
  profiles:
    type: struct
    calc:
      call: db.list           # or equivalent API call
      args:
        model_type: 'sosh_net.profile'
        offset:
          call: mul
          args:
            a: {params: {page: {}}}
            b: 20
        size: 20

output:
  - heading: 'sosh net'
    level: 1
  - heading: ':: profiles'
    level: 2
  - breadcrumbs: [home, sosh-net, profiles]
  - break: 1
  - list display (table) of profiles from state.profiles
  - break: 1
  - pagination widget (prev/next using page param)
```

## Tests

- Playwright test (`templates/sosh-net/tests/`) — navigate to `/sosh-net/profile`, verify:
  - Profile list table is visible
  - No create/edit form is present on this page
  - Pagination controls are visible (if there are enough profiles)
  - Clicking a profile navigates to the instance page

## Documentation

- Update `src/mspec/data/lingo/pages/sosh-profile.yaml` inline comments to explain the page structure
- Note in `docs/LINGO_MAPP_SPEC.md` or a sosh-net usage doc that the profiles page is view-only; profile creation is on the account page

## References

- `src/mspec/data/lingo/pages/sosh-profile.yaml` — current placeholder
- `src/mspec/data/lingo/pages/sosh-network-page.yaml` — navigation links
- `src/mspec/data/lingo/pages/builtin-mapp-page-account.yaml` — account page for context
- Ticket 05 — Account page with profile create/edit
