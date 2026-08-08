# Weather Helper

Personal weather-decision app. Ranks locations and recommends time windows for
outdoor activities (hiking or beach) using MET Norway forecast data. Two UIs
share core logic: a Tkinter desktop app (`src/gui/`) and a Flet Android app
(`src/mobile/`), both built on `src/core/` and `src/application/`.

This is a solo personal project, not an enterprise codebase. Keep changes
direct and proportionate — no process for its own sake.

## Workflow: work on `main`, no feature branches

Commit and push directly to `main` as you go. Don't create branches, don't
open PRs, don't ask for merge approval — this repo has one branch.

**But be deliberate about pushes.** Every push to `main` that touches `**.py`,
`pyproject.toml`, or `.github/workflows/**` triggers `.github/workflows/release.yml`:
the full test suite (Ubuntu + Windows), a Windows executable build, an Android
APK build, and a GitHub release with a bumped version tag. That pipeline is
slow and not free. Don't trigger it per small edit:

- Make your edits, run tests locally, iterate — commit locally as checkpoints
  if useful.
- Push once a task is actually done and tests pass locally, not after every
  file change.
- `workflow_dispatch` exists if a rebuild is ever needed without a code change.

Commit message prefixes affect the release version bump (see the `version`
job): `breaking:` or `[major]` → major bump, `feat:` or `[minor]` → minor
bump, anything else → patch bump.

## Commands

```bash
# Install (editable, with dev deps)
python -m pip install -e ".[dev]"

# Run the full test suite (needs Tk; skip windows_gui marker if headless)
python -m pytest
python -m pytest -m "not windows_gui"   # what CI runs on Ubuntu

# Lint (no configured linter beyond compileall/pyflakes-by-hand)
python -m compileall -q src weather_helper.py weather_helper_mobile.py
python -m pyflakes src tests

# Run the apps locally
python weather_helper.py            # Tkinter desktop
python weather_helper_mobile.py     # Flet mobile (desktop preview)
```

## Architecture notes

- `src/core/scoring.py` — per-hour weighted scoring tables for two activity
  profiles (`ACTIVITY_HIKING`, `ACTIVITY_BEACH_DAY`). Rating word thresholds
  (Poor/Fair/Good/Very Good/Excellent) are *derived* from each profile's
  maximum achievable score (`RATING_FRACTIONS_BY_PROFILE` → `_rating_thresholds`),
  not hardcoded — retuning a range table can never leave a rating unreachable.
- `src/core/evaluation.py` — finds the best contiguous "weather window" per
  day and scores the day-out (ranking) on that window, not the whole-day
  average, with a duration bonus so a longer good stretch beats one perfect hour.
- `get_recommendation_hours()` is the single source of truth for which hours
  count toward a recommendation (daylight, future-only for today) — used
  consistently by ranking, window selection, and the hourly breakdown.
- Scoring is calibrated for the Asturias / Atlantic-Spain coast the app is
  actually used in: rain is a baseline condition, not a disqualifier; hiking
  favors cool over hot and barely penalizes cloud/humidity. See README.md
  "How the scores work" for the full rationale.

## Tests

`tests/test_ranking_calibration.py` encodes scoring judgments in human terms
("a long good window beats a single perfect hour") rather than raw numbers —
prefer extending it over adding another numeric-only assertion when checking
that a scoring change produces sensible real-world behavior.
