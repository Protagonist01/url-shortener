# Isolated foundation correctness checks

Child [F03a / #55](https://github.com/Protagonist01/url-shortener/issues/55) adds the `Foundation correctness` GitHub workflow. It runs on pull requests and main pushes, with optional manual runs. It uses read-only repository permission, no persisted checkout credential, pinned official action commits, a GitHub-hosted Ubuntu24.04 runner and Python3.12. The 15-minute timeout and 7-day synthetic artifact lifetime are CI safeguards, not production budgets or product retention policy.

## Local reproduction

Use a clean checkout and a virtual environment with Docker available:

```powershell
python -m pip install -r requirements-ci.txt
python -m scripts.verify_configuration --docker
python -m pytest tests/test_worker_registration.py -q --junitxml=output/worker-registration/unit.xml
python -m scripts.verify_worker_registration up
try { python -m scripts.verify_worker_registration verify }
finally { python -m scripts.verify_worker_registration down }
```

The workflow runs the same commands with an `always()` cleanup step. The harness refuses existing names or occupied ports25432/26379, checks ownership labels/loopback bindings before mutation, and seeds only synthetic fixtures. It applies actual Alembic migrations, starts one Celery solo worker and uses one real Scheduler instance to publish a due periodic task. It verifies the resulting PostgreSQL rows and shuts down its own worker. No shared Redis key deletion or external GeoIP request occurs.

Application imports and migration/worker descendants run from empty temporary directories; synthetic settings are supplied explicitly and local `.env` is never needed. Migration script paths resolve to this checkout. The registration unit check does not need a DB/broker. Direct dependencies are pinned; a full transitive lock/security advisory gate is still parent work.

The uploaded artifact directory contains synthetic worker/migration logs, evidence JSON and JUnit. Missing artifacts are reported, not interpreted as successful tests. A clean runner does not contain the owner's production configuration. This job performs no deployment or production settings change.

## Coverage and limitations

This is a correctness gate for registry discovery, actual local broker/scheduler delivery and configuration packaging. It does not run the legacy HTTP API suite, unpublished QR prototype, browser/Next.js checks, lint/types, advisory/history-secret checks, migration rollback/old-new compatibility, restore, load or prefork supervision. Parent [F03 / #3](https://github.com/Protagonist01/url-shortener/issues/3) and all milestone gates remain open.

There is no API/query change or measured latency/capacity improvement. F01/F05 establish performance/recovery budgets and baselines. Before merging, inspect the actual GitHub check for the implementation revision; local passes alone do not meet this child's GitHub-run criterion.

Least-privilege permissions and full-SHA action pinning follow [GitHub's official secure-use guidance](https://docs.github.com/en/actions/reference/security/secure-use).

## Local evidence — 2026-10-06

Windows, Python3.12.13, pytest8.3.4, Celery5.4.0, Docker29.7.2: one registration test passed (10.46s), Git/template/synthetic actual Docker boundaries passed, migrations and real worker/scheduler delivery passed with counts4/2 and interval3600 preserved. The helper changes are on base e3a97a84a2040a89976d87c0787a7d2c3e010e0e; see the implementation PR for the final revision. Raw synthetic logs/JUnit/evidence remain ignored under output/worker-registration.

Initial verification was started before fixture startup completed and refused missing services. Startup also exposed Windows's inability to delete the current working directory; the helper now restores its prior cwd in finally. Those attempts were failed checks. The passing sequence used freshly created owned fixtures after cleanup. A separate system Python3.13 unit pass is not the declared baseline. No GitHub/Linux success is claimed here before its actual job completes.

## Actual GitHub evidence — 2026-10-06

[PR #56](https://github.com/Protagonist01/url-shortener/pull/56) head `840d64322f4b951395a4c64acb677cbaaf6d018a` passed [run37521244163 / job112466887529](https://github.com/Protagonist01/url-shortener/actions/runs/37521244163/job/112466887529). The API reports pull_request event, completed/success for this head. Checked every step: dependency install, configuration boundaries, unit regression, owned service startup, migrations/real worker delivery, cleanup and artifact upload all succeeded. The foundation-verification artifact exists (2396 bytes at verification, not expired).

This supersedes the earlier pending GitHub status. Reviewed PR56 merged as `bad860b57261b5225eaf9a033b40a5a4ae1ac08e`, and GitHub closed child55. Parent3 and milestone gates remain open. The job proves Linux solo correctness for these checks, not prefork/load/full-security readiness. GitHub schedules a separate main-push run after merge; verify that run independently rather than inferring its result from the PR job.
