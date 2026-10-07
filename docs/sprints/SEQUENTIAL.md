# Sequential sprint execution

Adopted2026-10-08 by owner request. This controls execution of the existing
GitHub roadmap; it does not replace acceptance criteria or authorize new product
choices. A sprint is one issue outcome, not a promised number of days.

## Advancement rule

Work in progress is **one issue**. The first active issue is [61](https://github.com/Protagonist01/url-shortener/issues/61).
Read its live body, prerequisites, milestone gate and code before implementation.
The full47-issue order is in [sequence.json](sequence.json); the original
[roadmap](../ROADMAP.md) remains the product/dependency reference.

Advance only after every applicable gate below is passed:

| Gate | Required proof |
|---|---|
| G0 — Ready | Prerequisite issues completed with their evidence inspected; required owner decisions recorded as answers; no ambiguous acceptance criterion |
| G1 — Behavior | Every live acceptance item mapped to files and concrete results; failure/negative cases verified; linked child outcomes complete |
| G2 — Quality and compatibility | Relevant unit, actual PostgreSQL/Redis, contract/concurrency/browser checks pass; printed links, ownership, privacy and accessibility preserved |
| G3 — Performance and resources | Applicable approved budgets pass, including tail latency/query/resource effects; no-impact documentation explains why benchmarks do not apply |
| G4 — Review and operations | Final diff reviewed, required current-head CI succeeds; configuration/migration, rollout/rollback and documentation complete |
| G5 — Integration | Authorized PR merge uses checked head; fetched target contains the implementation; GitHub issue closure verified; gate record contains evidence links |

Mark evidence **passed**, **failed**, **unverified** or **input_required**.
A test being unavailable is unverified; a green evidence-collection job with
known findings is not security clearance. Approved exceptions must satisfy the
repository's owner/expiry/follow-up rules. Do not reduce the gate to tests that
happen to exist today.

Issue closure alone is insufficient: inspect merged behavior, prerequisites and
evidence. Reopen the gate if later evidence contradicts its result. Partial
parent outcomes stay open even when a child is complete. For implementation,
G3 must distinguish the issue's actual measured impact from F01/F05 release
budgets; missing applicable numerical targets cannot be silently waived.

## Order

| Steps | Milestone | Queue |
|---|---|---|
| 1–12 | M0 | 61 → 1 → 42 → 43 → 46 → 4 → 44 → 45 → 47 → 48 → 3 → 5 |
| 13–17 | M1 | 6 → 7 → 8 → 9 → 10 |
| 18–22 | M2 | 11 → 12 → 13 → 14 → 15 |
| 23–27 | M3 | 16 → 17 → 18 → 19 → 20 |
| 28–32 | M4 | 21 → 22 → 23 → 24 → 25 |
| 33–37 | M5 | 26 → 27 → 28 → 29 → 30 |
| 38–42 | M6 | 31 → 32 → 33 → 34 → 35 |
| 43–47 | M7 | 36 → 37 → 38 → 39 → 40 |

Issue61 is the independent remaining dependency repair; audit2 and discovery58
are complete. It does not select F01 budgets. After61 passes, issue1 is the next
gate and presently needs IN01–IN06. Other policy questions still apply at their
own issue's G0; approving F01 does not answer legacy-link management, prototype
publication or secret rotation.

At a milestone boundary, verify **all** its issues/children and the exit gate
in docs/ROADMAP.md, then verify GitHub's milestone state before starting the
next milestone. Later-stage demand/provider/expansion decisions remain required;
evaluation can legitimately decide to defer a concept where that issue permits
it, but cannot masquerade as implementing a promised feature.

The snapshot covers47 open issues checked on2026-10-08. Refresh GitHub at each
entry/exit; if issues/dependencies change, record and review the queue revision
without silently dropping or adding scope. No duration, deadline or staffing
estimate is promised.

## A held gate

Put the question, affected issue/gate and prerequisite in
[INPUT_REQUIRED.md](../../INPUT_REQUIRED.md). Keep the current issue active and
work on its independent investigation, tests or documentation. **Do not skip
to another implementation issue** while that gate is held. A change in order
requires an explicit owner instruction; pending input is not approval.
This sequential rule supersedes the earlier permission to start unrelated
issues while waiting. It does not ask for production deployment permission
again or revoke the owner's authorization to merge verified PRs.

For an issue too large for one PR, reviewed child PRs may progress one at a time
inside its sprint. The parent gate remains held until every required outcome
passes. Preparation of these execution rules is documentation setup, not
completion of issue61 or a separate completed product sprint.

## Evidence records

Use one docs/sprints/NN-issue-NUMBER.md per active sprint. For each live
acceptance item record the concrete evidence, exact commit/run/profile,
passed/failed/unverified status and any limits. Keep G0–G5 status and blocking
input IDs visible. Link the PR, checked head, merge/fetched commit and verified
GitHub closure. Record milestone exit evidence separately at the boundary.
Update sequence.json and GOAL_PROGRESS.md only from those verified states.

Active record: [01 — issue61](01-issue-61.md). No sprint completion is claimed
by creating this plan.
