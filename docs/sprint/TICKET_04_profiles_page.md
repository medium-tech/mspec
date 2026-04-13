# Ticket 04 — Custom Profiles Page (Pagination Only, No Create Widget)

**Branch:** `improve-sosh-net-ui`

## Overview

Update the sosh-net profiles page so it only shows the paginated list of profiles. The create-profile form should be removed from this page — users will create their profile from the account page (Ticket 05).

## Background

Currently `sosh-profile.yaml` (at `src/mspec/data/lingo/pages/sosh-profile.yaml`) is a minimal placeholder. The model page for `profile` may also show a create widget by default. We want:

- The **profiles model page** — shows pagination only (no create/edit form)
- The **account page** — is where users create/edit their profile (see Ticket 05)

## Implementation

1. **`src/mspec/data/lingo/pages/sosh-profile.yaml`** — Rewrite as follows:
   - Use `src/mspec/data/lingo/pages/builtin-mapp-model.json` as a starting point
   - instead of being dynamic like `builtin-mapp-model.json` should be hardcoded for the profile page
   - have `model` widget for pagination
   - do not have `model` widget for create

2. **`src/mspec/data/generator/sosh-net.yaml`** — Confirm (or update) the `profile.page` reference points to the updated `sosh-profile.yaml`

3. **Browser JS client** (`templates/mapp-py/` or the sosh-net front-end) — Ensure the profile page route uses the custom page YAML instead of the builtin model page

## Tests

- Playwright test (`templates/sosh-net/tests/`) — navigate to `/sosh-net/profile`, verify:
  - Profile list table is visible
  - No create/edit form is present on this page
  - Pagination controls are visible (if there are enough profiles)
  - Clicking a profile navigates to the instance page

## References

- `src/mspec/data/lingo/pages/sosh-profile.yaml` — current placeholder
- `src/mspec/data/lingo/pages/sosh-network-page.yaml` — navigation links
- `src/mspec/data/lingo/pages/builtin-mapp-page-account.yaml` — account page for context
- Ticket 05 — Account page with profile create/edit
