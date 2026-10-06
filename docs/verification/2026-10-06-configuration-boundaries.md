# Configuration boundary verification — 2026-10-06

Scope: [AUD02a / #53](https://github.com/Protagonist01/url-shortener/issues/53), child of [AUD02 / #43](https://github.com/Protagonist01/url-shortener/issues/43). Base application: worker commit `78396bc462cd0f8999fd6ffbe2fc885cf94c5eed`, now merged through [PR #52](https://github.com/Protagonist01/url-shortener/pull/52). These checks establish future repository/build boundaries, not historical credential removal.

## Reproduce

From this branch with the pinned Python requirements installed:

```powershell
python -m scripts.verify_configuration
python -m scripts.verify_configuration --docker
git diff --check
git ls-files -- .env
Test-Path -LiteralPath .env
```

The last two checks report no tracked `.env` and `True` for the existing local file in this worktree. A fresh clone need not have a local `.env`; copy the public example as described in README. The verifier never requires one. Do not display the deleted file's patch or read private values to reproduce this check.

## Observed evidence

- Before the index/ignore changes, the checker failed because `.env` was tracked.
- After changes, Git index and ignore checks passed for root and nested private names; the public example remains tracked and trackable.
- The fake public example satisfies the application's required settings and PostgreSQL driver normalization. The subprocess runs from an empty temporary working directory with the repository on PYTHONPATH, so the relative dotenv lookup cannot read the real file. No database, broker or external service connections are opened.
- Docker Desktop engine 29.7.2: an actual `FROM scratch` / `COPY` build with the repository's `.dockerignore` and only synthetic fixtures passed. Root/nested dotenv files, Git, virtualenv and output markers were absent; the allowed application fixture was copied. No real repository configuration was submitted to Docker. Temporary fixtures were removed; no image or service container was created.
- `.env` stays on the local filesystem while `git rm --cached -- .env` removes its index entry. The original dirty checkout and its separate index are unchanged by that command.

The first Docker assertion falsely included its own ancestor `output` directory. Inspecting exported paths relative to the copied context fixed the checker; the actual build was rerun and passed. Review also found that environment overrides alone do not prevent dotenv file reads; the empty-directory subprocess replaced that approach before the final passing check.

## Limits and performance

No request routes, queries, cache policies or worker timings change. There is no API/database performance claim or load test for this configuration-only fix. Public placeholders must be replaced for local operation; they are not production credentials. No provider, production secret store, deployment or credential rotation is selected here.

Historical Git commits can still contain the previously tracked file. Active exposure and rotation remain unresolved in INPUT_REQUIRED.md; parent #43 also retains password hashing/session work. This child does not certify the repository's whole history or application as secret-free or production-ready.

Docker context behavior follows the [official Docker build-context documentation](https://docs.docker.com/build/concepts/context/). Historical cleanup and credential handling are separate work described in [GitHub's sensitive-data guidance](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository).
