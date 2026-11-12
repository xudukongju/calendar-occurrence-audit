import datetime as dt
import unittest
from calendar_occurrence_audit import audit, Inconclusive

def cal(body): return ('BEGIN:VCALENDAR\nVERSION:2.0\n'+body+'END:VCALENDAR\n').encode()
def event(extra='',uid='a',start='DTSTART:20260323T080000Z',end='DTEND:20260323T090000Z'):
 return f'BEGIN:VEVENT\nUID:{uid}\n{start}\n{end}\nSUMMARY:Synthetic\n{extra}END:VEVENT\n'
class Tests(unittest.TestCase):
 def compare(self,a,b):return audit(cal(a),cal(b),dt.date(2026,3,1),dt.date(2026,5,1))
 def test_lost_exdate(self):
  a=event('RRULE:FREQ=WEEKLY;COUNT=3\nEXDATE:20260330T080000Z\n');b=event('RRULE:FREQ=WEEKLY;COUNT=3\n')
  self.assertEqual(self.compare(a,b)['counts']['added'],1)
 def test_equivalent_zone_and_utc(self):
  self.assertEqual(self.compare(event(),event(start='DTSTART;TZID=Europe/Berlin:20260323T090000',end='DTEND;TZID=Europe/Berlin:20260323T100000'))['status'],'equal_in_window')
 def test_moved_override_uses_original_identity(self):
  master=event('RRULE:FREQ=WEEKLY;COUNT=3\n')
  override=event('RECURRENCE-ID:20260330T080000Z\n',start='DTSTART:20260331T080000Z',end='DTEND:20260331T090000Z')
  r=self.compare(master,master+override)
  self.assertEqual(r['counts'],dict(before=3,after=3,missing=0,added=0,changed=1))
 def test_dst_drift(self):
  utc=event('RRULE:FREQ=WEEKLY;COUNT=3\n');zoned=event('RRULE:FREQ=WEEKLY;COUNT=3\n',start='DTSTART;TZID=Europe/Berlin:20260323T090000',end='DTEND;TZID=Europe/Berlin:20260323T100000')
  r=self.compare(zoned,utc);self.assertEqual(r['counts']['missing'],2);self.assertEqual(r['counts']['added'],2)
 def test_cancelled_occurrence(self):
  a=event('RRULE:FREQ=WEEKLY;COUNT=3\n');b=a+event('RECURRENCE-ID:20260330T080000Z\nSTATUS:CANCELLED\n',start='DTSTART:20260330T080000Z',end='DTEND:20260330T090000Z')
  self.assertEqual(self.compare(a,b)['counts']['missing'],1)
 def test_duplicate_does_not_pass(self):
  with self.assertRaises(Inconclusive):self.compare(event()+event(),event())
 def test_unknown_zone_does_not_pass(self):
  with self.assertRaises(Inconclusive):self.compare(event(start='DTSTART;TZID=Missing/Zone:20260323T090000'),event())
 def test_floating_time_does_not_pass(self):
  with self.assertRaises(Inconclusive):self.compare(event(start='DTSTART:20260323T090000'),event())
 def test_all_day_not_equal_midnight_utc(self):
  r=self.compare(event(start='DTSTART;VALUE=DATE:20260323',end='DTEND;VALUE=DATE:20260324'),event(start='DTSTART:20260323T000000Z',end='DTEND:20260324T000000Z'))
  self.assertEqual(r['status'],'different')
 def test_bounded_last_weekday_bysetpos(self):
  a=event('RRULE:FREQ=MONTHLY;BYDAY=MO,TU,WE,TH,FR;BYSETPOS=-1\n',start='DTSTART:20260331T080000Z',end='DTEND:20260331T090000Z')
  self.assertEqual(self.compare(a,a)['counts']['before'],2)
 def test_embedded_zone_changes_do_not_reuse_prior_file_cache(self):
  def definition(offset, name):
   return f'BEGIN:VTIMEZONE\nTZID:{name}\nBEGIN:STANDARD\nDTSTART:19700101T000000\nTZOFFSETFROM:{offset}\nTZOFFSETTO:{offset}\nEND:STANDARD\nEND:VTIMEZONE\n'
  for name in ('Test/Fixed','Europe/Berlin'):
   body=event(start=f'DTSTART;TZID={name}:20260323T090000',end=f'DTEND;TZID={name}:20260323T100000')
   with self.subTest(name=name):
    r=self.compare(definition('+0100',name)+body,definition('+0200',name)+body)
    self.assertEqual(r['status'],'different')
 def test_end_is_exclusive(self):
  a=event(start='DTSTART:20260501T000000Z',end='DTEND:20260501T010000Z')
  self.assertEqual(self.compare(a,a)['counts']['before'],0)
 def test_dense_series_stops_at_limit(self):
  a=cal(event('RRULE:FREQ=SECONDLY\n'))
  with self.assertRaises(Inconclusive):audit(a,a,dt.date(2026,3,23),dt.date(2026,4,1),limit=10)
 def test_window_uses_utc_for_timed_events(self):
  utc=event(start='DTSTART:20260228T230000Z',end='DTEND:20260228T233000Z')
  local=event(start='DTSTART;TZID=Europe/Berlin:20260301T000000',end='DTEND;TZID=Europe/Berlin:20260301T003000')
  r=self.compare(utc,local);self.assertEqual(r['status'],'equal_in_window');self.assertEqual(r['counts']['before'],0)
 def test_rdate_period_retains_its_duration(self):
  a=event('RDATE;VALUE=PERIOD:20260401T080000Z/20260401T110000Z\n')
  b=event('RDATE;VALUE=PERIOD:20260401T080000Z/20260401T100000Z\n')
  r=self.compare(a,b);self.assertEqual(r['counts']['changed'],1);self.assertEqual(r['changed'][0]['fields'],['end'])
 def test_this_and_future_moves_remaining_instances(self):
  a=event('RRULE:FREQ=WEEKLY;COUNT=4\n')
  b=a+event('RECURRENCE-ID;RANGE=THISANDFUTURE:20260330T080000Z\n',start='DTSTART:20260330T100000Z',end='DTEND:20260330T110000Z')
  r=self.compare(a,b);self.assertEqual(r['counts']['changed'],3)
 def test_timezone_definition_after_event(self):
  zone='BEGIN:VTIMEZONE\nTZID:Late/Zone\nBEGIN:STANDARD\nDTSTART:19700101T000000\nTZOFFSETFROM:+0100\nTZOFFSETTO:+0100\nEND:STANDARD\nEND:VTIMEZONE\n'
  a=event(start='DTSTART;TZID=Late/Zone:20260323T090000',end='DTEND;TZID=Late/Zone:20260323T100000')
  self.assertEqual(self.compare(zone+a,a+zone)['status'],'equal_in_window')
 def test_moved_single_matches_by_uid(self):
  r=self.compare(event(),event(start='DTSTART:20260324T080000Z',end='DTEND:20260324T090000Z'))
  self.assertEqual(r['counts'],dict(before=1,after=1,missing=0,added=0,changed=1))
 def test_lost_rule_does_not_report_first_instance_as_missing(self):
  r=self.compare(event('RRULE:FREQ=WEEKLY;COUNT=3\n'),event())
  self.assertEqual(r['counts'],dict(before=3,after=1,missing=2,added=0,changed=0))
 def test_unknown_recurrence_dates_are_inconclusive(self):
  for prop in ('RDATE','EXDATE'):
   with self.subTest(prop=prop), self.assertRaises(Inconclusive):
    self.compare(event(f'{prop};TZID=Unknown/Zone:20260330T090000\n'),event())
 def test_cancelled_master_has_no_occurrences(self):
  a=event('RRULE:FREQ=WEEKLY;COUNT=3\nSTATUS:CANCELLED\n')
  self.assertEqual(self.compare(a,a)['counts']['before'],0)
 def test_event_overlapping_window_is_kept(self):
  a=event(start='DTSTART:20260228T230000Z',end='DTEND:20260301T010000Z')
  self.assertEqual(self.compare(a,a)['counts']['before'],1)
 def test_malformed_recurrence_is_rejected(self):
  with self.assertRaises(Inconclusive):self.compare(event('RRULE:FREQ=NONSENSE\n'),event())
if __name__=='__main__':unittest.main()
