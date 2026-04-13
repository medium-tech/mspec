# Ticket 04 — Custom Profiles Page (List + Create/Edit for Current User)

**Branch:** `improve-sosh-net-ui`

## Overview

Rewrite `sosh-profile.yaml` to be the single landing page for profile management. The page:

1. Shows a paginated list of all profiles (public view, anyone can browse)
2. For logged-in users: calls `get_current_user_profile` and branches:
   - **No profile found** — shows a `model` create widget so the user can create their profile
   - **Profile found** — shows a `model` read/edit widget for their own profile

The account page (`builtin-mapp-page-account.yaml`) is intentionally left profile-agnostic so it can be reused in other projects (see Ticket 05).

## Background

The current `sosh-profile.yaml` is a minimal placeholder. The `profile` model:
- Has `max_models_per_user: 1` (one profile per user), `require_login: true`
- Has a `unique: true` constraint on `username` (depends on Ticket 01)
- Is linked to the logged-in user via `user_id`

The page structure should mirror `builtin-mapp-model.json` but be hardcoded for `sosh_net.profile` and use the `get_current_user_profile` op (see Ticket 02 / 03 for the op infrastructure) to determine create vs. edit mode.

Use `builtin-mapp-page-account.yaml` as the reference pattern for the auth check and the `op` widget auto-submit pattern.

## Part A — Finish the `get_current_user_profile` op in `sosh-net.yaml`

The op is partially defined. It currently tries to use `db.read` with `model_id = auth.current_user.id`, which is incorrect — the profile is looked up by its `user_id` field, not by its own `id`. Update the op to use `db.query` (from Ticket 02) with a `fields` dict that filters by `user_id`:

```yaml
get_current_user_profile:
  name:
    lower_case: 'get current user profile'
  description: 'Get the profile of the currently logged in user'
  func:
    type: struct
    value:
      call: 'db.query'
      args:
        model_type: 'sosh_net.profile'
        fields:
          type: struct
          value:
            user_id:
              call: 'key'
              args:
                key: 'id'
                object:
                  call: 'auth.current_user'
                  args: {}
  params: {}
  result:
    type: struct
    fields:
      profile:
        name:
          lower_case: 'profile'
        type: struct
        description: 'The current user profile, or null if they have not created one yet'
```

## Part B — Rewrite `sosh-profile.yaml`

Use `builtin-mapp-model.json` as a starting point. Key differences from the generic page:

- Hardcoded for `sosh_net.profile` (no `params` for project/module/model names)
- Adds an `auth.is_logged_in` state check (pattern from `builtin-mapp-page-account.yaml`)
- Adds a `fetch_my_profile` state entry that auto-submits `get_current_user_profile` op when logged in
- The `output` branches on whether `fetch_my_profile.result.profile` is non-null:
  - **Logged out or loading** — show list only, no create/edit section
  - **Logged in, no profile** — show list + create form
  - **Logged in, has profile** — show list + edit/read form

### Outline

```yaml
lingo:
  version: page-beta-1
  title: "sosh net :: profile"

params: {}

state:
  is_logged_in:
    type: bool
    calc:
      call: key
      args:
        object:
          call: auth.is_logged_in
          args: {}
        key: logged_in

  profile_list:
    type: struct
    default:
      state: pending
      error: ''
      items: []
      total: 0
      showing: 0
      offset: 0
      size: 10

  fetch_my_profile:
    type: struct
    default:
      state: initial
      error: ''
      data: {}
      result:
        type: any
        value: null

  create_profile_state:
    type: struct
    default:
      state: initial
      error: ''
      data: {}
      result:
        type: any
        value: null

  edit_profile_state:
    type: struct
    default:
      state: initial
      error: ''
      data: {}
      result:
        type: any
        value: null

ops: {}

output:
- heading: 'sosh.net'
  level: 1

- heading: ':: profiles'
  level: 2

- breadcrumbs:
  - home
  - sosh-net
  - profiles

- break: 1

# --- public list ---
- heading: ':: all profiles'
  level: 3

- model:
    bind:
      state: {profile_list: {}}
    display: list
    http: '/api/sosh-net/profile'
    definition: 'sosh_net.profile'
    instance_url: '/sosh-net/profile/'

- break: 1

# --- my profile (logged-in only) ---
- branch:
  - if:
      state: {is_logged_in: {}}
    then:
      # auto-fetch current user's profile
      - op:
          bind:
            state: {fetch_my_profile: {}}
          interactive: false
          http: '/api/sosh-net/get-current-user-profile'
          definition: 'sosh_net.get_current_user_profile'
          auto_submit: true

      - branch:
        - if:
            call: eq
            args:
              a: {key: {object: {state: {fetch_my_profile: {}}}, key: result}}
              b: null
          then:
            - heading: ':: create your profile'
              level: 3
            - model:
                bind:
                  state: {create_profile_state: {}}
                display: create
                http: '/api/sosh-net/profile'
                definition: 'sosh_net.profile'
                instance_url: '/sosh-net/profile/'
        - else:
            - heading: ':: your profile'
              level: 3
            - model:
                bind:
                  state: {edit_profile_state: {}}
                display: edit
                http: '/api/sosh-net/profile'
                definition: 'sosh_net.profile'
                instance_url: '/sosh-net/profile/'
                item:
                  key:
                    object: {state: {fetch_my_profile: {}}}
                    key: result
```

## Files Changed

| File | Change |
|------|--------|
| `src/mspec/data/generator/sosh-net.yaml` | Fix `get_current_user_profile` op (Part A) |
| `src/mspec/data/lingo/pages/sosh-profile.yaml` | Rewrite (Part B) |

## Tests

Playwright tests (`templates/sosh-net/tests/`):
- **Logged out** — `/sosh-net/profile` shows the profile list; no create/edit form visible
- **Logged in, no profile** — create-profile form is visible; submit creates a profile and page switches to edit form
- **Logged in, has profile** — edit form shows the correct username/bio values; submit updates the profile
- **Duplicate username** — submitting an existing username returns a 400 and shows an error (depends on Ticket 01 `unique` constraint)
- Verify pagination controls appear when more than `size` profiles exist

## Dependencies

- Ticket 01 — `unique: true` on `username`; `max_models_per_user: 1` enforcement
- Ticket 02 — `db.query` lingo function (needed by the `get_current_user_profile` op)
- ~~Ticket 05~~ — profile management is now handled entirely on this page (Ticket 05 scope changed; see Ticket 05)

## References

- `src/mspec/data/lingo/pages/sosh-profile.yaml` — file to rewrite
- `src/mspec/data/generator/sosh-net.yaml` — op definition to fix
- `src/mspec/data/lingo/pages/builtin-mapp-model.json` — starting-point layout pattern
- `src/mspec/data/lingo/pages/builtin-mapp-page-account.yaml` — auth check + auto-submit op pattern
