# Ticket: Implement Real-Time Main Post Reaction Count Updates

## Summary
Implement immediate (optimistic) reaction count updates for the **main post** in `social-thread-instance.json` when users react, switch reactions, or unreact.

## Background
Current behavior updates `main_post_user_reaction_local` after successful react/unreact, but displayed counts still come from server-loaded state until a refetch. This creates a visible delay and inconsistent UI state.

## Scope
- Main post only (not reply rows).
- Page-spec and helper-op changes required for local count updates.
- No server API contract changes.

## Proposed Changes
1. Add local state field:
   - `main_post_reaction_counts_local` (default `[]`)
2. Seed local counts from server-loaded main post counts on successful initial load.
3. Add/reuse helper op logic to apply reaction transitions:
   - inputs: `old_reaction`, `new_reaction`, `existing_counts`
   - decrement/remove old reaction group when needed
   - increment/add new reaction group when needed
   - never allow negative counts
4. Update main-post react/unreact `on_success` handlers to set:
   - `main_post_user_reaction_local`
   - `main_post_reaction_counts_local`
5. Update rendering to prefer local counts first, then fallback to server counts.

## Acceptance Criteria
- After successful main-post react, displayed main-post count updates immediately without refetch.
- After switching reaction (e.g. 👍 -> ❤️), old count decrements and new count increments immediately.
- After unreact, corresponding count decrements/removes immediately.
- Count rendering still works from server fallback when local state is empty.
- Existing main-post reaction UX remains functional.

## Testing
- `tests/test_lingo.py` already exists and currently covers page-spec structure checks, so this ticket should extend that existing module (not create a new test file).
- Extend/adjust relevant `tests/test_lingo.py` assertions for:
  - presence of `main_post_reaction_counts_local`
  - local-first count rendering references
  - success-path updates that include count state mutation
- Run:
  - `PYTHONPATH=src python -m unittest tests.test_lingo`

## Risks / Notes
- Keep local updates in `on_success` only (avoid optimistic updates on failed operations).
- Ensure helper logic preserves deterministic count-group ordering.
