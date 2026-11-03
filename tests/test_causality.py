import sys,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'/'counts'))
from reproduce import baseline,lagmean,features,nb_logscore
class TestChronology(unittest.TestCase):
 def test_no_current_second_leakage(self):
  y=np.array([1.,3.,2.,0.,8.,5.,7.,2.,0.,1.]); y2=y.copy();y2[5:]=100000
  for model in ['bblend','EXP','AR']:
   a=features(y,model);b=features(y2,model)
   self.assertTrue(np.array_equal(a[:6],b[:6]),model)
 def test_exposure_is_only_past(self):
  y=np.array([10.,20.,30.,40.,50.]); self.assertEqual(lagmean(y,1,1)[2],20.);self.assertEqual(lagmean(y,2,3)[3],15.)
 def test_nb_score_finite(self):
  self.assertTrue(np.isfinite(nb_logscore(np.array([0.,1.,4.]),np.array([.2,1.,3.]),1.2)).all())
if __name__=='__main__':unittest.main()
