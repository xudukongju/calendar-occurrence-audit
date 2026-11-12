# Calendar Occurrence Audit

After importing a calendar, compare the source export with a fresh destination export: **which concrete appointments disappeared, appeared, or changed within your chosen dates?**

This offline Python CLI expands recurring events with `recurring-ical-events`, normalizes timed events to UTC, and compares stable identities. It does not connect to accounts or change calendars. Alpha; use the report to review a migration before removing the original calendar.

## Install and try

Python 3.10+ and Git are required. From this source checkout:

```sh
python -m venv .venv
# macOS/Linux
. .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
python -m pip install .
calendar-occurrence-audit examples/before-exdate.ics examples/after-exdate.ics --from 2026-03-01 --to 2026-05-01
```

The sample loses an exception date: the report identifies one newly appearing appointment, not merely a changed EXDATE field. Exit status is **1**, meaning differences were found; it is not an installation error.

```sh
calendar-occurrence-audit source.ics destination.ics --from 2026-01-01 --to 2027-01-01 > report.json
```

- **0**: compared fields agree inside this window.
- **1**: differences; inspect `missing`, `added`, and `changed` in JSON.
- **2**: inconclusive or invalid invocation; fix the input or use a smaller window before drawing conclusions.

The window includes overlapping events, with an exclusive end. Timed boundaries are UTC midnight; all-day boundaries are calendar dates. Default limits: 5 MiB per input, 10,000 expanded occurrences per input, 20 seconds per audit. `--max-occurrences` and `--timeout` change the latter two.

## When this helps

A recurring series can still be one VEVENT after dozens of appointments are lost. A field-level diff can correctly detect a rule change without showing its consequences. Here, dropping an EXDATE produces a concrete added date; a moved exception is paired with its original recurrence identity; equivalent UTC and zoned timestamps do not become false changes.

For inspecting **all ICS fields**, use [FindUtils ICS Diff](https://findutils.com/convert/ics-diff/) or [CalPorter](https://calporter.com/tools/compare-ics/). Both detected important changes in our comparisons. This CLI adds bounded occurrence consequences and machine-readable exit codes; it is not a replacement for their broader field inspection. [Evidence and comparison](docs/RESEARCH.md).

## Interpretation and limits

Only start/end, title and location are compared. Attendees, descriptions, alarms, attachments, permissions, and dates outside the window still require review. Equal empty windows do not prove an entire migration succeeded. Rewritten UIDs appear as removed/added; there is no guessed fuzzy pairing. Changes to a recurrence schedule can similarly appear as removed/added identities.

Floating/unresolved time zones, conflicting duplicate identities, unsupported components, parse failures and resource limits produce an inconclusive result, never a successful equality verdict. Embedded VTIMEZONE definitions take precedence over host definitions. Output contains event details: keep reports private and redact before posting an issue. Inputs remain unchanged.

## Dependency decision

The alpha pins upstream `recurring-ical-events` commit `7a0bd1d637e4afec389f9b9f32b336020e98634d`. Published 3.8.2 failed our THISANDFUTURE identity test; upstream already fixed it in [PR 285](https://github.com/niccokunzmann/python-recurring-ical-events/pull/285). We reuse that fix instead of forking recurrence logic or dropping the test. Installation therefore needs Git/network access; installed audits run offline. A later version can adopt a stable upstream release after the same regression checks.

Our code is MIT; separately installed dependencies retain their own licenses, including upstream's LGPL-3.0-or-later. No dependency source is vendored. Created under xudukongju with AI-assisted research, implementation and testing; no external adoption is claimed.

## Development

```sh
python -m pip install . build
python -m unittest discover -s tests -v
python -m build
```
