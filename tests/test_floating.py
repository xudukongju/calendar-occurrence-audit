import datetime as dt
import unittest
from test_audit import cal,event
from calendar_occurrence_audit import audit,Inconclusive
class FloatingTests(unittest.TestCase):
 def run_case(self,a,b,**kw): return audit(cal(a),cal(b),dt.date(2026,3,1),dt.date(2026,12,1),**kw)
 def floating(self,extra='',date='20260323',time='090000'):
  return event(extra,start=f'DTSTART:{date}T{time}',end=f'DTEND:{date}T100000')
 def test_before_explicit_assumption(self):
  r=self.run_case(self.floating(),event(),before_floating_zone='Europe/Berlin')
  self.assertEqual(r['status'],'equal_in_window');self.assertEqual(r['floating_time_assumptions']['before'],'Europe/Berlin')
 def test_defaults_still_reject(self):
  with self.assertRaises(Inconclusive):self.run_case(self.floating(),self.floating())
 def test_side_specific_zones_reveal_shift(self):
  r=self.run_case(self.floating(),self.floating(),before_floating_zone='Europe/Berlin',after_floating_zone='America/New_York')
  self.assertEqual(r['counts']['changed'],1)
 def test_explicit_times_are_not_reinterpreted(self):
  self.assertEqual(self.run_case(event(),event(),before_floating_zone='Asia/Tokyo')['status'],'equal_in_window')
 def test_unknown_tzid_not_repaired(self):
  a=event(start='DTSTART;TZID=Typo/Zone:20260323T090000')
  with self.assertRaises(Inconclusive): self.run_case(a,a,before_floating_zone='UTC',after_floating_zone='UTC')
 def test_unknown_assumption(self):
  with self.assertRaises(Inconclusive):self.run_case(self.floating(),event(),before_floating_zone='Typo/Zone')
 def test_gap_and_fold_rejected(self):
  for day in ('20260329','20261025'):
   with self.subTest(day=day),self.assertRaises(Inconclusive):
    self.run_case(self.floating(date=day,time='023000'),event(),before_floating_zone='Europe/Berlin')
 def test_generated_dst_gap_rejected(self):
  with self.assertRaises(Inconclusive):
   self.run_case(self.floating('RRULE:FREQ=DAILY;COUNT=3\n',date='20260328',time='023000'),event(),before_floating_zone='Europe/Berlin')
 def test_floating_until_and_exdate(self):
  a=self.floating('RRULE:FREQ=WEEKLY;UNTIL=20260406T090000\nEXDATE:20260330T090000\n')
  b=event('RRULE:FREQ=WEEKLY;UNTIL=20260406T070000Z\nEXDATE;TZID=Europe/Berlin:20260330T090000\n',start='DTSTART;TZID=Europe/Berlin:20260323T090000',end='DTEND;TZID=Europe/Berlin:20260323T100000')
  r=self.run_case(a,b,before_floating_zone='Europe/Berlin');self.assertEqual(r['status'],'equal_in_window');self.assertEqual(r['counts']['before'],2)
 def test_all_day_unchanged(self):
  a=event(start='DTSTART;VALUE=DATE:20260323',end='DTEND;VALUE=DATE:20260324')
  self.assertEqual(self.run_case(a,a,before_floating_zone='Asia/Tokyo')['status'],'equal_in_window')
 def test_floating_rdate_period(self):
  a=self.floating('RDATE;VALUE=PERIOD:20260401T090000/20260401T110000\n')
  r=self.run_case(a,a,before_floating_zone='Europe/Berlin',after_floating_zone='Europe/Berlin')
  self.assertEqual(r['counts']['before'],2)
 def test_moved_floating_exception(self):
  a=self.floating('RRULE:FREQ=WEEKLY;COUNT=3\n')
  b=a+self.floating('RECURRENCE-ID:20260330T090000\n',date='20260331')
  r=self.run_case(a,b,before_floating_zone='Europe/Berlin',after_floating_zone='Europe/Berlin')
  self.assertEqual(r['counts']['changed'],1)
