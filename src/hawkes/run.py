"""Phase 6: exact conditional compensator / held-out time-rescaling diagnostics.
Uses saved validated estimator from hawkes_ct_validation/validate.py.
Evaluation dates are reused exploratory data, NOT pristine holdout.
"""
import sys, os, json, zipfile, hashlib
from pathlib import Path
import numpy as np, pandas as pd
from scipy.stats import kstest
from scipy.optimize import minimize
from scipy.special import expit
from numba import njit
ROOT=Path(os.environ.get('BTCUSDT_DATA_DIR',str(Path(__file__).resolve().parents[2]/'data'))).resolve(); OUT=Path(os.environ.get('BTCUSDT_OUTPUT_DIR',str(Path(__file__).resolve().parents[2]/'results'/'hawkes_recomputed'))).resolve(); OUT.mkdir(parents=True,exist_ok=True);sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'continuous_time'))
from validate import fit,loglike
DATES_TRAIN=['2026-09-03','2026-09-10','2026-09-17','2026-09-24','2026-09-30']
DATES_EVAL=['2026-10-23','2026-10-24','2026-10-25']
START=12*3600; DUR=1200; CUT=600

def read_window(date):
    fp=ROOT/f'BTCUSDT-trades-{date}.zip'
    with zipfile.ZipFile(fp) as z:
        with z.open(z.namelist()[0]) as f:
            # avoid memory blow-up by chunking
            parts=[]; ids=[];sides=[]
            for ch in pd.read_csv(f,header=None,usecols=[0,4,5],dtype={0:'int64',4:'int64',5:'str'},chunksize=500000):
                # timestamp microseconds epoch
                epoch=pd.Timestamp(f'{date} 00:00:00',tz='UTC').value//1000
                ts=ch[4].to_numpy(dtype='int64');mask=(ts>=epoch+START*1000000)&(ts<epoch+(START+DUR)*1000000)
                if mask.any():
                    parts.append((ts[mask]-(epoch+START*1000000)).copy())
                    ids.append(ch[0].to_numpy()[mask].copy())
                    sides.append(ch[5].to_numpy()[mask].copy())
    return np.concatenate(parts),np.concatenate(ids),np.concatenate(sides)

def get_events(raw_us,threshold_us):
    unique=np.unique(raw_us)
    if threshold_us==0: out=unique
    else:
        # Event = first unique timestamp of each burst; a burst ends after a gap > threshold.
        boundaries=np.r_[True,np.diff(unique)>threshold_us]
        out=unique[boundaries]
    return out.astype(np.float64)/1e6

@njit
def hawkes_intervals(t,cut,stop,mu,n,beta):
    # Time-rescaling: conditional compensator from previous event (or cut) to the next test event
    intervals=np.empty(len(t));k=0
    s=0.;prev=0.; left=cut
    # advance past training events to obtain intensity history at cutoff
    for x in t:
        if x>=cut:break
        s*=np.exp(-beta*(x-prev));s+=1.;prev=x
    s*=np.exp(-beta*(cut-prev));prev=cut
    for x in t:
        if x<cut:continue
        if x>=stop:break
        dt=x-prev
        z=mu*dt+n*s*(-np.expm1(-beta*dt))
        intervals[k]=z;k+=1
        s=s*np.exp(-beta*dt)+1.
        prev=x
    return intervals[:k]

def metrics(z):
    if len(z)<20:return {}
    z=np.asarray(z)
    # PIT U=1-exp(-z) follows Uniform(0,1) under correct conditional process intensity
    U=-np.expm1(-z)
    ks=kstest(U,'uniform')
    cov=np.corrcoef(z[:-1],z[1:])[0,1]
    return dict(count=len(z),mean_compensated=float(z.mean()),var_compensated=float(z.var()),ks_stat=float(ks.statistic),ks_pvalue=float(ks.pvalue),lag1_corr=float(cov),fraction_z_under_point_one=float((z<.1).mean()))

def template_from_past():
    counts=[]
    for d in DATES_TRAIN:
        t,*_=read_window(d)
        event=get_events(t,0)
        counts.append(np.histogram(event,bins=np.arange(0,DUR+120,120))[0].astype(float))
    a=np.asarray(counts)
    # Prior-date deterministic time-of-day Poisson template (2min bins).
    template=a.mean(axis=0)
    overall=template.mean()
    # shrink to the pooled mean to avoid fitting noise from only five days
    return .6*template+.4*overall,a

