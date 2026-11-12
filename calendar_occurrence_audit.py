"""Offline calendar audit: compare concrete occurrences in an explicit window.

Uses recurring-ical-events rather than implementing iCalendar recurrence rules.
No calendar edits, networking, fuzzy identity matching or migration writeback.
"""
import argparse
import datetime as dt
import json
import multiprocessing as mp
import math
from pathlib import Path
import sys
import icalendar
from icalendar import timezone
import recurring_ical_events

UTC = dt.timezone.utc
class Inconclusive(ValueError):
    pass

def value_key(value):
    if isinstance(value, dt.datetime):
        if value.tzinfo is None:
            raise Inconclusive('Floating or unresolved time zone: choose a source export with explicit time zones.')
        return 'instant:' + value.astimezone(UTC).isoformat()
    if isinstance(value, dt.date):
        return 'date:' + value.isoformat()
    raise Inconclusive('Unsupported calendar time value')

def expand(text, start, end, limit=10000, series_uids=None):
    if len(text) > 5 * 1024 * 1024:
        raise Inconclusive('Input exceeds 5 MiB')
    # The parser's default global cache can make the second file reuse the first
    # file's custom TZID definition. Honor each export's embedded definitions,
    # including an IANA-named VTIMEZONE, instead of silently applying host tzdata.
    timezone.use_zoneinfo()
    preliminary = icalendar.Calendar.from_ical(text)
    embedded = {str(z['TZID']) for z in preliminary.walk('VTIMEZONE')}
    class ExportZones(timezone.zoneinfo.ZONEINFO):
        def knows_timezone_id(self, name):
            return False if name in embedded else super().knows_timezone_id(name)
        def timezone(self, name):
            return None if name in embedded else super().timezone(name)
    timezone.tzp.use(ExportZones())
    cal = icalendar.Calendar.from_ical(text)
    if cal.name != 'VCALENDAR':
        raise Inconclusive('Expected VCALENDAR')
    identities = set()
    if series_uids is None:
        series_uids = {str(e.get('UID','')) for e in cal.walk('VEVENT') if any(k in e for k in ('RRULE','RDATE','EXDATE','RECURRENCE-ID'))}
    for component in cal.walk():
        if component.errors:
            raise Inconclusive('Calendar contains parse errors')
        if component.name in ('VTODO', 'VJOURNAL', 'VFREEBUSY'):
            raise Inconclusive('Only VEVENT exports are supported; non-event components need separate review')
        if component.name != 'VEVENT':
            continue
        uid = str(component.get('UID', ''))
        if not uid:
            raise Inconclusive('Missing UID; records cannot be matched safely')
        rid = component.get('RECURRENCE-ID')
        key = (uid, value_key(rid.dt) if rid is not None else 'master')
        if key in identities:
            raise Inconclusive('Duplicate UID and RECURRENCE-ID; resolve conflicting records first')
        identities.add(key)
        if 'DTSTART' not in component:
            raise Inconclusive('Event without DTSTART requires manual review')
        for prop in ('DTSTART', 'DTEND', 'RECURRENCE-ID'):
            if prop in component:
                value_key(component[prop].dt)
        for prop in ('RDATE', 'EXDATE'):
            properties = component.get(prop, [])
            if not isinstance(properties, list):
                properties = [properties]
            for dates in properties:
                for entry in dates.dts:
                    value = entry.dt
                    if isinstance(value, tuple):
                        value_key(value[0])
                        if not isinstance(value[1], dt.timedelta):
                            value_key(value[1])
                    else:
                        value_key(value)
    # This query includes occurrences overlapping the window, not only start dates.
    # CLI executes this bounded query in a time-limited child process.
    pages = recurring_ical_events.of(cal, skip_bad_series=False).paginate(
        min(100, limit + 1), earliest_end=dt.datetime.combine(start, dt.time(), UTC),
        latest_start=dt.datetime.combine(end, dt.time(), UTC))
    rows = {}
    count = 0
    for event in (event for page in pages for event in page):
        # The library page stop can include an occurrence exactly at the end.
        start_value = event['DTSTART'].dt
        if isinstance(start_value, dt.datetime):
            if start_value.astimezone(UTC) >= dt.datetime.combine(end, dt.time(), UTC):
                continue
        elif start_value >= end:
            continue
        count += 1
        if count > limit:
            raise Inconclusive('Occurrence limit exceeded; reduce the date window')
        if str(event.get('STATUS', '')).upper() == 'CANCELLED':
            continue
        uid = str(event['UID'])
        rid = event.get('RECURRENCE-ID', event['DTSTART']).dt
        original = value_key(rid) if uid in series_uids else None
        key = (uid, original or 'single')
        if key in rows:
            raise Inconclusive('Expanded occurrence identity is ambiguous')
        rows[key] = {'uid': uid, 'original_start': original,
                     'start': value_key(event['DTSTART'].dt),
                     'end': value_key(event['DTEND'].dt),
                     'summary': str(event.get('SUMMARY', '')),
                     'location': str(event.get('LOCATION', ''))}
    return rows

