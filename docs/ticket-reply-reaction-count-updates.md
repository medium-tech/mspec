# Ticket: Implement Real-Time Reply Reaction Count Updates

## Summary
Implement immediate (optimistic) reaction count updates for **reply rows** in `social-thread-instance.json` when users react, switch reactions, or unreact on a reply.

## Background
Current reply behavior updates `reply_user_reaction_local[index]` after successful operations, but each row’s displayed `reaction_counts` remains server-derived until refetch. This leaves reply counts stale in-session.

## Scope
- Reply rows only (not main post).
- Indexed local state and row-level success handlers.
- No server API contract changes.

## Proposed Changes
1. Add local indexed state field:
   - `reply_reaction_counts_local` (default `[]`; each entry is one reply row’s count list)
2. Seed/reseed local reply counts from loaded reply data:
   - `reply_reaction_counts_local[index] <- reply_items[index].reaction_counts`
3. Ensure reset/pagination alignment:
   - clear/reseed local reply count state in the same flow that resets reply state (`reset_reply_state`) to prevent index drift.
4. Add/reuse helper op logic for reaction transitions per row:
   - inputs: `old_reaction`, `new_reaction`, `existing_counts`
   - decrement/remove old group, increment/add new group, no negatives
5. Update each reply react/unreact `on_success` handler to set both:
   - `reply_user_reaction_local[index]`
   - `reply_reaction_counts_local[index]`
6. Update reply count rendering to prefer local indexed counts first, then fallback to row server counts.

## Acceptance Criteria
- After successful reply react, that row’s count display updates immediately without page refresh.
- Switching a reply reaction updates both old and new count groups immediately for that row only.
- Unreact decrements/removes the matching group immediately for that row.
- Local reply count state stays aligned with reply rows across refresh/pagination/reset.
- Existing reply reaction UX remains functional across all reply rows.

## Testing
- `tests/test_lingo.py` already exists and currently validates social-thread page-spec behavior, so this ticket should extend that existing module (not create a new test file).
- Extend/adjust `tests/test_lingo.py` assertions for:
  - `reply_reaction_counts_local` state field usage
  - indexed local count writes in reply success handlers
  - local-first reply count rendering references
- Run:
  - `PYTHONPATH=src python -m unittest tests.test_lingo`

## Risks / Notes
- Reply state is index-based; incorrect reset/reseed handling can map counts to wrong rows.
- Rapid repeated clicks may create overlapping operations; if needed, gate row/button actions while in-flight.
- Keep count mutation in `on_success` paths to avoid stale optimistic state on failures.
