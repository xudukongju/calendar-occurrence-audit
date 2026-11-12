# Review the appointments, not just the import count

Calendar Occurrence Audit is an offline alpha CLI comparing two ICS exports over an explicit window. One recurring VEVENT can represent many appointments: preserving the record count is not enough to preserve the schedule.

The concrete addition over a field diff is a list of missing, added and changed occurrences with UTC-normalized times. Mature `recurring-ical-events` does the expansion; this project adds per-export timezone isolation, identity matching and conservative JSON/exit-code reporting. FindUtils and CalPorter remain useful for broader field inspection, and both detected changes in our baseline comparisons.

Includes synthetic examples, cancellation/moved-exception/BYSETPOS/THISANDFUTURE tests, input limits, timeout handling and private-error suppression. Installation needs Python 3.10+ and Git: an immutable upstream commit is pinned because the published stable dependency still fails one regression. Audits after installation are offline.

Scope: times, titles and locations within the selected window. Review attendees, alarms and permissions separately. Do not delete the source calendar based solely on an equal report.

Author: xudukongju; research, implementation and tests are AI-assisted. External usage and time savings have not been measured.
