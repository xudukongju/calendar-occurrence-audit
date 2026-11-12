# Why compare occurrences rather than just records?

Research checked 2026-11-12. This is a narrow integration of mature recurrence machinery, not a claim that calendar diff tools do not exist.

## Actual user workflows

- [r/privacy migration comparison request](https://www.reddit.com/r/privacy/comments/1045k1l/): a Thunderbird import stopped at a problematic record. After a partial retry, the author was manually checking days and asked for a Linux comparison utility. The original thread is archived; its suggestion was CSV export plus WinMerge. This is historical direct demand, not proof of a large current market.
- [gcalcli #784](https://github.com/insanum/gcalcli/issues/784): imported updates can be rejected as duplicates, and a manual legacy-import workaround exists. Open at review; later comments discuss unchanged/deleted UIDs. Import confirmation and destination state differ. Our audit reports destination differences; it does not repair the importer.
- [org-caldav recurrence report](https://www.reddit.com/r/emacs/comments/1ilu3km/): end-bounded repeating events became unbounded after conversion. Replies offer an existing expansion script and the author thanks them. This problem has a workaround, and this CLI does not read Org files.
- [Cloudron exception loss](https://forum.cloudron.io/topic/16259/recurring-event-exceptions-recurrence-id-exdate-are-silently-dropped-on-caldav-put): Nov 6 report followed by Nov 8 fix confirmation. Already fixed; not counted as an open defect.

These reports support checking actual post-transfer state, but not a measured market size. No original calendars or private data were copied. The test fixtures are synthetic representations of failure mechanisms.

## Same-input comparisons performed

| Input / question | Existing solution observed | This integration |
|---|---|---|
| One weekly VEVENT loses EXDATE; which meeting reappears? | Guillaume Richard comparer reported 1 present / 0 modified; FindUtils ICS Diff correctly reported EXDATE removed | 2 versus 3 occurrences; lists the extra March 30 meeting |
| Last weekday each month, March–April | FindUtils Expand RRULE returned March 31 and explicitly warned BYSETPOS unsupported | Mature Python engine yields March 31 and April 30 |
| Same embedded TZID changes +0100 to +0200 | CalPorter reported unchanged event record with an explicit timezone-definition warning | Lists actual instant differences |

Links: [Richard comparer](https://grichard.eu/en/tools/ics-compare/), [FindUtils Diff](https://findutils.com/convert/ics-diff/), [FindUtils expansion](https://findutils.com/convert/ics-expand-rrule/), [CalPorter](https://calporter.com/tools/compare-ics/). Browser tools were exercised with synthetic inputs, not inferred only from documentation. Their warnings are useful results, not silent failures. No speed or saved-time percentage was measured.

FindUtils also offers API/MCP access, so scripting alone is not unique. The particular contribution is an offline bounded occurrence comparison using a mature recurrence engine and conservative exit codes. Existing Python libraries can implement this workflow; this project supplies the matching, per-file timezone isolation, failure handling, installation and tests. Field diff remains better for attendees and alarms.

## Important counterexamples discovered during development

A global timezone cache initially reused the first file's definition when reading the second, causing false equality. Per-export timezone providers now honor each embedded definition. Tests cover custom and IANA-named definitions.

Stable recurring-ical-events 3.8.2 failed THISANDFUTURE occurrence identity. Its upstream PR285 already fixed the cause; we pin the tested commit rather than duplicate the patch. Git installation is a real alpha tradeoff.

UID rewriting is not recoverable by this matching contract: unmatched records remain added/removed. A finite window cannot verify an infinite calendar. Missing all data outside the selected window is not detected. These limits appear in the command's output and README.

Additional adversarial check: an unresolved TZID on RDATE was silently treated by the expansion library as an ordinary date. The integration now validates RDATE/EXDATE times before expansion and rejects unresolved/floating values, including period endpoints. This prevents a false equal verdict.
