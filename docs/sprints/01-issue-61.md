# Sprint 1 — issue61: compatible framework/parser repair

Status: **active — investigation; no acceptance item complete**.
Issue: https://github.com/Protagonist01/url-shortener/issues/61
Entry checked2026-10-08; implementation base main dc815b5d7610fb8772d23705ba2e345d057706a1.
Issue2 audit and58 advisory discovery are verified closed from live GitHub
and linked evidence. Existing issue62 fix is merged via65.

## Gates

| Gate | State | Evidence / remaining work |
|---|---|---|
| G0 | passed for scoped repair | Audit/discovery complete; live61 explicitly permits dependency repair without F01 hosting/quotas/privacy choices; excludes unpublished QR uploads |
| G1 | pending | All five acceptance items below remain incomplete |
| G2 | pending | Run actual parser/static/range controls and full relevant isolated compatibility suite |
| G3 | pending | Measure parser/static CPU/RSS/event-loop effects alongside redirects; keep F01 production thresholds unapproved |
| G4 | pending | Final diff review/current-head CI, migration/client compatibility and rollback documentation |
| G5 | pending | No implementation PR, merge or closed61 exists |

## Acceptance-to-evidence map

| Live acceptance item | Evidence required | State |
|---|---|---|
| Review every advisory; choose supported pins; clean Linux/Python3.12 resolution | All13 canonical package/advisory IDs traced to maintainers/fixes; actual joint resolution/install and pip check | unverified |
| Remove targeted findings without suppression | Actual fresh runtime/test/operations reports; explicit targeted gate and visible remaining findings | unverified |
| Real API/static/parser/range compatibility | Guarded auth/management/analytics/redirect/fragment/metrics suite, static bytes/ranges, malicious/malformed parser inputs, legitimate controls | unverified |
| Resource bounds and event-loop isolation | Bounded synthetic parser/static workload concurrent with redirects; CPU/RSS/lag/error results; no unpublished QR coverage claim | unverified |
| Compatibility/rollout/performance documentation and actual CI | Exact pins/profile/commands/results, reviewed deployment/rollback guidance; current-head actual Linux checks | unverified |

## Existing observations, not completion

The retained post-pytest reports resolve47 runtime/53 test/51 operations
packages and retain26 raw records in Starlette/python-multipart,13 unique
package/advisory IDs. Counts do not prove distinct exploitable bugs.

FastAPI0.115.6 and instrumentator7.0.0 constrain old Starlette. Primary metadata
investigation found instrumentator8.1.0 admits Starlette1.x; current framework
and parser candidates still need release/source/compatibility checks.
No candidate pin is adopted, installed or verified yet. Existing runtime
imports/static behavior must guide the patch; unknown upload quotas stay
unapproved. IN08 concerns unpublished prototype publication, not permission
to claim its tests passed.

## Exit

Hold at issue61 until G1–G5 pass. Next step is issue1's owner-approved
architecture/performance/privacy/recovery decision gate. Do not start42 or
later steps because issue1 still needs answers.