def poisson_intervals(t,cut,stop,rates):
    # rates piecewise-constant over 120 s bins, defined using only previous dates + first 600s per evaluation day
    ev=t[(t>=cut)&(t<stop)]
    prev=cut;z=[]
    for x in ev:
        cur=prev;total=0.
        while cur<x:
            b=min(int(cur//120),len(rates)-1)
            edge=min(x,(b+1)*120)
            if edge<=cur: edge=x
            total+=float(rates[b])*(edge-cur)
            cur=edge
        z.append(total);prev=x
    return np.asarray(z)

def loglike_poisson(t,cut,stop,rates):
    arr=t[(t>=cut)&(t<stop)]
    ll=sum(np.log(max(rates[min(int(x//120),len(rates)-1)],1e-12)) for x in arr)
    integrated=0
    for b in range(len(rates)):
        a=max(cut,120*b);c=min(stop,120*(b+1))
        if c>a: integrated+=rates[b]*(c-a)
    return float(ll-integrated)

if __name__=='__main__':
    template,template_samples=template_from_past()
    results={'design':{'train_days':DATES_TRAIN,'evaluation_days':DATES_EVAL,'event_definitions':['unique_microsecond_timestamp','burst_gap_1ms','burst_gap_10ms'],'train_interval_UTC':'12:00-12:10','test_interval_UTC':'12:10-12:20','baseline':'2-minute time-of-day rate template using 5 Sep days, shrinkage 40% towards pooled mean, scaled using only first 10min on each evaluation day','status':'EXPLORATORY: evaluation dates were previously examined in earlier project phases; NOT novel independent testing'},'baseline_prior_counts':template_samples.tolist(),'baseline_template_counts':template.tolist(),'rows':[],'audit':[]}
    for d in DATES_EVAL:
        raw,ids,sides=read_window(d)
        unique=np.unique(raw);dupe_frac=1-len(unique)/len(raw)
        result={'date':d,'executions':len(raw),'unique_timestamps':len(unique),'same_timestamp_execution_fraction':dupe_frac,'ids_nondecreasing':bool(np.all(np.diff(ids)>=0)),'mixed_aggressor_side_timestamps':None,'event_fits':[]}
        # Side indicator: at how many timestamp groups do both maker flags occur?
        frame=pd.DataFrame({'t':raw,'side':sides})
        nun=frame.groupby('t',sort=False)['side'].nunique()
        result['mixed_aggressor_side_timestamps']=int((nun>1).sum())
        for threshold,label in [(0,'unique_microsecond_timestamp'),(1000,'burst_gap_1ms'),(10000,'burst_gap_10ms')]:
            t=get_events(raw,threshold);tr=t[t<CUT]
            par=fit(tr,T=CUT,restarts=4,beta_min=.003,beta_max=2000)
            # fit likely converge for most samples; no tuning on test
            z=hawkes_intervals(t,CUT,DUR,par['mu'],par['n'],par['beta'])
            LL=loglike(t,par['mu'],par['n'],par['beta'],CUT,DUR)
            train_counts=np.histogram(tr,bins=np.arange(0,601,120))[0]
            factor=float(train_counts.sum()/max(template[:5].sum(),1))
            rates=np.maximum(template*factor/120,1e-6)
            pz=poisson_intervals(t,CUT,DUR,rates)
            pll=loglike_poisson(t,CUT,DUR,rates)
            homog=float(len(tr)/CUT)
            hll=float(len(z)*np.log(homog)-homog*(DUR-CUT))
            result['event_fits'].append({'definition':label,'merge_gap_us':threshold,'train_events':len(tr),'test_events':len(z),'hawkes_params':par,'hawkes_test_ll':float(LL),'seasonal_poisson_test_ll':float(pll),'homogeneous_poisson_test_ll':float(hll),'delta_ll_vs_seasonal':float(LL-pll),'per_event_ll_gain':float((LL-pll)/max(len(z),1)),'hawkes_rescaling':metrics(z),'seasonal_poisson_rescaling':metrics(pz)})
            print(d,label,'N',len(z),'beta',round(par['beta'],3),'n',round(par['n'],3),'LL Gain',round(LL-pll,2),'KS',round(metrics(z).get('ks_stat',0),3),flush=True)
        results['rows'].append(result)
    (OUT/'results.json').write_text(json.dumps(results,indent=2))
    flat=[]
    for day in results['rows']:
        for r in day['event_fits']:
            flat.append({'date':day['date'],'event_definition':r['definition'],'train_events':r['train_events'],'test_events':r['test_events'],'n':r['hawkes_params']['n'],'beta_per_s':r['hawkes_params']['beta'],'decay_ms':r['hawkes_params']['tau_s']*1000,'optimizer_success':r['hawkes_params']['success'],'beta_boundary':r['hawkes_params']['boundary_beta'],'Hawkes_log_likelihood':r['hawkes_test_ll'],'time_of_day_poisson_log_likelihood':r['seasonal_poisson_test_ll'],'Hawkes_loglik_gain_per_event':r['per_event_ll_gain'],'Hawkes_rescaled_mean':r['hawkes_rescaling'].get('mean_compensated'),'Hawkes_KS_p':r['hawkes_rescaling'].get('ks_pvalue'),'Hawkes_lag1_corr':r['hawkes_rescaling'].get('lag1_corr'),'Poisson_KS_p':r['seasonal_poisson_rescaling'].get('ks_pvalue')})
    pd.DataFrame(flat).to_csv(OUT/'summary.csv',index=False)
    print('SAVED',OUT,flush=True)
