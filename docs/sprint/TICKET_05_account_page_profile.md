# Ticket 05 — Account Page: Keep Generic (No Profile Coupling)

**Branch:** `improve-sosh-net-ui`

> **Note:** The original scope of this ticket (adding profile create/edit to the account page) has been superseded. Profile management is now handled entirely on the profile page (Ticket 04). This ticket now covers ensuring the account page remains clean and reusable.

## Overview

Verify that `builtin-mapp-page-account.yaml` (the sosh-net account page) contains no profile-specific logic, so it can be reused in other projects. Make any needed cleanup and confirm the page spec only handles auth (login, logout, register, current-user display).

## Background

`builtin-mapp-page-account.yaml` (at `src/mspec/data/lingo/pages/builtin-mapp-page-account.yaml`) currently handles:
- Login/logout/register via `auth.*` ops
- Displaying current-user details when logged in

**There should be no profile-specific state, ops, or output blocks on this page.** Profile management lives on the profile page (`sosh-profile.yaml`), so users navigate there after logging in.

## Implementation

1. **Audit `builtin-mapp-page-account.yaml`** — confirm there are no references to `sosh_net.profile`, `get_current_user_profile`, or any profile fields.

2. **Add a "manage profile" link** (optional but recommended) — when the user is logged in, show a navigable link to `/sosh-net/profile` so they can reach their profile management page without hunting for it:

   ```yaml
   - branch:
     - if:
         state: {is_logged_in: {}}
       then:
         - text: 'manage your profile: '
         - link:
             text: 'go to profile page'
             url: '/sosh-net/profile'
   ```

3. **`src/mspec/data/generator/sosh-net.yaml`** — confirm `sosh_net.pages.account` still points to `builtin-mapp-page-account.yaml` (unchanged).

## Files Changed

| File | Change |
|------|--------|
| `src/mspec/data/lingo/pages/builtin-mapp-page-account.yaml` | Audit; add profile link if not already present; remove any profile-specific state |

## Tests

- Playwright test (`templates/sosh-net/tests/`):
  - Navigate to `/sosh-net/account` — verify no profile fields (username, bio, profile picture) appear
  - When logged in, verify a link or pointer to the profile page is present
  - Existing login/logout/register tests must still pass

## Dependencies

- Ticket 04 — Profile page (provides the destination for the profile link)

## References

- `src/mspec/data/lingo/pages/builtin-mapp-page-account.yaml` — account page to audit
- `src/mspec/data/generator/sosh-net.yaml` — page wiring
- Ticket 04 — where profile create/edit now lives
