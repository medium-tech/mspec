# Plan: Update Reaction Counts After Reacting (Research)

## Goal
Enable `social-thread-instance.json` to update reaction counts immediately in the UI when a user adds, changes, or removes a reaction for:
- the main post
- each reply row

This document focuses on implementation planning (not implementation).

## Current behavior (confirmed)

### Main post
- Current counts are derived from server-loaded data (`thread_op_view_state.result.value.main_post_reaction_counts.value`).
- Main-post reaction buttons only update `main_post_user_reaction_local` on success.
- Result: user reaction label updates immediately, but reaction counts remain stale until a reload/refetch.

### Replies
- Each reply row renders server-provided `reaction_counts`.
- Reply reaction actions only update `reply_user_reaction_local[index]`.
- Result: user reaction indicator updates immediately, but row reaction counts remain stale until refetch.

## Lingo capability assessment

### What already exists
- `set` in Browser2 already supports:
  - setting a single state field,
  - setting indexed list entries (`index` / `_list_index`),
  - setting struct fields (single-field and multi-field update).
- This is enough to support local optimistic reaction-count state if we store counts in state.

### Gaps / constraints
- **Python renderer only:** `set` currently supports only full-field replacement (single top-level state field).
- **Both renderers:** no built-in helper exists to directly "increment/decrement reaction count by emoji" in a counts list.
- **Both renderers (documentation/runtime shape):** no documented way to set multiple *top-level* state fields in one `set` expression.

## Recommended implementation approach

### 1) Add local count state fields
- Main post:
  - `main_post_reaction_counts_local` (list, default `[]`)
- Replies:
  - `reply_reaction_counts_local` (list of list, default `[]`)

### 2) Initialize local counts from server data
- On initial successful load:
  - seed `main_post_reaction_counts_local` from `main_post_reaction_counts`
  - seed `reply_reaction_counts_local[index]` from each reply item's `reaction_counts`
- On page/offset refresh (`reset_reply_state` op in `social-thread-instance.json`), clear or reseed reply-local count state so row indexes stay aligned.

### 3) Centralize count adjustment logic in helper ops
Create ops to update counts based on reaction transition:
- inputs: `old_reaction`, `new_reaction`, `existing_counts`
- behavior:
  - if old == new: no-op
  - decrement/remove old group (if old not empty)
  - increment/add new group (if new not empty)
  - never emit negative counts
  - preserve deterministic ordering (keep existing order; append newly introduced emoji at end)

Use these ops from each `on_success` handler.

### 4) Update success handlers to write both reaction and counts
- Main post reaction/unreact success:
  - keep setting `main_post_user_reaction_local`
  - also set `main_post_reaction_counts_local` using helper op
- Reply reaction/unreact success (indexed by `self.index`):
  - keep setting `reply_user_reaction_local[index]`
  - also set `reply_reaction_counts_local[index]` using helper op

### 5) Render counts from local-first fallback
- Main post count display should prefer `main_post_reaction_counts_local` when populated, then fallback to server `main_post_reaction_counts`.
- Reply row count display should prefer `reply_reaction_counts_local[index]` when present, then fallback to row `reaction_counts`.

## Framework updates needed?

### Short term (no Browser2 framework change required)
Based on current Browser2 `set` behavior (indexed list updates plus struct/list writes), this can be implemented in `social-thread-instance.json` plus helper ops without changing Browser2 runtime code.

### Recommended follow-up framework hardening
To reduce future complexity and parity risk:
1. Extend the existing Python `render_set` function to support indexed list and struct-field updates (to match Browser2 behavior).
   - `render_set` is the current Python state-assignment handler in `src/mspec/lingo.py`.
2. Document Browser2 `set` features in docs (`index`, struct multi-set).
3. Consider a first-class helper function/op for grouped reaction count mutation to avoid repeated complex branching logic in page specs.

## Validation plan for implementation ticket
1. Extend `tests/test_lingo.py` page-spec assertions for new local count state fields and local-first count rendering references.
2. Add/adjust Browser2 tests (if available for this flow) to validate count text updates immediately after react/unreact without full refresh.
3. Run targeted tests first:
   - `PYTHONPATH=src python -m unittest tests.test_lingo`
4. Run broader suite as needed (acknowledging unrelated environment failures).

## Risk notes
- Reply list uses index-based local state; pagination/refresh must reset or reseed local arrays to avoid index drift.
- Simultaneous rapid clicks could race updates; if needed, disable controls while an op is in-flight per row/button.
- If server rejects a reaction change, local counts must not update (keep updates in `on_success` only).
