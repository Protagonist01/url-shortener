# Owner decisions and prerequisites

Updated: 2026-10-06. The owner asked agents to keep questions here and continue independent work without interrupting. **An unanswered item is not approval.** Enter answers under the stable IDs; agents must reconcile answers with ADRs, issues and this register before dependent work.

Confirmed: FastAPI, PostgreSQL, Next.js; small initial launch with growth; Cloudflare is a hosting candidate. Continuous work through all eight milestones is authorized. This does not select pricing, providers, privacy policy or authorize production deployment/PR merging.

## Foundation decisions — F01 / issue #1

| ID | Input requested | Proposed option / evidence | What waits | Owner answer |
|---|---|---|---|---|
| IN01 | Which architecture/hosting direction should be adopted? | ADR0002 proposes Cloudflare frontend/edge plus CPython containers and managed PostgreSQL. Actual Next.js adapter compatibility remains to be tested | Provider-specific implementation and F01 sign-off | Pending |
| IN02 | What monthly infrastructure spending ceiling and primary audience/data region should be used? | No region/cost ceiling was selected; do not infer audience from the owner's timezone | Paid provisioning, region/cost/SLO tradeoffs | Pending |
| IN03 | May the proposed test profile and latency targets in ADR0002 become the initial benchmark specification? | Proposed 10,000 codes/1M events, 20 RPS sustained/100 RPS burst; warm p95 100 ms/p99 250 ms. These are not measured results | F05 numerical release gate | Pending |
| IN04 | What availability, backup recovery point and recovery time are required? | No uptime/RPO/RTO guarantee is approved. Record backup/restore experiments without inventing acceptable data loss | Recovery/launch gate | Pending |
| IN05 | What analytics lag and loss are acceptable, and how much raw IP/GeoIP data may be retained? | Current code stores raw IP and calls an external provider. Proposal is data minimization; no retention period or provider disclosure approved | Event delivery/retention/privacy-dependent design | Pending |
| IN06 | What is the permitted cache freshness/revocation window and outage behavior for protected/disabled codes? | Current audit found stale cache vs /q behavior. Correctness must hold; no stale-serving exception approved | Cache policy, routing/limits performance budgets | Pending |

## Existing prototype and management policy

| ID | Input requested | Evidence / options | What waits | Owner answer |
|---|---|---|---|---|
| IN07 | How should ownerless legacy links be managed or claimed? Are any analytics intentionally public? | Existing anonymous creation/deletion/analytics need an explicit ownership policy. A public code must not become a management credential | AUD01 / #42 legacy management semantics | Pending |
| IN08 | Which existing uncommitted prototype changes should be reviewed/published as the baseline? | Main now contains the roadmap/audit via merge #50, but the original checkout still has uncommitted QR source, migration, frontend and Build Book changes. Agents preserve them and use an isolated checkout | Clean-clone QR reproduction and migration of the experimental UI; no wholesale publication | Pending |
| IN09 | May reviewed implementation PRs be merged automatically, or should they remain for owner review? | Current AGENTS.md requires applicable merge/deploy authorization. Broad issue execution does not explicitly authorize merge/deployment | Merging; verified code can still be developed/tested/published in PRs | Pending |
| IN10 | Have any active secrets in tracked .env/history been rotated, and who owns rotation? | Tracked file is confirmed; values/activity were not inspected or published. Answers must not include secrets | Verified exposure remediation/rotation, not safe local untracking work | Pending |

## Later-stage choices — record now, request only when relevant

| ID | Input requested | Issue / dependency | What waits | Owner answer |
|---|---|---|---|---|
| IN11 | Product name, public domain and brand direction | Working name TBD; verified domains require owner control | Public identity/domain activation and final branding | Pending |
| IN12 | Free/paid prices, quotas and custom-domain eligibility | B05 / #25; D01 quota ambiguity | Billing and entitlements, numerical quotas | Pending |
| IN13 | First industry pilot and contact/recruitment authorization | B02 / #22, restaurant/facilities candidates | Industry-specific validation and outreach | Pending |
| IN14 | AI provider, input types, spending/data policy and keys availability | B04 / #24 | Provider integration and paid/data-transferring operations | Pending |
| IN15 | Wallet developer accounts, certificates and allowed integrations | T04 / #29 | Real Apple/Google signing and production issuance | Pending |
| IN16 | Prioritized no-code vendors and sandbox account availability | T05 / #30, X01 / #36 | Selected vendor adapters/live verification | Pending |
| IN17 | Sensitive form/community data and moderation policy | X04 / #39 | Community/sensitive-content expansion | Pending |
| IN18 | Physical-product partners and approval for deferred engines | X05 / #40 | Physical fulfillment/checkout/inventory/scheduling expansion | Pending |

## How agents proceed

- Refresh GitHub and the current worktree before picking work. Read actual acceptance criteria and prerequisites.
- Implement independent correctness fixes and prepare reusable interfaces/tests. Record proposed values as proposals. Do not bypass unmet prerequisites merely to advance a milestone.
- Keep parent issues open while mandatory outcomes/child tasks or decisions remain incomplete. Distinguish verified implementation from merged/released behavior.
- Put newly discovered questions here with a stable ID and affected issue. Do not repeatedly ask the same question in chat.
- Never paste credentials, customer records, raw medical payloads or secret values into this file.

References: docs/ROADMAP.md, docs/PERFORMANCE.md, docs/decisions/0002-small-launch-hosting-proposal.md, docs/audits/2026-10-03-foundation.md. GitHub issue status is authoritative; this file records unresolved inputs.
