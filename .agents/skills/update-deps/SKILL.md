---
name: update-deps
description: Update the locked dependencies of PTPlot with uv, after verifying that the working tree is clean and the latest commit has passed CI, and then fix any issues found by the linters, the unit tests and the documentation build. Use when the user asks to update, upgrade or bump the dependencies or uv.lock.
---

# Update the dependencies

Follow these steps in order. When a step says **stop**, report the reason to the user and end the skill
without doing any of the later steps.

## 1. Check for uncommitted changes

Run `git status --porcelain -- . ':!.claude'`.
If it prints anything (modified, staged or untracked files), **stop**
and list the uncommitted changes to the user.

## 2. Check that the latest commit has passed CI

The CI workflow is `.github/workflows/main.yml` with the name `CI`, and it runs on every push.
The repository is `CFT-HY/PTPlot` (verify with `git remote get-url origin`).

1. Get the latest commit with `git rev-parse HEAD` and the current branch with `git branch --show-current`.
2. Find the CI workflow runs of that commit.
   - If the GitHub plugin (`mcp__github__*` tools) provides a tool for listing GitHub Actions workflow runs
     (e.g. `actions_list` or `list_workflow_runs`), use it. Load it with ToolSearch if it is deferred.
     (As of 2026-09, the plugin does not have the Actions toolset enabled, so the fallback is usually needed.)
   - Otherwise, fall back to the GitHub CLI:
     `gh run list --workflow CI --commit <sha> --json databaseId,status,conclusion,url,createdAt`
   - If neither works, fall back to the REST API:
     `gh api "repos/CFT-HY/PTPlot/actions/workflows/main.yml/runs?head_sha=<sha>"`
3. Act on the most recent run:
   - `completed` with conclusion `success`: continue to step 3.
   - `completed` with any other conclusion (`failure`, `cancelled`, `timed_out`, etc.):
     **stop** and give the user the URL of the run, the names of the failed jobs and steps
     (`gh run view <id> --json jobs --jq '.jobs[] | select(.conclusion == "failure")'`),
     and the cause of the failure from the logs (see below).
   - `queued` or `in_progress`: wait for it to finish (see below) and then act on its conclusion.
   - No run exists: the commit has most likely not been pushed. Check with `git status -sb`
     whether the branch is ahead of its upstream.
     Before asking about the push, check the most recent CI run of the branch
     (`gh run list --workflow CI --branch <branch> --limit 1 --json databaseId,headSha,conclusion,url`).
     If it failed, find the cause from its logs, as the same failure is likely to happen again,
     unless the unpushed commits fix it. Include this in the question.
     Ask the user for permission to run `git push` (use AskUserQuestion). If the user declines, **stop**.
     If the user agrees, run `git push` (or `git push -u origin <branch>` if there is no upstream),
     wait for the CI run of the commit to appear and to finish, and then act on its conclusion.
     If the push does not create a CI run within a few minutes, **stop** and tell the user.

To wait for a run, use `gh run watch <id> --exit-status` in the background (`run_in_background: true`),
as the CI can take several minutes. Do not poll with short sleeps.

To find the cause of a failure, use `gh run view <id> --log-failed | tail -n 100`.
If it prints nothing, which can happen e.g. when a step failed during setup,
get the log of the failed job from the REST API instead:
`gh api repos/CFT-HY/PTPlot/actions/jobs/<job_id>/logs | grep -iE -B5 -A20 "error|fail"`.

## 3. Update the dependencies

The dependencies in `[project] dependencies` and in the `dev` and `docs` groups of `[dependency-groups]`
in `./pyproject.toml` have only lower bounds (`>=`), so `uv lock --upgrade` upgrades them to the latest versions.
The exception is PTtools, which is installed from the Git commit in `[tool.uv.sources]`.
The version in its `pttools-gw[...] == X` pin in `[project] dependencies` must match the version of that commit.

