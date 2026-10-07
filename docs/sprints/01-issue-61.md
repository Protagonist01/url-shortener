# Sprint 1 — issue61: compatible framework/parser repair

Status: **completed — all scoped gates passed; issue61 closed**.
Issue: https://github.com/Protagonist01/url-shortener/issues/61
Entry checked2026-10-08; implementation base main dc815b5d7610fb8772d23705ba2e345d057706a1.
Issue2 audit and58 advisory discovery are verified closed from live GitHub
and linked evidence. Existing issue62 fix is merged via65.

## Gates

| Gate | State | Evidence / remaining work |
|---|---|---|
| G0 | passed for scoped repair | Audit/discovery complete; live61 explicitly permits dependency repair without F01 hosting/quotas/privacy choices; excludes unpublished QR uploads |
| G1 | passed for scoped repair | All13 sources mapped; exact supported stack resolves; fresh scans clear targets; published contracts and documented rollback verified |
| G2 | passed for scoped repair | Linux12 library/8 token/18 guarded real API checks, image/monitoring, migrations, real worker and cleanup pass |
| G3 | passed for issue61 scope | Raw bounded parser/static/redirect CPU/RSS/thread/lag profiles validated; rollover write isolated from loop; no issue-specific production target was selected; F01/F05 budgets still held |
| G4 | passed | Parent final diff/source/fixture review complete; final headc7d6a4c foundation37703812297/advisory37703812319 passed; ADR/compatibility/reproduction/rollback documented |
| G5 | passed | PR67 merged with c7d6a4c0f59fffc12d521294e67ea4345c1f19f2 guard asf6e5e2c08d3a38753a806fddbecd1be641351cfc; fetched main contains checked head/merge; live61 closed completed via67 |

## Acceptance-to-evidence map

| Live acceptance item | Evidence required | State |
|---|---|---|
| Review every advisory; choose supported pins; clean Linux/Python3.12 resolution | All13 source records/ranges reviewed; actual fresh resolution/install/pip check; exact pins/manifest hashes in retained evidence | passed |
| Remove targeted findings without suppression | Fresh49 runtime/55 test/53 operations reports, zero known findings/no skips/no ignored IDs; targeted gate passes | passed |
| Real API/static/parser/range compatibility | Linux12 library/18 real HTTP regressions plus guarded static/metrics/JSON and cold/warm printed-anchor controls | passed |
| Resource bounds and event-loop isolation | Exact raw40 redirect-only/40 mixed redirect+24 static/16 parser/4 file measurements; zero errors/timeouts; actual thread-isolated rollover control; unpublished QR excluded | passed for scoped repair |
| Compatibility/rollout/performance documentation and actual CI | ADR0004/reproduction/rollback, retained exact source/resource data; implementation and final-head actual jobs pass; reviewed guarded merge verified | passed |

## Existing observations, not completion

The retained post-pytest reports resolve47 runtime/53 test/51 operations
packages and retain26 raw records in Starlette/python-multipart,13 unique
package/advisory IDs. Counts do not prove distinct exploitable bugs.

FastAPI0.115.6 and instrumentator7.0.0 constrain old Starlette. Primary metadata
investigation found instrumentator8.1.0 admits Starlette1.x; current framework
and parser candidates still need release/source/compatibility checks.
Candidate FastAPI0.141.1/Starlette1.7.0/multipart0.0.32/instrumentator8.1.0 pins
are implemented with a targeted fresh-scan gate in all scopes. All13 source
boundaries are mapped in [repair verification](../verification/framework-dependency-remediation.md).
Twelve meaningful local library tests pass using isolated hash-verified wheel
paths and the unchanged owner's Python3.12.13 dependencies. This is not a clean
install/real-service pass. Actual Linux/Python3.12 install/image/worker/API and
resource evidence remain pending. Unknown upload quotas stay unapproved.
IN08 concerns unpublished prototype publication, not permission to claim coverage.

This earlier candidate checkpoint is superseded by actual d31107d evidence:
[validated summary](../verification/framework-linux-evidence.json),
[resource results](../verification/framework-linux-resource-evidence.json),
[source/reproduction/limits](../verification/framework-dependency-remediation.md).
PR: https://github.com/Protagonist01/url-shortener/pull/67.
Verified CI source6144325c4a5b199b435d5a393e21ee2f447dc5ae differs from branch
d31107d489cf79b6d40b13573f2508e5cc82f9cc. Manifest/static hashes and raw
nearest-rank quantiles match. G3 does not approve F01 numerical release budgets.

## Exit

Final [foundation37703812297](https://github.com/Protagonist01/url-shortener/actions/runs/37703812297/job/113073313265)
and [advisory37703812319](https://github.com/Protagonist01/url-shortener/actions/runs/37703812319/job/113073313254)
passed at the checked documentation head. GitHub closed61 through merged67;
fetched main's merge commit has the checked PR head as a parent. The read API
omits merge_commit_sha; use the actual merge tool's returned SHA plus fetched
commit/parent/ancestry, rather than inventing one or relying on issue closure alone.

Next: [Sprint2/issue1](02-issue-1.md), held at G0 for IN01–IN06. Do not start42
or later work. All8 milestones and parent3 remain open; this scoped completion
does not approve numerical release budgets, full security, Windows deployment,
browser/physical QR or unpublished prototype coverage.
