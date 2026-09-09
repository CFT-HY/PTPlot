For developers
==============

Developing a new feature
------------------------
Create a new feature branch in the repo.
If you don't have permissions to create a branch in the repo,
you can either request the permissions or create a fork.


Developing a hotfix
-------------------
Small bugfixes and improvements can be done in a separate hotfix branch.
This branch should be merged to main without squashing.


Creating a new release
----------------------
Update the PTPlot version number in:

- CITATION.cff
- codemeta.json
- pyproject.toml


Updating Python version requirements
------------------------------------
When updating the Python version requirements,
update the version numbers in:

- .github/workflows/\*.yml
- .readthedocs.yaml
- Dockerfile
- pyproject.toml


Nightly runs
------------
The `nightly.sh` script runs the unit tests, builds the documentation
(which also runs the examples) and archives the results with 7-Zip:

- the figures from `./examples/fig` to `./examples/fig_YYYY-MM-DD.7z`
- the documentation from `./docs/_build` to `./docs/nightly/docs_YYYY-MM-DD.7z`

It logs to `./logs/nightly_YYYY-MM-DD.log`.
The run is skipped if the HEAD commit is older than 24 hours,
so that unchanged code is not rebuilt every night.
The maximum age of the commit can be adjusted with the `MAX_COMMIT_AGE`
environment variable, which is given in seconds.

To run the script every night at 2 AM, open the crontab of your user

```bash
crontab -e
```

and add the following lines, where ``REPO_PATH`` is the path to the PTPlot repository.
Cron runs commands with a minimal environment, so the paths and the shell are set explicitly.
The `flock` prevents a new run from starting if the previous one is still going on,
and the `MAILTO` sends the output of a failed run by email, if a mail transfer agent is configured.
Remove the `MAILTO` line if you don't want these emails.

```
SHELL=/bin/bash
PATH=/usr/local/bin:/usr/bin:/bin
MAILTO=your.email@example.com

0 2 * * * flock -n /REPO_PATH/nightly.lock /REPO_PATH/nightly.sh
```

The cron daemon uses the local time zone of the system, which can be checked with `timedatectl`.
The scheduled jobs can be listed with `crontab -l`.
