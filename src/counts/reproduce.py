"""Frozen BTC/USDT count-model evaluation. Uses only lagged one-second distinct-timestamp counts.

Usage: python src/counts/reproduce.py --data-dir /path/to/zips [--date 2026-10-23]
Requires: numpy pandas scipy. Results are out-of-sample retrospective, not preregistered.
"""
from pathlib import Path
import argparse, json, zipfile, hashlib
import numpy as np
import pandas as pd
from scipy.signal import lfilter
from scipy.special import gammaln
ROOT = Path(__file__).resolve().parents[2]
TEST_DATES = ['2026-10-23','2026-10-24','2026-10-25','2026-10-26','2026-10-27']

def load_unique_timestamp_counts(file, date):
    """Collapse duplicate microsecond timestamps, including across CSV read chunks."""
    first = int(pd.Timestamp(date,tz='UTC').timestamp()*1_000_000)
    counts=np.zeros(86400,dtype=float); last=None; prior_id=None
    n=unique=0
    with zipfile.ZipFile(file) as z:
        files = [name for name in z.namelist() if name.endswith('.csv')]
        if len(files)!=1: raise ValueError('Expected exactly one CSV in ZIP')
        with z.open(files[0]) as f:
            for chunk in pd.read_csv(f,header=None,usecols=[0,4],dtype={0:'int64',4:'int64'},chunksize=500_000):
                ids=chunk.iloc[:,0].to_numpy(); ts=chunk.iloc[:,1].to_numpy()
                if not len(ts):continue
                if last is not None and ts[0] < last:raise ValueError('Nonmonotone timestamps')
                if np.any(ts[1:]<ts[:-1]):raise ValueError('Nonmonotone timestamps')
                if prior_id is not None and ids[0] <= prior_id:raise ValueError('Non-increasing trade IDs')
                if np.any(ids[1:]<=ids[:-1]):raise ValueError('Non-increasing trade IDs')
                selected=np.r_[last is None or ts[0]!=last, ts[1:]!=ts[:-1]]
                sec=(ts[selected]-first)//1_000_000
                if np.any((sec<0)|(sec>=86400)):raise ValueError('Timestamp outside selected UTC day')
                counts+=np.bincount(sec.astype(int),minlength=86400)
                n+=len(ts);unique+=len(sec);last=ts[-1];prior_id=ids[-1]
    return counts, {'executions':n,'unique_microsecond_timestamps':unique,'sha256_zip':hashlib.sha256(Path(file).read_bytes()).hexdigest()}

def baseline(y,window):
    c=np.r_[0.,np.cumsum(y)];i=np.arange(len(y));j=np.maximum(0,i-window)
    return (c[i]-c[j]+60)/(i-j+60)

def lagmean(y,begin,end):
    c=np.r_[0.,np.cumsum(y)];t=np.arange(len(y))
    hi=np.maximum(0,t-begin+1);lo=np.maximum(0,t-end)
    return (c[hi]-c[lo])/np.maximum(1,hi-lo)

def features(y,model):
    b=baseline(y,1800)
    if model=='bblend':return np.column_stack([b,baseline(y,300),baseline(y,60)])
    if model=='EXP':
        rho=np.exp(-0.5)
        return np.column_stack([b,lfilter([0.,rho],[1.,-rho],y)])
    if model=='AR':return np.column_stack([b,lagmean(y,1,1),lagmean(y,2,5),lagmean(y,6,30),lagmean(y,31,120)])
    raise ValueError(model)

def nb_logscore(y,mu,k):
    mu=np.maximum(mu,1e-8)
    return gammaln(y+k)-gammaln(k)-gammaln(y+1)+k*np.log(k/(k+mu))+y*np.log(mu/(k+mu))

def evaluate_day(file,date,parameters):
    y,meta=load_unique_timestamp_counts(file,date)
    output={'date':date,'meta':meta,'models':{}}
    for m in ['bblend','EXP','AR']:
        p=parameters[m];mu=np.maximum(1e-8,features(y,m) @ np.array(p['weights']))
        k=p['nb_size_k'];score=nb_logscore(y,mu,k)
        output['models'][m]={'nb_score':float(score.mean()),'mae':float(np.mean(np.abs(y-mu))),
            'predicted_zero_fraction':float(np.mean((k/(k+mu))**k)), 'observed_zero_fraction':float(np.mean(y==0)),
            'pearson_dispersion':float(np.mean((y-mu)**2/(mu+mu*mu/k)))}
    output['AR_minus_blend']=output['models']['AR']['nb_score']-output['models']['bblend']['nb_score']
    output['AR_minus_EXP']=output['models']['AR']['nb_score']-output['models']['EXP']['nb_score']
    return output

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--data-dir',type=Path,required=True);ap.add_argument('--date',choices=TEST_DATES,default=None);ap.add_argument('--out',type=Path,default=None)
    args=ap.parse_args()
    frozen=json.loads((ROOT/'results/counts/frozen_parameters.json').read_text())['models']
    dates=[args.date] if args.date else TEST_DATES
    results=[evaluate_day(args.data_dir/f'BTCUSDT-trades-{d}.zip',d,frozen) for d in dates]
    for item in results:
        print(item['date'], 'exec=',item['meta']['executions'],'unique_ts=',item['meta']['unique_microsecond_timestamps'],
              'scores=',{m:round(item['models'][m]['nb_score'],6) for m in ['bblend','EXP','AR']})
    if args.out:args.out.write_text(json.dumps(results,indent=2))
if __name__=='__main__':main()
