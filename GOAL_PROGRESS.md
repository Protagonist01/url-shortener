# Roadmap execution ledger

Goal: work through **all issues and all eight milestones**, recording owner questions in INPUT_REQUIRED.md. No reduced-scope completion claim is allowed.

## Latest authoritative state — 2026-10-06

- Refreshed GitHub issues and fetched origin/main: `779206989c0d0e8377e5c7cf3b1e706927e9717f`, owner merge PR #50 of the roadmap/audit commits.
- Forty initial roadmap issues and seven remediation issues were open at initial refresh; all eight milestones remain incomplete. PR #49 is still open/draft although its commits reached main through #50. Subsequent closure/child task evidence is recorded below.
- Existing local prototype changes remain in the original checkout; an attached managed worktree starts from origin/main for scoped implementation. No source is discarded or published wholesale.
- F02 audit evidence is published, with route compatibility, 81 focused passes/one QR failure, 18 API passes and linked remediation. These are 2026-10-03 results, not new test results.
- F01 numerical/deployment/privacy decisions remain unapproved; INPUT_REQUIRED.md tracks these and later stage choices.
- F02 / #2 is now closed after verifying its evidence deliverables on owner-merged main via PR #50. This closes the audit, not the remediation. AUD04a/#51 is a real child of AUD04/#45 in M0; no milestone is complete.

## Current work

AUD04 / #45: child [AUD04a / #51](https://github.com/Protagonist01/url-shortener/issues/51) implements the missing worker task registration. Fresh-interpreter regression failed before the include change and passes afterward. Real delivery verified with one worker and one scheduler through isolated Redis/PostgreSQL:record_click consumed, hourly schedule preserved, one scheduled rollup consumed and two daily rows with counts4 and2. Keep pool/idempotency/incremental rollup outcomes in the parent until separately verified. Child stays open for its implementation PR/review.

Docker was stopped on refresh; the installed Docker Desktop is now running. Verified using Celery5.4.0 solo worker on Windows, not a Linux prefork or load run. Test services used dedicated ports25432/26379 and the exact qr.worker.registration=20261006 label. Removed only those containers and the worker spawned by the harness. Existing Supabase/Langfuse services were untouched; no shared key cleanup occurred.

Commands: `python -m pytest tests/test_worker_registration.py -q`; `python -m scripts.verify_worker_registration up`, `verify`, `down`. Raw logs/JUnit/evidence stay ignored under output/. The before-fix test failed with aggregate_daily_stats missing; latest post-fix test:one pass. No redirect throughput or latency change is claimed.

## Full scope and gates

### Subsequent verified progress

- Owner authorized merging PRs on2026-10-06; INPUT_REQUIRED.md IN09 records approval. Manual deployment is a separate decision.
- [PR #52](https://github.com/Protagonist01/url-shortener/pull/52) merged as `0f316c69f88374a177ce5d4abb58c153d8e249d3`. Fetched main contains the exact worker commit; child #51 is closed. This supersedes the earlier awaiting-review status. Parent #45 remains open.
- [AUD02a / #53](https://github.com/Protagonist01/url-shortener/issues/53) is attached to parent #43. Private configuration is removed only from the isolated branch's index, with Git/Docker boundaries and a public fake template. Before checker failed on tracked .env; final Git/template/synthetic actual Docker checks pass. See docs/verification/2026-10-06-configuration-boundaries.md. Child awaits its implementation PR; no historical cleanup, rotation or parent completion is claimed.

- [PR #54](https://github.com/Protagonist01/url-shortener/pull/54) merged as `e3a97a84a2040a89976d87c0787a7d2c3e010e0e`; GitHub closed child #53. This supersedes its awaiting-review status; parent #43 remains open.
- [F03a / #55](https://github.com/Protagonist01/url-shortener/issues/55) is attached to parent #3 for isolated foundation correctness CI. It reuses verified checks without choosing hosting/service budgets. The full parent remains gated by F01 and broader coverage. Actual GitHub execution is pending; do not mark CI successful from YAML/local results.


| Milestone | Status / next dependency |
|---|---|
| M0 foundation/performance | Audit published; independent correctness fixes can progress. F01 decisions, CI, tenant migrations and measured recovery/performance gates remain |
| M1 free offline QR | Browser-local privacy/payload/styles/export/accessibility outcomes depend on foundation; source prototype is not the free offline catalog |
| M2 dynamic codes/analytics | Ownership, code versions, reliable redirects, analytics and bounded routing/limits remain |
| M3 hosted-page MVP | Editor, publish, blocks, abuse and release/restore/printed-link gates remain |
| M4 brand/industry/AI/paid | Pilot/provider/pricing decisions plus actual implementations remain |
| M5 business/trust | Teams/domains/signatures/wallet/vendor integrations and their prerequisites remain |
| M6 developer API | Keys, batch jobs, webhooks, SDK/embed and tenant capacity/reconciliation remain |
| M7 gated expansion | Authenticated updates, opt-in offline pages, artistic/community/physical-product evaluations remain |

## Continuation rules

Use GitHub as live status. Add each result with commit/PR, relevant tests, observed failures and next available safe task. Do not infer approval from a pending answer. End a turn with the full goal active unless requirement-by-requirement evidence proves completion or the specified repeated-blocker threshold is met. No dates, guarantees, quotas or approval decisions are invented.
