# MilestoneVerdict

`MilestoneVerdict` is a standalone GenLayer Intelligent Contract primitive for
evidence-backed milestone adjudication. It is designed for agent marketplaces,
grants, bounties, service agreements, and escrow systems that need a neutral
structured decision but want to keep custody and payment logic in a separate
contract.

## Why this primitive exists

A deterministic contract can check a timestamp or a signature, but it cannot
reliably decide whether a delivered API "matches the agreed specification" or
whether submitted work "materially satisfies" a natural-language milestone.
Those questions require evidence interpretation and judgment.

This contract makes that decision explicit and reusable:

- the requester defines acceptance criteria before delivery;
- the provider submits a stable, validator-accessible evidence URL;
- a leader proposes a structured verdict;
- independent validators re-fetch the evidence and judge the proposal;
- only the consensus-backed result updates contract state.

The output is deliberately bounded: `ACCEPT`, `PARTIAL`, `REVISION`, or
`REJECT`, a 0-100 score, a payout recommendation in basis points, reason codes,
and a short evidence-grounded summary.

## State machine

```text
OPEN -> SUBMITTED -> ACCEPTED
                  -> PARTIAL
                  -> REJECTED
                  -> REVISION -> SUBMITTED
```

Only the provider can submit evidence. Either party can trigger adjudication.
Revision rounds are capped at creation time (maximum five), preventing endless
re-submission loops.

## Consensus design

The leader:

1. renders the agreed evidence URL as text;
2. treats the page as untrusted evidence and ignores embedded instructions;
3. evaluates it against the immutable milestone criteria;
4. returns strict JSON with bounded decision and payout fields.

Each validator:

1. rejects malformed or internally inconsistent proposals deterministically;
2. independently fetches the same evidence;
3. asks its own model whether the proposed decision, score band, payout, reason
   codes, and summary are reasonably supported;
4. votes on the proposal rather than requiring identical free-form reasoning.

This is a custom Equivalence Principle: validators agree on the settlement
semantics, not on identical prose.

## Prompt-injection and reliability safeguards

- Evidence is explicitly labeled untrusted in both leader and validator prompts.
- The contract forbids browsing beyond the submitted page.
- Rendered evidence is capped at 12,000 characters.
- Output keys, enums, ranges, payout rules, revision rules, and summary length
  are checked before the validator invokes an LLM.
- The decision that changes state is structured and narrow; reasoning prose is
  not consensus-critical.
- The contract does not claim legal authority and does not itself transfer
  funds. Integrators can consume `payout_bps` after protocol finality.

## Public methods

### `create_milestone(provider, title, criteria, max_revisions)`

Creates an `OPEN` milestone. The caller becomes the requester.

### `submit_evidence(milestone_id, evidence_url, submission_note)`

Provider-only. Accepts evidence for an `OPEN` or `REVISION` milestone.

### `adjudicate(milestone_id)`

Party-only. Runs GenLayer consensus and writes the accepted structured verdict.

### `get_milestone(milestone_id)`

Returns all milestone and verdict fields for integrations and reviewers.

### `count()`

Returns the number of created milestones.

## Example

1. A requester creates a milestone: "REST API delivery" with exact acceptance
   criteria and allows two revisions.
2. The provider publishes a stable delivery report and calls
   `submit_evidence` with its URL.
3. Either party calls `adjudicate`.
4. The accepted result may be `PARTIAL` with `payout_bps = 7500`, plus reason
   codes explaining the material gap.
5. An integrating escrow can use that final result as its settlement input.

## Tests

The test suite covers:

- lifecycle and caller permissions;
- valid input constraints;
- a supported `ACCEPT` verdict;
- validator agreement with independent evidence review;
- validator rejection of an unsupported leader proposal;
- storage pickling checks.

Run with the official GenLayer testing suite:

```bash
pip install genlayer-test
pytest tests/ -v
```

Use Studio Mode for a final multi-validator integration run before deployment.

## Design boundary

This contract is an adjudication primitive, not a complete escrow product. That
separation is intentional: custody, token choice, dispute deposits, release
timing, and jurisdiction-specific rules belong in the integrating application.
