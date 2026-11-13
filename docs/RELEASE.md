# Floating 09:00 is not automatically 09:00 UTC

Version 0.2.0a1 adds side-specific `--before-floating-zone` and `--after-floating-zone` assumptions to the offline occurrence audit. Confirm the interpretation used by each calendar, then compare the resulting appointments without rewriting either export. Both assumptions are recorded in JSON.

The new workflow distinguishes three cases: valid floating wall time needing context; an explicit but unresolved TZID that must not be silently repaired; and a daylight-saving gap/fold that needs human review. Known UTC/TZID values and all-day dates keep their original meaning. Defaults retain the previous strict behavior.

A 09:00 floating event can compare equal to Berlin 09:00 under the Berlin assumption, or reveal a time shift when the destination used New York. Recurrence exceptions and local UNTIL values receive the same context. Generated DST ambiguities remain inconclusive. This is conditional auditing, not an importer fix or a guarantee that a guessed zone is correct.

[Research and alternatives](https://github.com/xudukongju/calendar-occurrence-audit/blob/v0.2.0a1/docs/RESEARCH.md). Python/Git installation and the pinned upstream dependency are unchanged. Author: xudukongju; AI-assisted research, implementation and tests. External adoption remains unconfirmed.