1. Update PTtools:
   1. Get the latest commit of the `dev` branch with `git ls-remote https://github.com/CFT-HY/pttools.git refs/heads/dev`.
      PTPlot follows the `dev` branch of PTtools, not the default branch `main`, which can be hundreds of commits behind.
   2. Verify that the new commit is a descendant of the current `rev`, so that PTtools is not downgraded:
      `gh api repos/CFT-HY/pttools/compare/<current rev>...<new commit> --jq '{status, ahead_by, behind_by}'`
      must give the status `ahead` (or `identical`, if PTtools is already up to date).
      If the status is `behind` or `diverged`, **stop** and tell the user.
   3. List the new commits with
      `gh api repos/CFT-HY/pttools/compare/<current rev>...<new commit> --jq '.commits[] | "\(.sha[0:8]) \(.commit.message | split("\n")[0])"'`.
      PTPlot computes its results with PTtools, so tell the user explicitly about the new commits
      that change the physics of PTtools, e.g. equations, reference values or default parameters.
      Update the `rev` in the `[tool.uv.sources]` section of `./pyproject.toml`.
   4. Get the version of PTtools at that commit from
      `https://raw.githubusercontent.com/CFT-HY/pttools/<commit>/pyproject.toml`,
      and update the `pttools-gw[...] == X` pin to it, if it has changed.
2. Run `uv lock --upgrade` to upgrade the locked versions in `uv.lock` to the latest versions
   allowed by `pyproject.toml`.
3. Run `./install_requirements.sh` to install them into `.venv`.
   (PTPlot has no optional dependencies, and the `dev` and `docs` groups are installed by default.)
4. Show the user a summary of the version changes, e.g. from `git diff pyproject.toml uv.lock`
   (`uv lock --upgrade` also prints them).
   If nothing changed, tell the user that the dependencies are already up to date and **stop**.
5. Check with `uv tree --outdated --depth 1 --all-groups | grep latest` that no direct dependency was held back.
   If one was (e.g. because another dependency requires an older version), mention it to the user.
6. For each new major version of a direct dependency (e.g. `django-debug-toolbar` 6 → 8),
   check its changelog for breaking changes that affect PTPlot, and mention the major upgrades to the user.

Do not loosen or remove the lower bounds in `pyproject.toml` to get newer versions,
and do not raise them unless it is needed, e.g. to require a version with a fix that PTPlot relies on.
If a constraint prevents an upgrade that seems important, mention it to the user instead.

## 4. Run the checks and fix the issues

Run these checks one at a time, in this order:

1. `./lint.sh` (~2 min)
2. `uv run pytest` (~10 min, run in the background)
3. `uv run make -C docs all-noplot` (~5 min, run in the background).
   This builds the documentation without running the examples, and checks the external links (`linkcheck`),
   which requires network access.

Redirect the output of the long checks to a log file in the scratchpad directory
and inspect its tail afterwards, as the output is very long.
Save the exit code of the check itself (e.g. `cmd > log 2>&1; code=$?; tail log; exit $code`),
as piping to `tail` would hide a failure.

For each check:
- If it passes, move on to the next check.
- If it fails, investigate the cause, fix it, and re-run the check until it passes before moving on.
  - Prefer fixing the code of PTPlot to work with the new dependency versions.
    If a failure is caused by a bug or regression in a dependency, exclude the broken version in `pyproject.toml`
    (e.g. `"package >= X, != Y"`) with a comment linking to the upstream issue.
    Then re-run `uv lock` and `./install_requirements.sh`, and tell the user.
  - Follow the instructions of `AGENTS.md`, e.g. that physics code must be covered by unit tests before editing it,
    and that any changes to the physics must be reported to the user explicitly.
  - Do not disable, skip or weaken tests or lint rules to make the checks pass, unless the user agrees.
  - If `pyrefly` reports new errors, find out which upgrade causes them by re-running it with the old version
    of pyrefly and of each upgraded stub package (e.g. `django-stubs`, `pandas-stubs` and `scipy-stubs`) in turn:
    `uv run --with <package>==<old> pyrefly check --output-format min-text`.
    The errors caused by stricter stubs often indicate that PTPlot's own type annotations are inaccurate,
    so prefer fixing the annotations over suppressing the errors.
    Follow the conventions in the docstring of `.venv/lib/python*/site-packages/pttools/type_hints.py`:
    prefer targeted `# pyrefly: ignore[<code>]` comments over `typing.cast()` in `@njit` functions,
    as Numba cannot compile `typing.cast()`.
  - If a type checker reveals a real bug, do not fix it silently if the fix changes the behavior of the code.
    Report it to the user instead.
  - If you cannot fix a failure, **stop** and report the failure and what you tried to the user.

If you made any changes to the files other than `uv.lock` during this step,
re-run all three checks at the end with the final version of the code, and ensure that all of them pass.
A check that has already passed after the last change to the files does not need to be re-run.
If a check fails, fix it and repeat the full set of checks.

## 5. Report

Summarize to the user:
- the upgraded packages and their old and new versions,
- the issues found by each check and how they were fixed,
- the final results of all three checks.

Do not commit or push the changes unless the user asks you to.
