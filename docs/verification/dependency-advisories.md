# Dependency advisory baseline

Scope: [F03b / #58](https://github.com/Protagonist01/url-shortener/issues/58), a discovery child of [F03 / #3](https://github.com/Protagonist01/url-shortener/issues/3). The published Python requirements are scanned against real advisory data with pip-audit2.10.1 and a recorded resolved transitive set. Findings require linked remediation; this is not a security approval.

## Reproduce

Create a separate Python3.12 virtualenv, install requirements-audit.txt from public PyPI, and run `python -m scripts.audit_dependencies` from the checkout with that environment's interpreter. Disable pip configuration with PIP_CONFIG_FILE=os.devnull when installing isolated tooling; the helper itself strips PIP_* settings and disables pip configuration before resolution. It imports no application configuration and reads no local dotenv files.

The helper writes platform-specific baseline JSON, metadata and scanner log under ignored output/dependency-audit. It resolves application requirements, including platform-selected transitives, with the real PyPI advisory service. There is no --fix or ignored finding. Return0 means no known findings in that scanned set;1 means known vulnerabilities were recorded;2 means the audit failed or coverage is incomplete. Empty/skipped reports and exit/report disagreement are errors.

The GitHub `Dependency advisory evidence` workflow runs a clean Linux/Python3.12 counterpart with read-only credentials and pinned official action SHAs. Its purpose is to collect a baseline: known findings remain visible in the report and log and do not become accepted release exceptions. A successful collection job is not a clean-security result. Operational code2 fails the job. F03's enforcing security gate and remediation remain open. Synthetic artifact lifetime is7 days, a CI safeguard rather than product retention policy.

## Current evidence

Base source: ddddc5175e3dbd9c3bac8ac73b13a8eaa1f53c50. Local tooling setup initially failed with a CacheControl/filelock resolution error after public PyPI read timeouts. This is an incomplete scan, not a vulnerability verdict. An actual Windows/Linux result and primary-source mapping will be recorded after their commands complete.

### Verified Linux baseline

PR59 head5db24d0015bcd2838b6f7e34c7760f4271e6fbe3 passed [actual advisory collection run37525390386/job112480968985](https://github.com/Protagonist01/url-shortener/actions/runs/37525390386/job/112480968985) and [foundation correctness run37525390328/job112480983369](https://github.com/Protagonist01/url-shortener/actions/runs/37525390328/job/112480983369). The advisory artifact reports Python3.12.14/Linux, pip-audit2.10.1,61 resolved packages with no skips,5 vulnerable packages and35 raw records, with scanner exit1/result known_vulnerabilities. Its source_head73bd7e5 is the PR merge checkout, not the branch head; metadata preserves both identities through the run/PR references.

The [sanitized exact resolved baseline](../security/dependency-baseline-linux.json), [metadata](../security/dependency-baseline-linux-metadata.json) and [18 unique package/advisory-ID mappings](../security/dependency-triage.md) preserve aliases/candidate fixes. Duplicates were not hidden;35 records and18 unique IDs are not a verified count of distinct exploitable bugs. The successful job means evidence collection worked while known vulnerabilities remain.

| Packages | Linked remediation | Static applicability / limits |
|---|---|---|
| python-jose3.3.0 and ecdsa0.19.2 | [DEP01 / #60](https://github.com/Protagonist01/url-shortener/issues/60) | Current code uses HS256, not JWE/ECDSA; no finding waiver or exploitability certification |
| Starlette0.41.3 and python-multipart0.0.20 | [DEP02 / #61](https://github.com/Protagonist01/url-shortener/issues/61) | Static delivery exists; clean-main and future published upload/parser contracts require regression evidence |
| pytest8.3.4 | [DEP03 / #62](https://github.com/Protagonist01/url-shortener/issues/62) | Test tool currently appears in production requirements; both scopes need repair |

No fix candidate is adopted by this evidence PR. Every recorded finding maps to these issues; parent3 and release gates remain open. Local scanner installation succeeded unchanged on retry. A too-early local command failed before installation completed; the ordered Windows scan is still pending, so no Windows coverage claim is made yet.

The first ordered Windows scan ended with temporary-directory PermissionError and no valid baseline. The revised runner logs directly to an owned file, waits at most300 seconds, stops only its own Popen descendants with pinned psutil7.2.2, and keeps descendant temporary files inside the verified owned directory. Operational failures return2 and write a separate failure JSON. A real process-tree test checks that a separate sentinel survives; it runs in Linux CI too. The next Windows scan uses this revised runner; coverage remains incomplete until its actual result is read. All18 canonical PyPA links returned200 and contained their expected IDs at verification.

### Final runner verification

On head `50f6bc0e2e630bf942e676ca77b763ded657f1a0`, actual [Linux advisory run37527373512/job112487687740](https://github.com/Protagonist01/url-shortener/actions/runs/37527373512/job/112487687740) and [correctness run37527373523/job112487687993](https://github.com/Protagonist01/url-shortener/actions/runs/37527373523/job/112487687993) succeeded. The revised real process-tree check also passed locally (one unittest,2.105s): its descendant was stopped and a separate sentinel survived.

The ordered Windows rerun terminated as an incomplete audit: its ignored scanner log records a real PyPI HTTPS ReadTimeout (15s), and failure JSON reports RuntimeError at2026-10-06T20:37:10Z. There is no valid Windows baseline. The operational failure stayed separate from known findings; no repeated unbounded network retries or fabricated coverage. Rerun `output/dependency-audit/tools/Scripts/python.exe -m scripts.audit_dependencies` from the checkout when PyPI connectivity improves, after installing requirements-audit.txt. Actual Linux evidence and the canonical mapping meet this discovery child's scope; Windows/full-security/production install coverage is not inferred.

Tool behavior: [PyPA pip-audit](https://github.com/pypa/pip-audit); configuration isolation: [official pip configuration](https://pip.pypa.io/en/stable/topics/configuration/).

## Limits and performance

No routes, queries, data or runtime pins change in the evidence step; there is no latency/capacity claim. Advisory databases change with time, so preserve scan date, requirements hash and exact resolved versions. A clean resolved set does not prove every platform's set, production installation, unpublished QR prototype, frontend/native image/system dependencies or exploitability. Scanner tool dependencies are separate from application findings. Secret-history/credential rotation and all parent/milestone release gates remain open.
