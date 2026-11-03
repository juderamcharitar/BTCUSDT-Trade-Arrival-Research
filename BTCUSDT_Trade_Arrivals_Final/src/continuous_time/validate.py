"""Continuous-time Hawkes estimator validation with known synthetic parameters and Binance BTCUSDT pilot.
Reproducible: pip install numpy scipy pandas numba ; python validate.py
"""
from pathlib import Path
import os
import zipfile,json,hashlib,time
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.special import expit
from numba import njit

ROOT=Path(os.environ.get('BTCUSDT_DATA_DIR',str(Path(__file__).resolve().parents[2]/'data'))).resolve(); OUT=Path(os.environ.get('BTCUSDT_OUTPUT_DIR',str(Path(__file__).resolve().parents[2]/'results'/'continuous_time_recomputed'))).resolve(); OUT.mkdir(parents=True,exist_ok=True)
@njit
def loglike(t,mu,n,beta,lo,hi):
    # history prior to lo contributes to lambda(t) throughout [lo,hi]
    s=0.;prev=0.;score=0.;inrange=0
    for k in range(len(t)):
        x=t[k]
        if x>=hi:break
        s*=np.exp(-beta*(x-prev))
        if x>=lo:
            intensity=mu+n*beta*s
            if intensity<=0:return -1e300
            score+=np.log(intensity);inrange+=1
        s+=1.
        prev=x
    integral=mu*(hi-lo)
    for x in t:
        if x>=hi:break
        a=lo if x<lo else x
        integral+=n*(np.exp(-beta*(a-x))-np.exp(-beta*(hi-x)))
    return score-integral

# Exact event simulation via branching representation, with history stabilization warmup.
def simulate_hawkes(mu,n,beta,T,seed=1,warm=400):
    rng=np.random.default_rng(seed)
    immigrants=rng.uniform(-warm,T, size=rng.poisson(mu*(T+warm)))
    all_events=list(immigrants)
    parents=np.asarray(immigrants)
    for generation in range(100):
        offspring_counts=rng.poisson(n,size=len(parents)); total=int(offspring_counts.sum())
        if total==0:break
        kids=np.repeat(parents,offspring_counts)+rng.exponential(1/beta,size=total)
        kids=kids[(kids>=-warm)&(kids<T)]
        if len(kids)==0:break
        all_events.extend(kids.tolist());parents=kids
    return np.sort(np.array(all_events)[(np.array(all_events)>=0)&(np.array(all_events)<T)])

def fit(t,T=600, restarts=4, beta_min=.003,beta_max=2000.):
    avg=len(t)/T
    def f(z):
        mu=np.exp(z[0]);n=.98*expit(z[1]);beta=np.exp(z[2])
        return -loglike(t,mu,n,beta,0,T)
    seeds=[]
    for n0,tau in [(.1,0.2),(.4,1),(.7,.02),(.25,10)][:restarts]:
        seeds.append([np.log(max(.001,avg*(1-n0))),np.log(n0/(.98-n0)),np.log(1/tau)])
    bound=[(np.log(1e-5),np.log(max(1e4,avg*100))),(-10,7),(np.log(beta_min),np.log(beta_max))]
    opts=[minimize(f,s,method='L-BFGS-B',bounds=bound,options={'maxiter':180,'ftol':1e-9}) for s in seeds]
    best=min(opts,key=lambda v:v.fun)
    mu=np.exp(best.x[0]);n=.98*expit(best.x[1]);beta=np.exp(best.x[2])
    return {'mu':float(mu),'n':float(n),'beta':float(beta),'tau_s':float(1/beta),'train_ll':float(-best.fun),'success':bool(best.success),'boundary_beta':bool(beta>=.99*beta_max or beta<=1.01*beta_min),'event_count':len(t),'seeds':len(opts)}

def actual_events(date,hour=12,minutes=10, step=0.):
    path=ROOT/f'BTCUSDT-trades-{date}.zip'
    data= pd.read_csv(path,compression='zip',header=None,usecols=[4],names=['t'],dtype={'t':'int64'})
    start=pd.Timestamp(f'{date} {hour:02}:00:00',tz='UTC').value//1000
    # Binance data since 2025 is microseconds; shift to exact relative times BEFORE float convert
    micros=data.t.to_numpy()
    sel=micros[(micros>=start)&(micros<start+minutes*60*1000000)]
    assert len(sel)>0,(date,sel.shape)
    uniq=np.unique(sel)
    if step:
        b=int(round(step*1e6));uniq=np.unique(((uniq-start)//b)*b+start)
    secs=(uniq-start).astype('float64')/1e6
    return secs, {'executions':len(sel),'distinct_timestamps':len(np.unique(sel)),'events_after_grouping':len(uniq),'zero_gaps_fraction':float(np.mean(np.diff(sel)==0)) if len(sel)>1 else 0,'zip_sha256':hashlib.sha256(path.read_bytes()).hexdigest()}

if __name__=='__main__':
    out={'method':'Exponential continuous-time Hawkes on distinct timestamps; beta bound widened from exp(5)~148.4/s to 2000/s, multi-start MLE; synthetic branching simulator warmup; real pilot uses first 10 minutes from 12:00 UTC','synthetic':[],'real':[]}
    # test exact likelihood known params and recovery on several simulated regimes
    for j,(mu,n,beta) in enumerate([(4,.25,.5),(3,.55,2),(1.8,.7,12)]):
        t=simulate_hawkes(mu,n,beta,1200,seed=177+j)
        tr=t[t<900]
        r=fit(tr,T=900)
        r.update({'truth':{'mu':mu,'n':n,'beta':beta},'true_ll':float(loglike(tr,mu,n,beta,0,900))})
        out['synthetic'].append(r)
        print('SYNTH',j,r,flush=True)
    for date in ['2026-10-01','2026-10-23']:
        for resolution in [0,.001,.01,.1]:
            t,meta=actual_events(date,step=resolution)
            r=fit(t,600)
            r.update({'date':date,'coarsening_seconds':resolution,'raw_data':meta})
            out['real'].append(r)
            print('REAL',date,resolution,round(r['n'],4),round(r['beta'],4),round(r['mu'],4),r['boundary_beta'],len(t),flush=True)
    (OUT/'results.json').write_text(json.dumps(out,indent=2))