def audit(before, after, start, end, limit=10000):
    if not start < end:
        raise Inconclusive('The end must be after the start')
    series_uids = set()
    for text in (before, after):
        if len(text) > 5 * 1024 * 1024:
            raise Inconclusive('Input exceeds 5 MiB')
        series_uids.update(str(e.get('UID','')) for e in icalendar.Calendar.from_ical(text).walk('VEVENT')
                           if any(k in e for k in ('RRULE','RDATE','EXDATE','RECURRENCE-ID')))
    left, right = expand(before, start, end, limit, series_uids), expand(after, start, end, limit, series_uids)
    missing = [left[k] for k in sorted(left.keys() - right.keys())]
    added = [right[k] for k in sorted(right.keys() - left.keys())]
    changed = [{'before': left[k], 'after': right[k],
                'fields': [field for field in ('start','end','summary','location') if left[k][field] != right[k][field]]}
               for k in sorted(left.keys() & right.keys()) if left[k] != right[k]]
    return {'status': 'different' if missing or added or changed else 'equal_in_window',
            'window': {'from_inclusive': str(start), 'to_exclusive': str(end), 'timed_zone':'UTC', 'all_day':'calendar dates'},
            'counts': {'before':len(left), 'after':len(right), 'missing':len(missing),'added':len(added),'changed':len(changed)},
            'missing':missing,'added':added,'changed':changed,
            'scope':'Concrete event times, title and location only; no attendee, alarm, attachment or permission audit. Stable UID required; rewritten IDs are not guessed.'}

def read_bounded(path):
    with Path(path).open("rb") as stream:
        data = stream.read(5 * 1024 * 1024 + 1)
    if len(data) > 5 * 1024 * 1024:
        raise Inconclusive("Input exceeds 5 MiB")
    return data

def worker(conn, args):
    try:
        result = audit(read_bounded(args.before), read_bounded(args.after),
                       dt.date.fromisoformat(args.start), dt.date.fromisoformat(args.end), args.max_occurrences)
        conn.send(result)
    except Exception as error:
        # Parse errors may contain private source text; do not dump tracebacks.
        conn.send({'status':'inconclusive','reason':str(error) if isinstance(error, Inconclusive) else 'Could not parse or expand input; no equality conclusion.'})
    finally:
        conn.close()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('before'); parser.add_argument('after')
    parser.add_argument('--from', dest='start', required=True)
    parser.add_argument('--to', dest='end', required=True)
    parser.add_argument('--max-occurrences', type=int, default=10000)
    parser.add_argument('--timeout', type=float, default=20)
    args = parser.parse_args()
    if args.max_occurrences < 1 or not math.isfinite(args.timeout) or args.timeout <= 0:
        parser.error('Limits must be positive')
    ctx=mp.get_context('spawn'); receive, send=ctx.Pipe(duplex=False)
    proc=ctx.Process(target=worker,args=(send,args)); proc.start(); send.close()
    if receive.poll(args.timeout):
        try: result=receive.recv()
        except EOFError: result={'status':'inconclusive','reason':'Expansion process exited without a result'}
    else:
        result={'status':'inconclusive','reason':'Expansion exceeded the time limit; reduce the window'}
        proc.terminate()
    proc.join(); receive.close()
    print(json.dumps(result,ensure_ascii=False,indent=2))
    return {'equal_in_window':0,'different':1,'inconclusive':2}[result['status']]

if __name__ == '__main__':
    sys.exit(main())
