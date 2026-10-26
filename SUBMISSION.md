# Portal submission copy

## Title

MilestoneVerdict — Consensus-Based Delivery Adjudication Primitive

## One-line summary

A reusable GenLayer contract that turns web evidence and natural-language acceptance criteria into a consensus-backed milestone verdict.

## Description

MilestoneVerdict addresses a recurring problem in grants, bounties, service agreements, agent marketplaces, and escrow systems: deterministic contracts cannot judge whether a real-world delivery materially satisfies natural-language acceptance criteria.

The requester commits the criteria and provider address when creating a milestone. The provider then submits a stable evidence URL and delivery note. During adjudication, a leader renders the evidence and proposes a bounded result: ACCEPT, PARTIAL, REVISION, or REJECT, together with a 0–100 score, payout recommendation in basis points, reason codes, and a short evidence-grounded summary.

The custom validator does more than compare formatting. It first rejects structurally inconsistent proposals, independently re-fetches the evidence, and uses its own model to judge whether the proposed decision, score band, payout, reasons, and summary are supported. Validators therefore agree on settlement semantics rather than identical wording.

State follows an explicit OPEN → SUBMITTED → terminal/revision lifecycle. Only the provider may submit evidence, either party may request adjudication, revision rounds are capped, and accepted decisions cannot be silently rewritten. The primitive deliberately separates adjudication from custody so escrow, marketplace, grant, or agent-commerce contracts can consume its structured payout recommendation under their own payment rules.

The repository includes readable source, architecture and security documentation, plus tests for permissions, lifecycle, invalid inputs, supported consensus, validator agreement, and rejection of an unsupported leader verdict.

## Evidence / repository

Replace this line with the public GitHub repository URL before submission.

## Test proof

`4 passed` with the official `genlayer-test` direct test runner.
