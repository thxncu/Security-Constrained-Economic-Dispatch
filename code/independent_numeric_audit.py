"""Independent recheck of delivered R3 arithmetic (does not import analyze_r3).
Run: python independent_numeric_audit.py
Uses Decimal sums for 20 fixed cases; separately reconstructs 6,750 sensitivity
values and 20 wind cases; tests algebraic properties and a clipped-normal
analytic expectation. Source authentication/physical feasibility are not tested.
"""
from pathlib import Path
from decimal import Decimal, getcontext
import csv,json,math
import numpy as np
import pandas as pd
from scipy.special import ndtr
ROOT=Path(__file__).resolve().parent;D=ROOT/'data';O=ROOT/'results'
getcontext().prec=36
S=json.loads((D/'events.json').read_text()); data={};extended={};hourly={}
for key in S:
 data[key]=pd.read_csv(D/f'{key}_reserve.csv',parse_dates=['slot']).set_index('slot')
 extended[key]=pd.read_csv(D/f'{key}_reserve_extended.csv',parse_dates=['slot']).set_index('slot')
 hourly[key]=pd.read_csv(D/f'{key}_hourly.csv',parse_dates=['datetime']).set_index('datetime')
 assert data[key].index.is_unique and hourly[key].index.is_unique
 assert len(hourly[key])*12==len(data[key])
 assert set(data[key].index.floor('h'))==set(hourly[key].index)
 assert len(data[key])==int((pd.Timestamp(S[key][1])-pd.Timestamp(S[key][0])).total_seconds()/300)
fixed=pd.read_csv(O/'fixed_shocks.csv');fd=[]
for r in fixed.itertuples():
 q=Decimal(str(r.shock_gw))*1000;ret=Decimal(str(r.retained_gw))*1000
 vals=[max(q-max(Decimal(str(v))-ret,Decimal(0)),Decimal(0)) for v in data[r.event].prc_mw]
 exact=sum(vals)/Decimal(12);gap=float(exact)-r.ree_mwh
 assert abs(gap)<1e-6
 # Hourly-minimum reference recomputed from disjoint groups of twelve values.
 a=np.asarray(data[r.event].prc_mw);b=np.maximum(a-float(ret),0)
 upper=np.maximum(float(q)-b.reshape(-1,12).min(axis=1),0).sum()
 assert abs(upper-r.hourly_min_gwh*1000)<1e-6
 fd.append({'event':r.event,'shock_gw':r.shock_gw,'retained_gw':r.retained_gw,'decimal_ree_mwh':str(exact),'float_minus_csv_mwh':gap})
(O/'decimal_fixed_checks.json').write_text(json.dumps(fd,indent=2))
# Independent sensitivity calculation; do not reuse screen(), nominal(), or output subsets.
surface=pd.read_csv(O/'sensitivity_surface.csv');ds=[]
for r in surface.itertuples():
 a=pd.Timestamp(S[r.event][0])+pd.Timedelta(hours=r.start_shift_h)
 b=pd.Timestamp(S[r.event][1])+pd.Timedelta(hours=r.end_shift_h)
 x=extended[r.event].loc[(extended[r.event].index>=a)&(extended[r.event].index<b)]
 assert len(x)==int((b-a).total_seconds()/300)
 cap=x.prc_mw.to_numpy() if r.basis=='PRC' else x.rtolcap_mw.to_numpy()
 if r.basis=='RTOLCAP+RTOFFCAP':cap=cap+x.rtoffcap_mw.to_numpy()
 q=1000*r.shock_gw;ret=1000*r.retained_gw
 z=np.clip(q-np.clip(cap-ret,0,None),0,None)
 value=math.fsum(z)/(q*len(z));ds.append(abs(value-r.chi))
 assert abs(value-r.chi)<2e-14
