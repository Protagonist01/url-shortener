# Roadmap execution ledger

Goal: work through **all issues and all eight milestones**, recording owner questions in INPUT_REQUIRED.md. No reduced-scope completion claim is allowed.

## Latest authoritative state — 2026-10-06

Latest implementation checkpoint: main is `43efdc66d1d2aefbf98fd1e259cc53548b6eac77`, including reviewed worker52, configuration54, correctness56, dependency evidence59 and JWT repair63. Audit2 and children51/53/55/58/60 are closed; security43, analytics45, full CI3, dependency repairs61/62 and all8 milestones remain open. Final JWT headcf33361 passed actual Linux foundation37538150154 and advisory37538150166. Published reports preserve8 JWT contracts,18 HTTP regressions, real token/anchor/worker checks and55-package fresh resolution without JOSE/ECDSA. These updates supersede pending states below; original owner source/index remain preserved.

- Refreshed GitHub issues and fetched origin/main: `779206989c0d0e8377e5c7cf3b1e706927e9717f`, owner merge PR #50 of the roadmap/audit commits.
- Forty initial roadmap issues and seven remediation issues were open at initial refresh; all eight milestones remain incomplete. PR #49 is still open/draft although its commits reached main through #50. Subsequent closure/child task evidence is recorded below.
- Existing local prototype changes remain in the original checkout; an attached managed worktree starts from origin/main for scoped implementation. No source is discarded or published wholesale.
- F02 audit evidence is published, with route compatibility, 81 focused passes/one QR failure, 18 API passes and linked remediation. These are 2026-10-03 results, not new test results.
- F01 numerical/deployment/privacy decisions remain unapproved; INPUT_REQUIRED.md tracks these and later stage choices.
- F02 / #2 is now closed after verifying its evidence deliverables on owner-merged main via PR #50. This closes the audit, not the remediation. AUD04a/#51 is a real child of AUD04/#45 in M0; no milestone is complete.

## Current work

PR63 merged as43efdc66d1d2aefbf98fd1e259cc53548b6eac77 and GitHub closed60. Windows clean install/worker failures remain unverified limitations, not passes; final inspection confirms both owned local containers absent. All76 original saved source/config/readme/ignore hashes are unchanged. Next independent repairs are61 (framework/parsers) and62 (test tools); unknown owner choices remain in INPUT_REQUIRED.md. No production deployment or full-roadmap completion.

Actual GitHub refresh at2026-10-06T22:14:27Z: all8 milestones open; M0 has6 closed/13 open and each later milestone5 open. There are48 open issues excluding PRs. Counts include linked discovery/remediation children, not only the initial40 roadmap issues.

DEP01/60 implementation PR63 passed actual Linux foundation37536532072 and advisory37536532081 on headeae7f8f. Retrieved reports:18 HTTP API tests plus historical/current-token/ownership/anchor checks passed, actual worker delivery passed, clean resolved55 packages exclude JOSE/ECDSA with no known PyJWT findings. Remaining3 packages/28 records/14 unique IDs stay under61/62. Ordinary serial token decode p99 was71.323us with zero errors; this is not HTTP/load/capacity evidence. Verified reports are in docs/verification/jwt-dependency-remediation.md. Original Windows clean installs timed out twice, worker readiness failed, and owned cleanup required a retry; Linux results do not prove Windows readiness. Merge still requires the final reviewed head's checks. All8 milestones and parent3/43 remain open.

Verified discovery58 is complete: PR59 final head91123c8 passed actual Linux advisory37532103550 and correctness37532103585, then merged as e0ad487ecc0e0501d104e6a03fc01ede66220f4c. All findings map to open children60/61/62. The Windows audit is incomplete after its recorded PyPI timeout; no clean-security or Windows claim. The next scoped branch implements DEP01/60: pinned PyJWT without the unused JOSE/ECDSA chain, historical cross-issuer/verifier fixtures and guarded real HTTP API/printed-link tests. Eight local synthetic JWT contract tests passed before real service checks; new clean install/actual CI/scan remain pending. Original owner code remains untouched.

Dependency discovery F03b/#58: PR59's actual Linux collection resolves61 packages, with5 affected packages,35 raw advisory records and18 unique package/advisory IDs. Correctness CI also passes; security result is known_vulnerabilities, not an approval. Published mapping and sanitized baseline are in docs/security and docs/verification/dependency-advisories.md. DEP01/#60, DEP02/#61 and DEP03/#62 map all findings; all are children of full CI3 in M0. No runtime dependency is upgraded in the evidence branch; parent/release gates remain open. Windows tooling failures and its ordered run are recorded separately. F01 inputs remain pending in the original and managed registers, and issue1 has no new comments.

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

- PR56 is merged and child55 closed after actual Linux check success; details and exact run are in docs/verification/foundation-ci.md. Local fixtures/worker were cleaned. Original source comparison:76 files, zero changes. Draft49 is closed as superseded by already-merged50; PR41 was already merged. No milestone is complete.


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

### Latest checkpoint — 2026-10-07

PRs59/63/64 are merged; dependency evidence58 and JWT repair60 are closed. [PR65](https://github.com/Protagonist01/url-shortener/pull/65) implements62 with pytest9.1.1/plugin1.4.0 and separate runtime/test/operations installs. Review found compact includes omitted child hashes; a confirmed correction adds downgrade regressions.

Implementation c5eac2309cf7a072a8787e1791ce0268fc82df39 passed actual foundation37694595696/advisory37694595813. Old/fixed direct/chained symlink checks, ordinary root, production image package/CLI/health, monitoring,8 token contracts,18 HTTP checks, migrations and worker delivery pass. Retained exact evidence lives in docs/verification/test-dependency-remediation.md. Runtime47/test53/operations51 still contain26 raw Starlette/multipart records13 unique IDs under open61. Windows daemon remains unavailable; no Windows/load/full-lock/security/milestone proof.

PR65 merge waits for final documentation-head checks;62 remains open until then. Parent3/43/45 and all eight milestones remain incomplete. Next independent task is61 compatible framework/parser repair. Owner choices remain in INPUT_REQUIRED.md; the full roadmap goal stays active.

PR65 final head5fb8f9cf132aa4254dd340b53cdcd213624dfc8e passed foundation37695071938/advisory37695072149 and merged with that head guard asdc815b5d7610fb8772d23705ba2e345d057706a1. Main ancestry and closed62/all acceptance checks are verified. This supersedes the pending-merge sentence. Original76 saved app/test/config/readme/ignore hashes remain unchanged.

Current branch codex/framework-parser-dependencies starts from that fetched main. Issue61's primary metadata investigation found instrumentator7.0.0 requires Starlette below1.0;8.1.0 admits1.x. Latest FastAPI0.142.4 introduces base OpenTelemetry, while0.141.1 metadata has no such base dependency and admits Starlette1.x/Pydantic2.10.4. These are candidates, not installed/verified pins or a policy choice. Inspect all thirteen framework/parser advisory boundaries and actual compatibility/resource behavior before adopting any candidate.

Authoritative refresh2026-10-07T22:24:33Z:47 open issues excluding PRs; all8 milestones open. M0 has7 completed/12 open; later stages each have5 open. No goal or milestone completion is claimed.

Use GitHub as live status. Add each result with commit/PR, relevant tests, observed failures and next available safe task. Do not infer approval from a pending answer. End a turn with the full goal active unless requirement-by-requirement evidence proves completion or the specified repeated-blocker threshold is met. No dates, guarantees, quotas or approval decisions are invented.
