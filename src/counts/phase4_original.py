"""Chronological retrospective comparison. Sep train / Oct1-22 validation / Oct23-27 evaluation.
The model families were chosen in earlier work after examining other dates: this is not a pristine discovery-independent holdout.
Event definition: unique microsecond timestamps (not unique market orders). Features causal within each day.
"""
from pathlib import Path
import json,hashlib,zipfile
import numpy as np,pandas as pd
from scipy.signal import lfilter
from scipy.optimize import minimize,minimize_scalar
from scipy.special import gammaln
from scipy.stats import binomtest
ROOT=Path('/mnt/data');OUT=ROOT/'hawkes_multiday'/'phase4';OUT.mkdir(exist_ok=True,parents=True)
train=['2026-09-03','2026-09-10','2026-09-17','2026-09-24','2026-09-30']
validation=['2026-10-01','2026-10-08','2026-10-15','2026-10-22']
test=['2026-10-23','2026-10-24','2026-10-25','2026-10-26','2026-10-27']
models=['b30','b300','b60','bblend','EXP','AR']
series={}; manifest={}
def load_day(day):
 p=ROOT/f'BTCUSDT-trades-{day}.zip'; first=int(pd.Timestamp(day,tz='UTC').timestamp()*1e6)
 y=np.zeros(86400,dtype='float64');last=-1;total=0;uniq=0;reversal=0;out=0;minimum=None;maximum=None
 with zipfile.ZipFile(p) as z:
  names=z.namelist();assert len(names)==1 and names[0].endswith('.csv')
  with z.open(names[0]) as f:
   for chunk in pd.read_csv(f,header=None,names=['id','price','qty','quote','timestamp','buy','best'],usecols=['timestamp'],chunksize=750000):
    ts=chunk.timestamp.to_numpy('int64');total+=len(ts)
    if len(ts)==0:continue
    minimum=int(ts.min()) if minimum is None else min(minimum,int(ts.min()))
    maximum=int(ts.max()) if maximum is None else max(maximum,int(ts.max()))
    reversal+=int((ts[1:]<ts[:-1]).sum()) + (int(ts[0]<last) if last!=-1 else 0)
    is_new=np.r_[ts[0]!=last,ts[1:]!=ts[:-1]]
    secs=(ts[is_new]-first)//1000000
    valid=(secs>=0)&(secs<86400);out+=int((~valid).sum());uniq+=int(valid.sum())
    y+=np.bincount(secs[valid].astype(int),minlength=86400);last=int(ts[-1])
 manifest[day]={'file':p.name,'zip_size':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'execution_records':total,'distinct_timestamps':uniq,'out_of_day':out,'timestamp_reversals':reversal,'first_utc':pd.to_datetime(minimum,unit='us',utc=True).isoformat(),'last_utc':pd.to_datetime(maximum,unit='us',utc=True).isoformat(),'max_distinct_timestamps_per_sec':int(y.max())}
 assert out==0 and reversal==0,(day,out,reversal)
 return y

def lagmean(y,begin,end):
 c=np.r_[0.,np.cumsum(y)];t=np.arange(len(y));hi=np.maximum(0,t-begin+1);lo=np.maximum(0,t-end);n=np.maximum(1,hi-lo)
 return (c[hi]-c[lo])/n

def baseline(y,win):
 c=np.r_[0.,np.cumsum(y)];i=np.arange(len(y));j=np.maximum(0,i-win)
 return (c[i]-c[j]+60.)/(i-j+60.)

def features(y,model):
 b=baseline(y,1800)
 if model=='b30':return b[:,None]
 if model=='b300':return baseline(y,300)[:,None]
 if model=='b60':return baseline(y,60)[:,None]
 if model=='bblend':return np.column_stack((b,baseline(y,300),baseline(y,60)))
 if model=='AR':return np.column_stack((b,lagmean(y,1,1),lagmean(y,2,5),lagmean(y,6,30),lagmean(y,31,120)))
 if model=='EXP':return np.column_stack((b,lfilter([0.,np.exp(-0.5)],[1.,-np.exp(-0.5)],y)))
 raise ValueError(model)

def nb_ll(y,mu,k):
 mu=np.maximum(mu,1e-9)
 return gammaln(y+k)-gammaln(k)-gammaln(y+1)+k*np.log(k/(k+mu))+y*np.log(mu/(k+mu))