# Recompute wind shock profiles from explicit timestamp lookup, not a merged array.
wind=pd.read_csv(O/'wind_shocks.csv');wd=[]
for r in wind.itertuples():
 x=data[r.event];hh=hourly[r.event]
 q=np.array([float(hh.loc[t.replace(minute=0,second=0),'wind_mw'])*r.alpha for t in x.index])
 buf=np.clip(x.prc_mw.to_numpy()-1000*r.retained_gw,0,None)
 energy=math.fsum(q)/12000
 ee=math.fsum(np.clip(q-buf,0,None))/12000
 qq=math.fsum(q)/len(q);ce=math.fsum(np.clip(qq-buf,0,None))/12000
 assert abs(energy-r.shock_gwh)<1e-9 and abs(ee-r.ree_gwh)<1e-9
 assert abs(ee/energy-r.chi_wind)<1e-13 and abs(ce/energy-r.chi_constant)<1e-13
 assert abs((ee-ce)/energy-r.delta_chi)<1e-13
 wd.append(dict(event=r.event,alpha=r.alpha,retained_gw=r.retained_gw,shock_gwh=energy,ree_gwh=ee,chi=ee/energy))
# Randomized property tests supplement, but do not replace, the analytic proofs.
rng=np.random.default_rng(91372);tests=0
for _ in range(1000):
 n=int(rng.integers(1,200));B=rng.uniform(0,100,n);q1=rng.uniform(0,100,n);q2=rng.uniform(0,100,n);dt=rng.uniform(.001,2,n);lam=rng.uniform()
 f=lambda q,b:np.dot(np.clip(q-b,0,None),dt)
 assert -1e-10<=f(q1,B)<=np.dot(q1,dt)+1e-10;tests+=1
 assert f(lam*q1+(1-lam)*q2,B)<=lam*f(q1,B)+(1-lam)*f(q2,B)+1e-9;tests+=1
 assert f(q1,B+1)<=f(q1,B)+1e-9;tests+=1
 assert f(q1+1,B)>=f(q1,B)-1e-9;tests+=1
 assert f(2*q1,B)/np.dot(2*q1,dt)>=f(q1,B)/np.dot(q1,dt)-1e-12;tests+=1
 # Weighted Jensen extends the equal-duration corollary for a constant buffer.
 b0=float(B[0]);mean=np.dot(q1,dt)/dt.sum()
 assert f(q1,b0)>=max(mean-b0,0)*dt.sum()-1e-9;tests+=1
assert np.maximum(np.zeros(3)-np.array([0,1,2]),0).sum()==0
# Analytic mean of the uncalibrated toy mixture, using its stated clipped normal.
mu,sd,lo,hi=12000.,4000.,2000.,25000.
def stoploss(a):
 a=np.asarray(a);z=(mu-a)/sd
 return (mu-a)*ndtr(z)+sd*np.exp(-z*z/2)/np.sqrt(2*np.pi)
eq=lo+stoploss(lo)-stoploss(hi)
class_exact={}
for key in ['january_2025','elliott_2022','uri_2021']:
 b=np.maximum(data[key].prc_mw.to_numpy()-3000,0)
 exp=np.where(b<lo,eq-b,np.where(b>=hi,0,stoploss(b)-stoploss(hi)))
 class_exact[key]=float(exp.sum()/12000)
weights=np.array([4,2,1])/15
exact_mean=float(weights@np.array(list(class_exact.values())))
mc=json.loads((O/'toy_mixture_summary.json').read_text()); z=(mc['mean_ree_gwh']-exact_mean)/mc['mc_se_gwh']
assert abs(z)<5, 'Monte Carlo mean differs by over five reported Monte Carlo standard errors'
report=dict(status='PASS',fixed_decimal_cases=len(fd),sensitivity_cases=len(ds),wind_cases=len(wd),randomized_property_assertions=tests,
 fixed_max_absolute_difference_mwh=max(abs(r['float_minus_csv_mwh']) for r in fd),sensitivity_max_absolute_difference=max(ds),
 illustrative_analytic_class_mean_ree_gwh=class_exact,illustrative_analytic_mixture_mean_ree_gwh=exact_mean,
 simulated_mixture_mean_ree_gwh=mc['mean_ree_gwh'],simulation_difference_in_mc_se=float(z),
 interpretation='All calculations use the stated nominal buffers. Analytic toy expectation is uncalibrated mean REE, not EUE. No claim of physical adequacy validation.')
(O/'independent_numeric_audit.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
