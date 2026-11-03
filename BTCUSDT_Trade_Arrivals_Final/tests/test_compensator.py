import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'/'hawkes'));sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'/'continuous_time'))
import numpy as np
from run import hawkes_intervals, poisson_intervals, loglike_poisson
from scipy.stats import kstest
# n=0 must be exact Poisson; compensator intervals are correct
x=np.array([.2,.8,1.4,2.1,4.1,5.5,7.0]);cut=3.;stop=8.;mu=.9
zs=hawkes_intervals(x,cut,stop,mu,0.,5.)
expected=mu*np.diff(np.r_[cut,x[(x>=cut)&(x<stop)]])
assert np.allclose(zs,expected,atol=1e-12)
# exact closed-form compensator increment for one prior shock
arr=np.array([.5,1.,2.,3.]);cut=2.5;mu=1.2;n=.3;beta=2.
z=hawkes_intervals(arr,cut,4,mu,n,beta)
S=np.sum(np.exp(-beta*(cut-arr[arr<cut])))
expected=mu*(3-cut)+n*S*(1-np.exp(-beta*(3-cut)))
assert np.allclose(z,[expected],atol=1e-12)
# deterministic Poisson piecewise rates; no look-ahead in calendar template
rates=np.array([1.,2.,3.,4.]);t=np.array([119.,121.,180.,250.,350.]);cut=120;stop=360
z=poisson_intervals(t,cut,stop,rates)
assert np.allclose(z,[2,118,60*2+10*3,100*3])
print('PASS: Poisson limit, Hawkes history compensator, seasonal rate piecewise integration')
