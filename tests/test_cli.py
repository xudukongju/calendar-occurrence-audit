import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
class CLITests(unittest.TestCase):
 def run_audit(self, *args):
  return subprocess.run([sys.executable,'-m','calendar_occurrence_audit',*map(str,args)],capture_output=True,text=True,timeout=30)
 def args(self):
  return [ROOT/'examples/before-exdate.ics',ROOT/'examples/after-exdate.ics','--from','2026-03-01','--to','2026-05-01']
 def test_difference_json_and_exit(self):
  r=self.run_audit(*self.args());self.assertEqual(r.returncode,1);self.assertEqual(json.loads(r.stdout)['counts']['added'],1)
 def test_equality(self):
  a=self.args();a[1]=a[0];r=self.run_audit(*a);self.assertEqual(r.returncode,0)
 def test_missing_input_is_inconclusive(self):
  a=self.args();a[0]=ROOT/'nonexistent.ics';r=self.run_audit(*a);self.assertEqual(r.returncode,2);self.assertEqual(json.loads(r.stdout)['status'],'inconclusive')
 def test_timeout_is_inconclusive(self):
  r=self.run_audit(*self.args(),'--timeout','0.000001');self.assertEqual(r.returncode,2);self.assertIn('time limit',json.loads(r.stdout)['reason'])
 def test_invalid_window(self):
  a=self.args();a[-1]='2026-02-01';r=self.run_audit(*a);self.assertEqual(r.returncode,2)
 def test_nonfinite_timeout_rejected(self):
  for val in ['nan','inf','-1']:
   r=self.run_audit(*self.args(),'--timeout',val);self.assertEqual(r.returncode,2)
 def test_oversized_file(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'large.ics';p.write_bytes(b'x'*(5*1024*1024+1));a=self.args();a[0]=p
   r=self.run_audit(*a);self.assertEqual(r.returncode,2);self.assertIn('5 MiB',json.loads(r.stdout)['reason'])
 def test_malformed_does_not_echo_private_input(self):
  with tempfile.TemporaryDirectory() as d:
   p=Path(d)/'private.ics';p.write_text('PRIVATE_CALENDAR_CONTENT');a=self.args();a[0]=p
   r=self.run_audit(*a);self.assertEqual(r.returncode,2);self.assertNotIn('PRIVATE_CALENDAR_CONTENT',r.stdout+r.stderr)
 def test_floating_flags_record_context_without_editing_input(self):
  before=ROOT/'examples/before-floating.ics';after=ROOT/'examples/before-exdate.ics'
  original=before.read_bytes()
  r=self.run_audit(before,after,'--from','2026-03-01','--to','2026-05-01','--before-floating-zone','Europe/Berlin')
  self.assertEqual(r.returncode,0)
  self.assertEqual(json.loads(r.stdout)['floating_time_assumptions'],{'before':'Europe/Berlin','after':None})
  self.assertEqual(before.read_bytes(),original)
if __name__=='__main__':unittest.main()
