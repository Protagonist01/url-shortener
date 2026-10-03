# QR platform execution roadmap

Repository: [Protagonist01/url-shortener](https://github.com/Protagonist01/url-shortener)
Created: 2026-10-03
Confirmed stack: **FastAPI · PostgreSQL · Next.js**
Status: **8 GitHub milestones and 40 issues published and verified.** No implementation issue is complete merely because existing prototype code exists.

[Milestones](https://github.com/Protagonist01/url-shortener/milestones) · [Issues](https://github.com/Protagonist01/url-shortener/issues) · [Agent rules](../AGENTS.md) · [Performance gates](PERFORMANCE.md) · [Original scope](product-scope.md)

## Delivery strategy
M0 establishes evidence and decisions. M1–M3 deliver the free offline tools, dynamic code service and hosted-page MVP. M4–M6 add paid/pilot/business/developer capabilities after validated demand. M7 is gated expansion; discovery issues do not authorize building every concept.

The source's five phases have been separated into eight milestones so hosted pages and launch readiness have an explicit gate, and advanced artistic work does not block the free core. The source's week ranges are planning ideas, not committed dates. Actual dates require agreed scope, staffing and hosting/capacity decisions.

Existing FastAPI/PostgreSQL/Redis/Celery and QR code are inputs to an audit, not completed milestones. Preserve legacy printed links and uncommitted work. Next.js adoption needs a route/asset/session migration plan.

## Milestones and exit gates
| Order | Milestone | Outcome | Issues |
|---|---|---|---|
| M0 | [Foundation and performance baseline](https://github.com/Protagonist01/url-shortener/milestone/1) | Establish an agreed architecture, reproducible checks, security baseline and measured service budgets before feature expansion. | [#1](https://github.com/Protagonist01/url-shortener/issues/1), [#2](https://github.com/Protagonist01/url-shortener/issues/2), [#3](https://github.com/Protagonist01/url-shortener/issues/3), [#4](https://github.com/Protagonist01/url-shortener/issues/4), [#5](https://github.com/Protagonist01/url-shortener/issues/5) |
| M1 | [Free offline QR foundation](https://github.com/Protagonist01/url-shortener/milestone/2) | Deliver private, account-free static QR tools, conservative styling, scan checks and print-ready exports. | [#6](https://github.com/Protagonist01/url-shortener/issues/6), [#7](https://github.com/Protagonist01/url-shortener/issues/7), [#8](https://github.com/Protagonist01/url-shortener/issues/8), [#9](https://github.com/Protagonist01/url-shortener/issues/9), [#10](https://github.com/Protagonist01/url-shortener/issues/10) |
| M2 | [Dynamic codes and analytics](https://github.com/Protagonist01/url-shortener/milestone/3) | Deliver owned editable codes, resilient redirects, bounded routing and privacy-conscious asynchronous analytics. | [#11](https://github.com/Protagonist01/url-shortener/issues/11), [#12](https://github.com/Protagonist01/url-shortener/issues/12), [#13](https://github.com/Protagonist01/url-shortener/issues/13), [#14](https://github.com/Protagonist01/url-shortener/issues/14), [#15](https://github.com/Protagonist01/url-shortener/issues/15) |
| M3 | [Hosted pages and MVP launch](https://github.com/Protagonist01/url-shortener/milestone/4) | Deliver constrained mobile pages and complete the operational, accessibility, abuse and performance gates for MVP release. | [#16](https://github.com/Protagonist01/url-shortener/issues/16), [#17](https://github.com/Protagonist01/url-shortener/issues/17), [#18](https://github.com/Protagonist01/url-shortener/issues/18), [#19](https://github.com/Protagonist01/url-shortener/issues/19), [#20](https://github.com/Protagonist01/url-shortener/issues/20) |
| M4 | [Pro Brand Studio and first industry pilot](https://github.com/Protagonist01/url-shortener/milestone/5) | Deliver brand workflows, one validated industry pack, reviewed AI page drafts and approved paid entitlements. | [#21](https://github.com/Protagonist01/url-shortener/issues/21), [#22](https://github.com/Protagonist01/url-shortener/issues/22), [#23](https://github.com/Protagonist01/url-shortener/issues/23), [#24](https://github.com/Protagonist01/url-shortener/issues/24), [#25](https://github.com/Protagonist01/url-shortener/issues/25) |
| M5 | [Business governance and trust](https://github.com/Protagonist01/url-shortener/milestone/6) | Deliver teams, multi-location governance, domains, authenticity, wallet passes and selected business connectors. | [#26](https://github.com/Protagonist01/url-shortener/issues/26), [#27](https://github.com/Protagonist01/url-shortener/issues/27), [#28](https://github.com/Protagonist01/url-shortener/issues/28), [#29](https://github.com/Protagonist01/url-shortener/issues/29), [#30](https://github.com/Protagonist01/url-shortener/issues/30) |
| M6 | [Public API and developer platform](https://github.com/Protagonist01/url-shortener/milestone/7) | Deliver governed API keys, batch jobs, signed webhooks, developer SDKs and demonstrated tenant isolation under load. | [#31](https://github.com/Protagonist01/url-shortener/issues/31), [#32](https://github.com/Protagonist01/url-shortener/issues/32), [#33](https://github.com/Protagonist01/url-shortener/issues/33), [#34](https://github.com/Protagonist01/url-shortener/issues/34), [#35](https://github.com/Protagonist01/url-shortener/issues/35) |
| M7 | [Expansion and experimental features](https://github.com/Protagonist01/url-shortener/milestone/8) | Evaluate text updates, offline hosted pages, artistic exports, community blocks and further packs behind evidence gates. | [#36](https://github.com/Protagonist01/url-shortener/issues/36), [#37](https://github.com/Protagonist01/url-shortener/issues/37), [#38](https://github.com/Protagonist01/url-shortener/issues/38), [#39](https://github.com/Protagonist01/url-shortener/issues/39), [#40](https://github.com/Protagonist01/url-shortener/issues/40) |

A stage exits only when all assigned outcomes and applicable quality/performance/security/recovery checks pass. Run heavy workload/failure tests on the approved profile; no unresolved numerical budget gaps are allowed through the MVP release gate. Product decisions stay open until the owner answers them.

## Dependency map and working order
Each issue has scope, acceptance criteria, linked prerequisites and performance verification. The tables below are a snapshot of the initial graph; check the actual GitHub issue before starting. Dependencies govern order inside stages; stage gates govern progression. Ready discovery work can proceed while unrelated owner decisions are pending.

Do not start implementation by checking a feature name off against prototype code. F02 distinguishes working, failing and unverified behavior. Use F01's approved workload/service budgets, not invented latency claims. Keep cached redirects cheap, validate their failure behavior, and budget analytics/rendering separately.

## M0 — Foundation and performance baseline
Establish an agreed architecture, reproducible checks, security baseline and measured service budgets before feature expansion.

| Issue | Outcome | Prerequisites |
|---|---|---|
| [F01 / #1](https://github.com/Protagonist01/url-shortener/issues/1) | Approve architecture, deployment profile and performance budgets | None |
| [F02 / #2](https://github.com/Protagonist01/url-shortener/issues/2) | Audit and reconcile the existing shortener and QR prototype | None |
| [F03 / #3](https://github.com/Protagonist01/url-shortener/issues/3) | Establish reproducible CI and security checks | [F01 / #1](https://github.com/Protagonist01/url-shortener/issues/1), [F02 / #2](https://github.com/Protagonist01/url-shortener/issues/2) |
| [F04 / #4](https://github.com/Protagonist01/url-shortener/issues/4) | Design the tenant-aware data model and safe migration strategy | [F01 / #1](https://github.com/Protagonist01/url-shortener/issues/1), [F02 / #2](https://github.com/Protagonist01/url-shortener/issues/2) |
| [F05 / #5](https://github.com/Protagonist01/url-shortener/issues/5) | Build performance, observability and recovery baselines | [F01 / #1](https://github.com/Protagonist01/url-shortener/issues/1), [F02 / #2](https://github.com/Protagonist01/url-shortener/issues/2) |

## M1 — Free offline QR foundation
Deliver private, account-free static QR tools, conservative styling, scan checks and print-ready exports.

| Issue | Outcome | Prerequisites |
|---|---|---|
| [Q01 / #6](https://github.com/Protagonist01/url-shortener/issues/6) | Build browser-only offline payload generation | [F01 / #1](https://github.com/Protagonist01/url-shortener/issues/1), [F03 / #3](https://github.com/Protagonist01/url-shortener/issues/3) |
| [Q02 / #7](https://github.com/Protagonist01/url-shortener/issues/7) | Build conservative QR styling and preview | [Q01 / #6](https://github.com/Protagonist01/url-shortener/issues/6) |
| [Q03 / #8](https://github.com/Protagonist01/url-shortener/issues/8) | Implement free scannability and print-readiness checks | [Q01 / #6](https://github.com/Protagonist01/url-shortener/issues/6), [Q02 / #7](https://github.com/Protagonist01/url-shortener/issues/7) |
| [Q04 / #9](https://github.com/Protagonist01/url-shortener/issues/9) | Add PNG, SVG and printable card exports | [Q02 / #7](https://github.com/Protagonist01/url-shortener/issues/7), [Q03 / #8](https://github.com/Protagonist01/url-shortener/issues/8) |
| [Q05 / #10](https://github.com/Protagonist01/url-shortener/issues/10) | Complete accessible account-free QR onboarding | [Q01 / #6](https://github.com/Protagonist01/url-shortener/issues/6), [Q02 / #7](https://github.com/Protagonist01/url-shortener/issues/7), [Q03 / #8](https://github.com/Protagonist01/url-shortener/issues/8), [Q04 / #9](https://github.com/Protagonist01/url-shortener/issues/9) |

## M2 — Dynamic codes and analytics
Deliver owned editable codes, resilient redirects, bounded routing and privacy-conscious asynchronous analytics.

| Issue | Outcome | Prerequisites |
|---|---|---|
| [D01 / #11](https://github.com/Protagonist01/url-shortener/issues/11) | Harden accounts, ownership and free-tier quotas | [F03 / #3](https://github.com/Protagonist01/url-shortener/issues/3), [F04 / #4](https://github.com/Protagonist01/url-shortener/issues/4) |
| [D02 / #12](https://github.com/Protagonist01/url-shortener/issues/12) | Implement dynamic-code lifecycle and destination history | [D01 / #11](https://github.com/Protagonist01/url-shortener/issues/11), [F04 / #4](https://github.com/Protagonist01/url-shortener/issues/4) |
| [D03 / #13](https://github.com/Protagonist01/url-shortener/issues/13) | Make redirect resolution resilient and measurable | [D02 / #12](https://github.com/Protagonist01/url-shortener/issues/12), [F05 / #5](https://github.com/Protagonist01/url-shortener/issues/5) |
| [D04 / #14](https://github.com/Protagonist01/url-shortener/issues/14) | Build asynchronous privacy-conscious scan analytics | [D03 / #13](https://github.com/Protagonist01/url-shortener/issues/13), [F04 / #4](https://github.com/Protagonist01/url-shortener/issues/4) |
| [D05 / #15](https://github.com/Protagonist01/url-shortener/issues/15) | Implement bounded routing, expiry and atomic scan limits | [D02 / #12](https://github.com/Protagonist01/url-shortener/issues/12), [D03 / #13](https://github.com/Protagonist01/url-shortener/issues/13), [D04 / #14](https://github.com/Protagonist01/url-shortener/issues/14) |

## M3 — Hosted pages and MVP launch
Deliver constrained mobile pages and complete the operational, accessibility, abuse and performance gates for MVP release.

| Issue | Outcome | Prerequisites |
|---|---|---|
| [P01 / #16](https://github.com/Protagonist01/url-shortener/issues/16) | Build constrained hosted-page schemas, themes and editor | [D01 / #11](https://github.com/Protagonist01/url-shortener/issues/11), [F04 / #4](https://github.com/Protagonist01/url-shortener/issues/4), [Q05 / #10](https://github.com/Protagonist01/url-shortener/issues/10) |
| [P02 / #17](https://github.com/Protagonist01/url-shortener/issues/17) | Implement versioned publish, subdomains and edge caching | [P01 / #16](https://github.com/Protagonist01/url-shortener/issues/16), [D02 / #12](https://github.com/Protagonist01/url-shortener/issues/12), [F05 / #5](https://github.com/Protagonist01/url-shortener/issues/5) |
| [P03 / #18](https://github.com/Protagonist01/url-shortener/issues/18) | Deliver core page blocks and open-status behavior | [P01 / #16](https://github.com/Protagonist01/url-shortener/issues/16), [P02 / #17](https://github.com/Protagonist01/url-shortener/issues/17) |
| [P04 / #19](https://github.com/Protagonist01/url-shortener/issues/19) | Add page media limits, destination previews and abuse response | [P01 / #16](https://github.com/Protagonist01/url-shortener/issues/16), [P02 / #17](https://github.com/Protagonist01/url-shortener/issues/17), [F03 / #3](https://github.com/Protagonist01/url-shortener/issues/3) |
| [P05 / #20](https://github.com/Protagonist01/url-shortener/issues/20) | Pass MVP release, backup restore and printed-link continuity gates | [F03 / #3](https://github.com/Protagonist01/url-shortener/issues/3), [F05 / #5](https://github.com/Protagonist01/url-shortener/issues/5), [Q05 / #10](https://github.com/Protagonist01/url-shortener/issues/10), [D04 / #14](https://github.com/Protagonist01/url-shortener/issues/14), [D05 / #15](https://github.com/Protagonist01/url-shortener/issues/15), [P02 / #17](https://github.com/Protagonist01/url-shortener/issues/17), [P03 / #18](https://github.com/Protagonist01/url-shortener/issues/18), [P04 / #19](https://github.com/Protagonist01/url-shortener/issues/19) |

## M4 — Pro Brand Studio and first industry pilot
Deliver brand workflows, one validated industry pack, reviewed AI page drafts and approved paid entitlements.

| Issue | Outcome | Prerequisites |
|---|---|---|
| [B01 / #21](https://github.com/Protagonist01/url-shortener/issues/21) | Build Brand Studio presets and campaign variants | [Q02 / #7](https://github.com/Protagonist01/url-shortener/issues/7), [Q03 / #8](https://github.com/Protagonist01/url-shortener/issues/8), [P01 / #16](https://github.com/Protagonist01/url-shortener/issues/16), [P05 / #20](https://github.com/Protagonist01/url-shortener/issues/20) |
| [B02 / #22](https://github.com/Protagonist01/url-shortener/issues/22) | Pilot one industry pack with guided onboarding | [B01 / #21](https://github.com/Protagonist01/url-shortener/issues/21), [P03 / #18](https://github.com/Protagonist01/url-shortener/issues/18), [P05 / #20](https://github.com/Protagonist01/url-shortener/issues/20), [F01 / #1](https://github.com/Protagonist01/url-shortener/issues/1) |
| [B03 / #23](https://github.com/Protagonist01/url-shortener/issues/23) | Add scheduling, translation and page-block analytics | [D04 / #14](https://github.com/Protagonist01/url-shortener/issues/14), [P02 / #17](https://github.com/Protagonist01/url-shortener/issues/17), [P03 / #18](https://github.com/Protagonist01/url-shortener/issues/18) |
| [B04 / #24](https://github.com/Protagonist01/url-shortener/issues/24) | Build reviewed AI page setup from approved inputs | [P01 / #16](https://github.com/Protagonist01/url-shortener/issues/16), [P04 / #19](https://github.com/Protagonist01/url-shortener/issues/19), [B02 / #22](https://github.com/Protagonist01/url-shortener/issues/22) |
| [B05 / #25](https://github.com/Protagonist01/url-shortener/issues/25) | Approve pricing and implement paid entitlements | [D01 / #11](https://github.com/Protagonist01/url-shortener/issues/11), [D04 / #14](https://github.com/Protagonist01/url-shortener/issues/14), [P05 / #20](https://github.com/Protagonist01/url-shortener/issues/20), [F01 / #1](https://github.com/Protagonist01/url-shortener/issues/1) |

## M5 — Business governance and trust
Deliver teams, multi-location governance, domains, authenticity, wallet passes and selected business connectors.

| Issue | Outcome | Prerequisites |
|---|---|---|
| [T01 / #26](https://github.com/Protagonist01/url-shortener/issues/26) | Add teams, approvals, audit logs and multi-location templates | [D01 / #11](https://github.com/Protagonist01/url-shortener/issues/11), [D02 / #12](https://github.com/Protagonist01/url-shortener/issues/12), [P01 / #16](https://github.com/Protagonist01/url-shortener/issues/16), [B01 / #21](https://github.com/Protagonist01/url-shortener/issues/21), [B05 / #25](https://github.com/Protagonist01/url-shortener/issues/25) |
| [T02 / #27](https://github.com/Protagonist01/url-shortener/issues/27) | Add verified custom domains and safe domain lifecycle | [P02 / #17](https://github.com/Protagonist01/url-shortener/issues/17), [T01 / #26](https://github.com/Protagonist01/url-shortener/issues/26), [B05 / #25](https://github.com/Protagonist01/url-shortener/issues/25) |
| [T03 / #28](https://github.com/Protagonist01/url-shortener/issues/28) | Add authenticity signatures and cautious anomaly alerts | [D03 / #13](https://github.com/Protagonist01/url-shortener/issues/13), [T01 / #26](https://github.com/Protagonist01/url-shortener/issues/26), [F03 / #3](https://github.com/Protagonist01/url-shortener/issues/3) |
| [T04 / #29](https://github.com/Protagonist01/url-shortener/issues/29) | Implement Apple and Google wallet pass adapters | [T01 / #26](https://github.com/Protagonist01/url-shortener/issues/26), [T03 / #28](https://github.com/Protagonist01/url-shortener/issues/28), [B05 / #25](https://github.com/Protagonist01/url-shortener/issues/25) |
| [T05 / #30](https://github.com/Protagonist01/url-shortener/issues/30) | Implement selected no-code business connectors | [T01 / #26](https://github.com/Protagonist01/url-shortener/issues/26), [D04 / #14](https://github.com/Protagonist01/url-shortener/issues/14), [B02 / #22](https://github.com/Protagonist01/url-shortener/issues/22) |

## M6 — Public API and developer platform
Deliver governed API keys, batch jobs, signed webhooks, developer SDKs and demonstrated tenant isolation under load.

| Issue | Outcome | Prerequisites |
|---|---|---|
| [A01 / #31](https://github.com/Protagonist01/url-shortener/issues/31) | Publish versioned APIs, scoped keys and developer docs | [T01 / #26](https://github.com/Protagonist01/url-shortener/issues/26), [B05 / #25](https://github.com/Protagonist01/url-shortener/issues/25), [P05 / #20](https://github.com/Protagonist01/url-shortener/issues/20) |
| [A02 / #32](https://github.com/Protagonist01/url-shortener/issues/32) | Add bounded bulk, render jobs and data exports | [A01 / #31](https://github.com/Protagonist01/url-shortener/issues/31), [Q03 / #8](https://github.com/Protagonist01/url-shortener/issues/8), [D04 / #14](https://github.com/Protagonist01/url-shortener/issues/14), [F04 / #4](https://github.com/Protagonist01/url-shortener/issues/4) |
| [A03 / #33](https://github.com/Protagonist01/url-shortener/issues/33) | Deliver signed outgoing webhooks with replay controls | [A01 / #31](https://github.com/Protagonist01/url-shortener/issues/31), [D04 / #14](https://github.com/Protagonist01/url-shortener/issues/14), [T05 / #30](https://github.com/Protagonist01/url-shortener/issues/30) |
| [A04 / #34](https://github.com/Protagonist01/url-shortener/issues/34) | Build developer SDKs and a scoped embed designer | [A01 / #31](https://github.com/Protagonist01/url-shortener/issues/31), [A02 / #32](https://github.com/Protagonist01/url-shortener/issues/32), [Q02 / #7](https://github.com/Protagonist01/url-shortener/issues/7), [P01 / #16](https://github.com/Protagonist01/url-shortener/issues/16) |
| [A05 / #35](https://github.com/Protagonist01/url-shortener/issues/35) | Prove platform capacity, noisy-neighbor isolation and usage reconciliation | [A01 / #31](https://github.com/Protagonist01/url-shortener/issues/31), [A02 / #32](https://github.com/Protagonist01/url-shortener/issues/32), [A03 / #33](https://github.com/Protagonist01/url-shortener/issues/33), [A04 / #34](https://github.com/Protagonist01/url-shortener/issues/34), [F05 / #5](https://github.com/Protagonist01/url-shortener/issues/5) |

## M7 — Expansion and experimental features
Evaluate text updates, offline hosted pages, artistic exports, community blocks and further packs behind evidence gates.

| Issue | Outcome | Prerequisites |
|---|---|---|
| [X01 / #36](https://github.com/Protagonist01/url-shortener/issues/36) | Add authenticated text and webhook page updates | [A03 / #33](https://github.com/Protagonist01/url-shortener/issues/33), [T01 / #26](https://github.com/Protagonist01/url-shortener/issues/26), [B03 / #23](https://github.com/Protagonist01/url-shortener/issues/23) |
| [X02 / #37](https://github.com/Protagonist01/url-shortener/issues/37) | Add opt-in offline caching for hosted pages | [P02 / #17](https://github.com/Protagonist01/url-shortener/issues/17), [P04 / #19](https://github.com/Protagonist01/url-shortener/issues/19), [T01 / #26](https://github.com/Protagonist01/url-shortener/issues/26) |
| [X03 / #38](https://github.com/Protagonist01/url-shortener/issues/38) | Evaluate artistic, animated and material-specific QR packs | [Q03 / #8](https://github.com/Protagonist01/url-shortener/issues/8), [Q04 / #9](https://github.com/Protagonist01/url-shortener/issues/9), [A02 / #32](https://github.com/Protagonist01/url-shortener/issues/32) |
| [X04 / #39](https://github.com/Protagonist01/url-shortener/issues/39) | Evaluate community tip blocks and additional industry packs | [T01 / #26](https://github.com/Protagonist01/url-shortener/issues/26), [T05 / #30](https://github.com/Protagonist01/url-shortener/issues/30), [P04 / #19](https://github.com/Protagonist01/url-shortener/issues/19), [B02 / #22](https://github.com/Protagonist01/url-shortener/issues/22) |
| [X05 / #40](https://github.com/Protagonist01/url-shortener/issues/40) | Decide physical-product fulfillment and deferred engines | [B02 / #22](https://github.com/Protagonist01/url-shortener/issues/22), [X03 / #38](https://github.com/Protagonist01/url-shortener/issues/38), [B05 / #25](https://github.com/Protagonist01/url-shortener/issues/25) |

## Source coverage and boundaries
| Source capability | Roadmap coverage |
|---|---|
| Free static types, medical/home cards, no-account privacy | Q01–Q05 |
| Styling, scannability, PNG/SVG/cards/stickers | Q02–Q04; advanced styles B01; server PDF/bulk A02 |
| Accounts, editable codes, history, custom slugs, scan counts | D01–D04 |
| Expiry, scan limits, passwords, fallbacks and device/language/time/region rules | D05 |
| Free hosted page, subdomain, brand theme, core blocks, open status | P01–P04 |
| Safe previews, abuse controls and malicious destinations | P04, T03 |
| Brand kits, seasonal skins, campaign variants, personal/creator templates | B01–B02 |
| Scheduling, translation, block analytics and accessibility | B03 |
| AI menu/profile drafts | B04, with input/provider choice and human review |
| Paid quotas, billing, custom-domain tier ambiguity | B05 before entitlements are assumed |
| Teams, roles, approvals, audit, multi-location and guardrails | T01 |
| Custom code/page domains and continuity | T02 |
| Signed authenticity and qualified tamper/anomaly alerts | T03 |
| Apple/Google wallet | T04, provider prerequisites first |
| POS/commerce, CRM, automation, booking, marketing connectors | T05; prioritize selected adapters, not the entire catalog at once |
| Public code/style/rules/page/analytics/verification API | A01 |
| CSV, render, PDF and bulk jobs, exports | A02 |
| Signed webhooks, sandbox docs, SDKs and embed | A01, A03–A04 |
| Capacity, cost, metering and tenant fairness | F05, B05, A05 |
| Text/webhook page updates and opt-in offline hosted pages | X01–X02 |
| Artistic, AI-scene, animated and physical-medium exports | X03; existing artistic prototype remains experimental |
| Community board, extra packs and feedback/newsletter/intake forms | X04; sensitive-data/privacy decisions first |
| Physical products/print partnerships, built-in checkout/inventory/scheduling, full website/SEO | X05 discovery; remain deferred unless separately approved |

## Open decisions
F01 resolves hosting/provider, regions, peak/sustained load, representative data volumes, infrastructure budget, SLOs, latency percentiles, RPO/RTO, analytics delivery/loss and privacy retention. B02 resolves the first restaurant/facilities pilot; B04 resolves the first AI input/provider; B05 resolves pricing, quotas and custom-domain eligibility. T04/T05/X01 resolve vendor prerequisites and connector order. X04/X05 resolve expansion and partner-versus-build choices. Working product name remains TBD.

No decision above prevents writing requirements or running the existing-code audit. It does prevent dependent implementation from silently inventing requirements.

## Maintaining the roadmap
GitHub holds live status; docs/roadmap/plan.json preserves the initial definitions and stable F/Q/D/P/B/T/A/X keys. Add justified child issues when scope exceeds a cohesive change and link them to the parent/milestone. Do not mark parent outcomes complete while required children remain open. Update this document when milestone scope changes.

The PowerShell publisher is scoped to this repository, reads existing GitHub Git credentials only in memory and saves progress after each successful write:
- Dry-run/local structural validation: ./scripts/publish_roadmap.ps1
- Read-only remote verification: ./scripts/publish_roadmap.ps1 -Verify
- Explicit publication/recovery: ./scripts/publish_roadmap.ps1 -Publish -Verify

Publication checks full paginated issue/milestone lists by stable marker/title and refuses duplicates or wrong milestone assignments. Existing bodies/state are preserved. It does not retry ambiguous POST failures; rerun after checking remote state. Immediately after creation, a list read can be transiently incomplete; use a fresh read before interpreting that as missing data. Verification checks identity, uniqueness, milestone assignment and dependency links, not whether implementation is complete.

## References
- [GitHub milestones](https://docs.github.com/en/issues/using-labels-and-milestones-to-track-work/about-milestones) explain grouping issues into delivery goals.
- [PostgreSQL EXPLAIN](https://www.postgresql.org/docs/16/using-explain.html) grounds query-plan evidence.
- [OWASP API Security](https://api-security.owasp.org/editions/2023/en/0x11-t10/) informs ownership, resource bounds and SSRF requirements.
