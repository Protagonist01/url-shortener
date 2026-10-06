# Dependency advisory baseline

Scope: [F03b / #58](https://github.com/Protagonist01/url-shortener/issues/58), a discovery child of [F03 / #3](https://github.com/Protagonist01/url-shortener/issues/3). The published Python requirements are scanned against real advisory data with pip-audit2.10.1 and a recorded resolved transitive set. Findings require linked remediation; this is not a security approval.

## Reproduce

Create a separate Python3.12 virtualenv, install requirements-audit.txt from public PyPI, and run `python -m scripts.audit_dependencies` from the checkout with that environment's interpreter. Disable pip configuration with PIP_CONFIG_FILE=os.devnull when installing isolated tooling; the helper itself strips PIP_* settings and disables pip configuration before resolution. It imports no application configuration and reads no local dotenv files.

The helper writes platform-specific baseline JSON, metadata and scanner log under ignored output/dependency-audit. It resolves application requirements, including platform-selected transitives, with the real PyPI advisory service. There is no --fix or ignored finding. Return0 means no known findings in that scanned set;1 means known vulnerabilities were recorded;2 means the audit failed or coverage is incomplete. Empty/skipped reports and exit/report disagreement are errors.

The GitHub `Dependency advisory evidence` workflow runs a clean Linux/Python3.12 counterpart with read-only credentials and pinned official action SHAs. Its purpose is to collect a baseline: known findings remain visible in the report and log and do not become accepted release exceptions. A successful collection job is not a clean-security result. Operational code2 fails the job. F03's enforcing security gate and remediation remain open. Synthetic artifact lifetime is7 days, a CI safeguard rather than product retention policy.

## Current evidence

Base source: ddddc5175e3dbd9c3bac8ac73b13a8eaa1f53c50. Local tooling setup initially failed with a CacheControl/filelock resolution error after public PyPI read timeouts. This is an incomplete scan, not a vulnerability verdict. An actual Windows/Linux result and primary-source mapping will be recorded after their commands complete.

Tool behavior: [PyPA pip-audit](https://github.com/pypa/pip-audit); configuration isolation: [official pip configuration](https://pip.pypa.io/en/stable/topics/configuration/).

## Limits and performance

No routes, queries, data or runtime pins change in the evidence step; there is no latency/capacity claim. Advisory databases change with time, so preserve scan date, requirements hash and exact resolved versions. A clean resolved set does not prove every platform's set, production installation, unpublished QR prototype, frontend/native image/system dependencies or exploitability. Scanner tool dependencies are separate from application findings. Secret-history/credential rotation and all parent/milestone release gates remain open.