def train_model(model):
 X=np.vstack([features(series[d],model) for d in train]);y=np.concatenate([series[d] for d in train])
 w0=np.zeros(X.shape[1]);w0[0]=1
 def fun(w):
  m=np.maximum(X@w,1e-8)
  return np.mean(m-y*np.log(m)),(X*(1-y/m)[:,None]).mean(axis=0)
 opt=minimize(fun,w0,jac=True,method='L-BFGS-B',bounds=[(0,None)]*len(w0),options={'maxiter':180,'ftol':1e-11})
 w=opt.x;m=np.maximum(X@w,1e-8)
 scalar=minimize_scalar(lambda v:-nb_ll(y,m,np.exp(v)).mean(),bounds=(-6,9),method='bounded',options={'xatol':1e-5})
 return {'weights':w.tolist(),'nb_size_k':float(np.exp(scalar.x)),'poisson_objective_converged':bool(opt.success),'poisson_optimizer_message':str(opt.message),'nb_opt_converged':bool(scalar.success)}

for d in train+validation:
 series[d]=load_day(d);print('loaded development',d,manifest[d]['execution_records'],manifest[d]['distinct_timestamps'],flush=True)
params={}
for m in models:
 params[m]=train_model(m);print('fit',m,params[m],flush=True)
(OUT/'FROZEN_MODEL_PARAMETERS.json').write_text(json.dumps({'train':train,'validation':validation,'evaluation_dates':test,'models':params,'method':'Freeze September training parameters prior to reading October 23-27 evaluation archives; Oct 1-22 used only for diagnostics; model families and time constants were informed by previous experiments on other dates.'},indent=2))
print('FROZEN MODEL PARAMETERS SAVED BEFORE TEST FILE READ',flush=True)
results={}
for d in validation+test:
 if d not in series:series[d]=load_day(d)
 y=series[d];results[d]={}
 scores={}
 for m in models:
  p=params[m];mu=np.maximum(features(y,m)@np.asarray(p['weights']),1e-8);k=p['nb_size_k'];sc=nb_ll(y,mu,k)
  scores[m]=sc
  results[d][m]={'mean_nb_logscore':float(sc.mean()),'MAE':float(np.mean(np.abs(y-mu))),'predicted_mean':float(mu.mean()),'observed_mean':float(y.mean()),'pred_zero_rate':float(np.mean((k/(k+mu))**k)),'observed_zero_rate':float(np.mean(y==0)),'pearson_dispersion':float(np.mean((y-mu)**2/(mu+mu*mu/k)))}
 for m in ['AR','EXP']:
  for other in ['bblend','EXP']:
   if m==other:continue
   dif=scores[m]-scores[other]
   results[d][m+'_minus_'+other]={'mean_logscore_gain':float(np.mean(dif)),'positive_5minute_blocks':int(np.sum(dif.reshape(-1,300).mean(axis=1)>0))}
 print('evaluation',d,'AR',round(results[d]['AR']['mean_nb_logscore'],4),'EXP',round(results[d]['EXP']['mean_nb_logscore'],4),'blend',round(results[d]['bblend']['mean_nb_logscore'],4),flush=True)
summary={}
for m in ['AR','EXP']:
 for comparator in ['bblend','EXP']:
  if m==comparator:continue
  a=np.array([results[d][m]['mean_nb_logscore']-results[d][comparator]['mean_nb_logscore'] for d in test]);rng=np.random.default_rng(20261102)
  boots=rng.choice(a,size=(20000,len(a)),replace=True).mean(axis=1)
  summary[m+'_minus_'+comparator]={'daily_gains':dict(zip(test,map(float,a))),'mean_daily_gain':float(a.mean()),'positive_days':int((a>0).sum()),'bootstrap_95pct_interval':[float(np.quantile(boots,.025)),float(np.quantile(boots,.975))],'two_sided_day_sign_p':float(binomtest(int((a>0).sum()),len(a),.5).pvalue)}
output={'study':'Phase4 retrospective chronological training/validation/evaluation','warning':'Model families, event definition and metrics evolved after exploring other October and November dates; these new five dates are unused in previous runs but the research design is not prospectively pre-registered. No profit or causal Hawkes claim.','train_dates':train,'validation_dates':validation,'test_dates':test,'models':params,'manifest':manifest,'scores':results,'summary':summary}
(OUT/'results.json').write_text(json.dumps(output,indent=2))
print('FINAL SUMMARY',json.dumps(summary,indent=2),flush=True)
