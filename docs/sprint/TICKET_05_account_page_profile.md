# Ticket 05 — Custom Account Page with Profile Create/Edit

**Branch:** `improve-sosh-net-ui`

## Overview

Update the sosh-net account page to allow logged-in users to create or edit their profile (username, bio, profile picture). The existing account page handles login/logout/register; extend it to also manage the user's profile.

## Background

Currently `builtin-mapp-page-account.yaml` (at `src/mspec/data/lingo/pages/builtin-mapp-page-account.yaml`) handles auth only.

The `profile` model:
- Has `max_models_per_user: 1` (one profile per user)
- Has a `unique: true` constraint on `username`
- Is linked to the logged-in user via `user_id`

The account page should:
1. If the user has no profile → show a create-profile form
2. If the user has a profile → show the profile fields with an edit form

## Implementation

1. **`src/mspec/data/lingo/pages/builtin-mapp-page-account.yaml`** (or a new `sosh-net-account.yaml`) — Extend the page spec:
   - Add a state entry that fetches the current user's profile (call `db.list` with filter `user_id = current_user.id`, or use a dedicated op if available)
   - Branch on whether `state.my_profile` is empty:
     - **No profile** — render an inline create form for `sosh_net.profile` (username, bio, profile picture fields), wired to `POST /api/sosh-net/profile`
     - **Has profile** — render the profile data as a table, with an edit form (or edit-in-place) wired to `PUT /api/sosh-net/profile/<id>`

2. **`src/mspec/data/generator/sosh-net.yaml`** — Confirm the `sosh_net.pages.account` key points to the updated page YAML

3. Consider whether the existing `op` widget in the page YAML can drive the profile create/edit forms or whether a dedicated lingo `op` must be defined in the spec

## Page Structure (YAML outline)

```yaml
# Under the existing logged-in branch of the account page output:
- branch:
  - if:
      call: eq
      args:
        a:
          call: len
          args: {iterable: {state: {my_profile: {}}}}
        b: 0
    then:
      - heading: ':: create your profile'
        level: 4
      - op:
          bind:
            state: {create_profile: {}}
          interactive: true
          http: '/api/sosh-net/profile'
          method: POST
          definition: 'sosh_net.profile'
          submit_button_text: create profile
  - else:
      - heading: ':: your profile'
        level: 4
      - type: list
        display:
          format: table
        value: <profile fields from state.my_profile[0]>
      - op:
          bind:
            state: {edit_profile: {}}
          interactive: true
          http:
            call: str_concat
            args:
              items:
                - '/api/sosh-net/profile/'
                - <profile id>
          method: PUT
          definition: 'sosh_net.profile'
          submit_button_text: update profile
```

## Tests

- Playwright test (`templates/sosh-net/tests/`):
  - Log in as a user with no profile → verify create-profile form appears
  - Submit the create-profile form → verify profile is created and page shows edit form
  - Edit the profile → verify profile is updated
  - Log in as a different user with an existing profile → verify edit form shows correct values
- Verify that `unique: true` on `username` causes a 400 if the same username is submitted

## Documentation

- Update the `builtin-mapp-page-account.yaml` header comment to reflect the sosh-net-specific profile section
- Add a note in `docs/LINGO_MAPP_SPEC.md` on how the account page integrates with the profile model

## References

- `src/mspec/data/lingo/pages/builtin-mapp-page-account.yaml` — current account page
- `src/mspec/data/generator/sosh-net.yaml` — `sosh_net.modules.pages.account`
- `src/mapp/module/model/db.py` — `db_model_create`, `db_model_update`
- Ticket 01 — `unique` constraint on username
- Ticket 04 — Profiles page (read-only)
