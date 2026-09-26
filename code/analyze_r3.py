"""Reproduce the R3 deterministic sensitivity, seasonal extension, and toy mixture.

Run: python analyze_r3.py
Inputs are derived 5-minute panels (MW; local ERCOT time) and hourly
load/fuel panels. Outputs are full-precision CSVs, figure source data, and PNG/SVG
figures. No probabilities are assigned to the sensitivity envelopes.
"""
from pathlib import Path
import json, time, platform, hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
from print_style import save_print

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'; OUT=ROOT/'results'; FIG=ROOT/'figures'
OUT.mkdir(exist_ok=True); FIG.mkdir(exist_ok=True)
DT=1/12
SPECS=json.loads((DATA/'events.json').read_text())
ORDER=['january_2025','elliott_2022','uri_2021','february_2022','july_2022']
BASES=['PRC','RTOLCAP','RTOLCAP+RTOFFCAP']
START=time.perf_counter()

def load(key, extended=False):
    d=pd.read_csv(DATA/f'{key}_reserve{"_extended" if extended else ""}.csv',parse_dates=['slot']).set_index('slot')
    assert d.index.is_unique and d.index.is_monotonic_increasing
    assert (d.index.to_series().diff().dropna()==pd.Timedelta(minutes=5)).all()
    assert not d[ ['prc_mw','rtolcap_mw','rtoffcap_mw','rtordpa'] ].isna().any().any()
    return d

def nominal(d,R=3000,basis='PRC'):
    base={'PRC':d.prc_mw,'RTOLCAP':d.rtolcap_mw,'RTOLCAP+RTOFFCAP':d.rtolcap_mw+d.rtoffcap_mw}[basis].to_numpy(float)
    return np.maximum(base-R,0)

def screen(d,q,R=3000,basis='PRC'):
    b=nominal(d,R,basis); q=np.broadcast_to(np.asarray(q,float),b.shape)
    if np.any(q<0):raise ValueError('Negative shocks are not defined.')
    residual=np.maximum(q-b,0); stress=q.sum()*DT
    native=residual.sum()*DT
    hm=pd.Series(b,index=d.index).groupby(d.index.floor('h')).transform('min').to_numpy()
    if not pd.Series(q,index=d.index).groupby(d.index.floor('h')).nunique().le(1).all():
        raise ValueError('Hourly-minimum comparison requires an hourly-constant shock.')
    hourly=np.maximum(q-hm,0).sum()*DT
    assert hourly>=native-1e-7
    return dict(ree_mwh=native,ree_gwh=native/1000,stress_gwh=stress/1000,chi=native/stress if stress else np.nan,
                hourly_min_gwh=hourly/1000,overstatement_pct=100*(hourly/native-1) if native else np.nan,
                incidence=(residual>0).mean(),mean_depth_mw=residual[residual>0].mean() if (residual>0).any() else 0.,
                risk_hours=(residual>0).sum()*DT)

def savefig(fig,name):
    save_print(fig,name,FIG)

# All central panels and the appended hourly context are included in the archive.
D={k:load(k) for k in ORDER}; X={k:load(k,True) for k in ORDER}
H={k:pd.read_csv(DATA/f'{k}_hourly.csv',parse_dates=['datetime']).set_index('datetime') for k in ORDER}
rows=[]; windrows=[]; boots=[]; convex=[]; summaries=[]
for key in ORDER:
    d=D[key]; h=H[key]; a,b,year,label=SPECS[key]
    h=h.loc[(h.index>=pd.Timestamp(a))&(h.index<pd.Timestamp(b))]
    assert len(h)==len(d)//12 and h.index.is_unique
    peak=h.load_mw.idxmax()
    summaries.append(dict(event=key,label=label,start=a,end_exclusive=b,hours=len(d)*DT,
        peak_load_mw=h.load_mw.max(),peak_hour=str(peak),min_prc_mw=d.prc_mw.min(),
        hours_min_prc_below_8gw=int((d.prc_mw.groupby(d.index.floor('h')).min()<8000).sum()),
        positive_adder_hours=int((d.rtordpa.groupby(d.index.floor('h')).max()>0).sum()),
        material_adder_hours=int((d.rtordpa.groupby(d.index.floor('h')).max()>10).sum()),
        max_adder=d.rtordpa.max(),mean_wind_mw=h.wind_mw.mean(),peak_wind_mw=h.loc[peak,'wind_mw'],
        peak_solar_mw=h.loc[peak,'solar_mw']))
    for q in [10000,15000]:
        for R in [0,3000]:
            rows.append(dict(event=key,shock_gw=q/1000,retained_gw=R/1000,**screen(d,q,R)))
            daily=pd.Series(np.maximum(q-nominal(d,R),0),index=d.index).groupby(d.index.floor('D')).sum().to_numpy()*DT/1000
            n=len(daily); rng=np.random.default_rng(20260)
            ree=daily[rng.integers(0,n,size=(2000,n))].sum(axis=1)
            lo,hi=np.quantile(ree,[.025,.975]); e=screen(d,q,R)
            boots.append(dict(event=key,shock_gw=q/1000,retained_gw=R/1000,ree_gwh=e['ree_gwh'],ree_low_gwh=lo,ree_high_gwh=hi,
                              chi=e['chi'],chi_low=lo/e['stress_gwh'],chi_high=hi/e['stress_gwh'],days=n,replicates=2000,seed=20260))
    for R in [0,3000]:
        qs=np.arange(.5,25.01,.5)*1000; es=[screen(d,q,R)['ree_mwh'] for q in qs]
        md=float(np.diff(es,2).min());assert md>-1e-6
        convex.append(dict(event=key,retained_gw=R/1000,points=len(qs),minimum_second_difference_mwh=md))
        w=h.wind_mw.reindex(d.index.floor('h')).to_numpy()
        for alpha in [.5,1.]:
            q=alpha*w; s=screen(d,q,R); c=screen(d,q.mean(),R)
            p=pd.Series(q).corr(pd.Series(nominal(d,R))); rho=pd.Series(q).corr(pd.Series(nominal(d,R)),method='spearman')
            windrows.append(dict(event=key,alpha=alpha,retained_gw=R/1000,shock_gwh=s['stress_gwh'],mean_shock_gw=q.mean()/1000,
                ree_gwh=s['ree_gwh'],chi_wind=s['chi'],chi_constant=c['chi'],delta_chi=s['chi']-c['chi'],pearson=p,spearman=rho))
fixed=pd.DataFrame(rows);fixed.to_csv(OUT/'fixed_shocks.csv',index=False)
pd.DataFrame(summaries).to_csv(OUT/'event_summary.csv',index=False)
pd.DataFrame(boots).to_csv(OUT/'day_composition.csv',index=False)
pd.DataFrame(windrows).to_csv(OUT/'wind_shocks.csv',index=False)
pd.DataFrame(convex).to_csv(OUT/'convexity.csv',index=False)

# Independently move each endpoint by -24, 0, or +24 h (nine explicit windows).
boundary=[]; surfaces=[]; onefactor=[]; alt=[]
for key in ORDER:
    a,b=map(pd.Timestamp,SPECS[key][:2]);windows={}
    for ds in [-24,0,24]:
        for de in [-24,0,24]:
            s=a+pd.Timedelta(hours=ds);e=b+pd.Timedelta(hours=de)
            dd=X[key].loc[(X[key].index>=s)&(X[key].index<e)]
            assert len(dd)==int((e-s).total_seconds()/300)
            windows[(ds,de)]=dd
            boundary.append(dict(event=key,start_shift_h=ds,end_shift_h=de,start=str(s),end_exclusive=str(e),hours=len(dd)*DT,**screen(dd,15000,3000)))
    for basis in BASES:
        for R in [0,3000]:
            alt.append(dict(event=key,basis=basis,retained_gw=R/1000,**screen(D[key],15000,R,basis)))
    for qgw in range(1,26):
        values=[]
        for basis in BASES:
            for R in [0,3000]:
                for (ds,de),dd in windows.items():
                    rec=dict(event=key,shock_gw=qgw,retained_gw=R/1000,basis=basis,start_shift_h=ds,end_shift_h=de,chi=screen(dd,qgw*1000,R,basis)['chi'])
                    surfaces.append(rec);values.append(rec['chi'])
        assert len(values)==54
    # One-factor and joint ranges have no probability interpretation.
    settings={
      'shock_10_to_20_GW':[screen(D[key],q*1000,3000)['chi'] for q in range(10,21)],
      'retained_0_to_3_GW':[screen(D[key],15000,R)['chi'] for R in [0,3000]],
      'nine_event_windows':[screen(dd,15000,3000)['chi'] for dd in windows.values()],
      'three_buffer_definitions':[screen(D[key],15000,3000,basis)['chi'] for basis in BASES],
      'joint_at_15_GW':[r['chi'] for r in surfaces if r['event']==key and r['shock_gw']==15]
    }
    for factor,values in settings.items():onefactor.append(dict(event=key,factor=factor,chi_min=min(values),chi_max=max(values),central_chi=screen(D[key],15000,3000)['chi']))
S=pd.DataFrame(surfaces);S.to_csv(OUT/'sensitivity_surface.csv',index=False)
pd.DataFrame(boundary).to_csv(OUT/'window_sensitivity.csv',index=False)
pd.DataFrame(onefactor).to_csv(OUT/'sensitivity_ranges.csv',index=False)
pd.DataFrame(alt).to_csv(OUT/'alternative_buffers.csv',index=False)

# Original-case native/hourly diagnostics: maximum hourly aggregation gap.
diag=[]
for key in ORDER[:3]:
    d=D[key];b=d.prc_mw
    native=np.maximum(10000-b,0)
    hm=b.groupby(d.index.floor('h')).transform('min');hr=np.maximum(10000-hm,0)
    gaps=(hr-native).groupby(d.index.floor('h')).sum()*DT
    center=gaps.idxmax();start=max(d.index.min(),center-pd.Timedelta(hours=2));end=min(d.index.max()+pd.Timedelta(minutes=5),start+pd.Timedelta(hours=6))
    start=end-pd.Timedelta(hours=6)
    z=pd.DataFrame({'prc_mw':b,'hourly_min_prc_mw':hm,'shock_mw':10000,'native_residual_mw':native,'hourly_min_residual_mw':hr}).loc[(d.index>=start)&(d.index<end)]
    z.to_csv(OUT/f'diagnostic_{key}.csv',index_label='slot')
    diag.append(dict(event=key,start=str(start),end_exclusive=str(end),max_gap_hour=str(center),native_gwh=z.native_residual_mw.sum()*DT/1000,hourly_min_gwh=z.hourly_min_residual_mw.sum()*DT/1000,maximum_hourly_gap_mwh=gaps.max()))
    fig,ax=plt.subplots(figsize=(7.3,3.9))
    # Extend the last value to the exclusive endpoint: traces match the
    # piecewise-constant intervals integrated by the estimator, not linear joins.
    zz=z.copy(); zz.loc[end]=z.iloc[-1]
    ax.step(zz.index,zz.prc_mw/1000,where='post',label='5-minute PRC',linewidth=1.3)
    ax.step(zz.index,zz.hourly_min_prc_mw/1000,where='post',label='Hourly-minimum PRC',linewidth=1.3)
    ax.step(zz.index,zz.shock_mw/1000,where='post',linestyle=':',label='Imposed shock (10 GW)',linewidth=1.6)
    ax.step(zz.index,zz.native_residual_mw/1000,where='post',label='Native residual',linewidth=1.3)
    ax.step(zz.index,zz.hourly_min_residual_mw/1000,where='post',linestyle='--',label='Hourly-minimum residual',linewidth=1.3)
    ax.set_xlim(start,end)
    ax.set(ylabel='Power (GW)',xlabel=f'ERCOT local time | {start:%Y-%m-%d}',title=SPECS[key][3])
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M')); ax.grid(True,alpha=.22)
    ax.legend(fontsize=8,ncol=2,loc='best');fig.tight_layout();savefig(fig,f'fig4_{key}')
pd.DataFrame(diag).to_csv(OUT/'diagnostic_windows.csv',index=False)

# Sensitivity figures: shock on x-axis; 54 deterministic combinations at every x.
for key in ORDER[:3]:
    sub=S[S.event==key]; g=sub.groupby('shock_gw').chi.agg(['min','max'])
    fig,ax=plt.subplots(figsize=(7.1,3.55))
    ax.fill_between(g.index,g['min'],g['max'],alpha=.22,label='54-combination sensitivity envelope')
    ax.plot(g.index,[screen(D[key],q*1000,3000)['chi'] for q in g.index],linewidth=1.7,label='Central: PRC, retained 3 GW, stated window')
    ax.set(xlabel='Shock magnitude (GW)',ylabel='Conditional attenuation factor, χ',ylim=(0,1.02),title=SPECS[key][3])
    ax.grid(True,alpha=.22);ax.legend(fontsize=8,loc='upper left');fig.tight_layout();savefig(fig,f'fig5_{key}')

# Original shock sweep, now on one axis with explicit retained-reserve line styles.
fig,ax=plt.subplots(figsize=(7.2,4.2))
for key in ORDER[:3]:
    for R in [0,3000]:
        ax.plot(range(1,26),[screen(D[key],q*1000,R)['chi'] for q in range(1,26)],linestyle='-' if R else '--',label=f'{SPECS[key][3]}, retained {R/1000:g} GW')
ax.set(xlabel='Shock magnitude (GW)',ylabel='Conditional attenuation factor, χ',ylim=(0,1),title='Larger χ means a larger nominal reserve-exceedance share')
ax.grid(True,alpha=.22);ax.legend(fontsize=8,ncol=2);fig.tight_layout();savefig(fig,'fig2_shock_sweep')

# Added winter/summer cases: no implied prediction of actual load shedding.
fig,ax=plt.subplots(figsize=(7.2,3.7))
for key in ORDER[3:]:
    for R in [0,3000]:
        ax.plot(range(1,26),[screen(D[key],q*1000,R)['chi'] for q in range(1,26)],linestyle='-' if R else '--',label=f'{SPECS[key][3]}, retained {R/1000:g} GW')
ax.set(xlabel='Shock magnitude (GW)',ylabel='Conditional attenuation factor, χ',ylim=(0,1));ax.legend(fontsize=8);ax.grid(True,alpha=.22);fig.tight_layout();savefig(fig,'fig6_added_seasons')

# Revised decision diagram: zero REE never certifies adequacy.
fig,ax=plt.subplots(figsize=(7.3,6.0));ax.set(xlim=(0,10),ylim=(0,10));ax.axis('off')
boxes=[
 '1. Define the event window and data coverage\nRetain source time stamps and audit missing / repeated runs',
 '2. Specify a shock and a nominal screening buffer\nState retained reserve, buffer meaning, and omitted physical constraints',
 '3. Integrate native-interval REE and report χ\nCompare the same screen with hourly-minimum integration',
 '4. Test shock, retained reserve, window, and buffer assumptions\nReport deterministic sensitivity envelopes and temporal concentration',
 '5. Decide what further evidence is required\nLarge or sensitive REE motivates chronological modelling;\nsmall or zero REE does not certify sustained adequacy',
 '6. Estimate EUE only in a physical probabilistic adequacy model\nState-specific unserved energy, energy budgets, network constraints,\noperational responses, and calibrated probabilities are required']
for j,txt in enumerate(boxes):
    y=9.65-j*1.57
    ax.add_patch(Rectangle((.3,y-1.15),9.4,1.18,fill=False,linewidth=1.1))
    ax.text(5,y-.57,txt,ha='center',va='center',fontsize=10)
    if j<5:ax.annotate('',xy=(5,y-1.50),xytext=(5,y-1.18),arrowprops=dict(arrowstyle='->'))
fig.tight_layout();savefig(fig,'fig1_workflow')

# Uri state-consistency plot; dates are report anchors, not independent UE validation.
d=D['uri_2021'];fig,ax=plt.subplots(figsize=(7.2,3.7));ax.plot(d.index,d.prc_mw/1000,label='5-minute PRC',linewidth=.9)
ax.axvspan(pd.Timestamp('2021-02-15 00:15'),pd.Timestamp('2021-02-19 09:00'),alpha=.13,label='Documented EEA window')
ax.axvspan(pd.Timestamp('2021-02-15 01:20'),pd.Timestamp('2021-02-17 23:55'),alpha=.22,label='Documented firm-load-shed window')
for val in [2.3,1.75,1.375]:ax.axhline(val,linestyle=':',linewidth=.8,label=f'Historical trigger {val:g} GW')
ax.set(ylabel='PRC (GW)',xlabel='ERCOT local date (February 2021)');ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'));ax.legend(fontsize=7.5,ncol=2);fig.tight_layout();savefig(fig,'fig3_uri_states')

# Actual raw duplicate-run sensitivity (not a pre-rounded legacy table).
raw=pd.read_csv(DATA/'january_2025_selected_runs.csv',parse_dates=['stamp','slot']).sort_values(['stamp','batch'],kind='stable')
a,b=map(pd.Timestamp,SPECS['january_2025'][:2]);raw=raw[(raw.slot>=a)&(raw.slot<b)]
variants={'Latest run':raw.drop_duplicates('slot',keep='last').set_index('slot'), 'First run':raw.drop_duplicates('slot',keep='first').set_index('slot'), 'Within-slot mean':raw.groupby('slot')[['prc_mw','rtolcap_mw','rtoffcap_mw','rtordpa']].mean()}
pd.DataFrame([dict(rule=rule,retained_gw=R/1000,**screen(dd,15000,R)) for rule,dd in variants.items() for R in [0,3000]]).to_csv(OUT/'january_dedup.csv',index=False)

# One missing summer slot: explicit no-assumption bounds and interpolation variants.
t=pd.Timestamp('2022-07-12 17:40');d=D['july_2022'];assert d.loc[t,'imputed']
gaps=[]
for method in ['Linear interpolation','Previous observation','Next observation','Zero residual bound','Full shock residual bound','Exclude missing slot']:
    dd=d.copy()
    if method=='Previous observation':dd.loc[t,'prc_mw']=dd.loc[t-pd.Timedelta(minutes=5),'prc_mw']
    if method=='Next observation':dd.loc[t,'prc_mw']=dd.loc[t+pd.Timedelta(minutes=5),'prc_mw']
    if method=='Zero residual bound':dd.loc[t,'prc_mw']=18000
    if method=='Full shock residual bound':dd.loc[t,'prc_mw']=0
    if method=='Exclude missing slot':dd=dd.drop(t)
    gaps.append(dict(method=method,prc_mw=dd.loc[t,'prc_mw'] if t in dd.index else np.nan,hours=len(dd)*DT,**screen(dd,15000,3000)))
pd.DataFrame(gaps).to_csv(OUT/'summer_missing_slot.csv',index=False)
assert abs(gaps[4]['ree_gwh']-gaps[3]['ree_gwh']-1.25)<1e-8

# Toy finite-mixture expectation, explicitly NOT EUE and NOT annualized.
classes=['none','january_2025','elliott_2022','uri_2021'];probs=np.array([8,4,2,1])/15
blocks={key:[g.prc_mw.to_numpy() for _,g in D[key].groupby(D[key].index.floor('D'))] for key in ORDER[:3]}
blocks={key:[np.maximum(g-3000,0) for g in val] for key,val in blocks.items()}
def conditional_draw(key,rng):
    q=float(np.clip(rng.normal(12000,4000),2000,25000))
    bl=blocks[key];idx=rng.integers(0,len(bl),size=len(bl));buf=np.concatenate([bl[i] for i in idx])
    return float(np.maximum(q-buf,0).sum()*DT/1000)
rng=np.random.default_rng(2026);clsdraw=rng.choice(4,size=20000,p=probs)
rr=np.array([0. if i==0 else conditional_draw(classes[i],rng) for i in clsdraw])
mc=dict(mean_ree_gwh=float(rr.mean()),mc_se_gwh=float(rr.std(ddof=1)/np.sqrt(len(rr))),median_gwh=float(np.median(rr)),p95_gwh=float(np.quantile(rr,.95)),p99_gwh=float(np.quantile(rr,.99)),draws=len(rr),seed=2026)
for i,key in enumerate(classes):mc[f'contribution_{key}_gwh']=float(rr[clsdraw==i].sum()/len(rr))
(OUT/'toy_mixture_summary.json').write_text(json.dumps(mc,indent=2))
pd.DataFrame({'class':[classes[i] for i in clsdraw],'ree_gwh':rr}).to_csv(OUT/'toy_mixture_draws.csv',index=False)
rng=np.random.default_rng(2027);means={'none':0.}
for key in classes[1:]:means[key]=float(np.mean([conditional_draw(key,rng) for _ in range(20000)]))
weights={
 'Baseline demonstration':[8/15,4/15,2/15,1/15],
 'Event-class probabilities halved':[23/30,2/15,1/15,1/30],
 'Event-class probabilities multiplied by 1.5':[.3,.4,.2,.1],
 'Equal event-class probabilities':[.8,1/15,1/15,1/15],
 'Uri-class probability halved':[17/30,4/15,2/15,1/30]}
probrows=[]
for name,p in weights.items():
    assert abs(sum(p)-1)<1e-9
    probrows.append(dict(scenario=name,**dict(zip(['p_none','p_january','p_elliott','p_uri'],p)),mean_ree_gwh=sum(p[i]*means[k] for i,k in enumerate(classes))))
pd.DataFrame(probrows).to_csv(OUT/'toy_mixture_sensitivity.csv',index=False)
(OUT/'toy_class_means.json').write_text(json.dumps(means,indent=2))
fig,ax=plt.subplots(figsize=(7.1,3.5));ax.plot(np.arange(1,len(rr)+1),np.cumsum(rr)/np.arange(1,len(rr)+1),linewidth=.9)
ax.set(xlabel='Monte Carlo draws',ylabel='Running mean REE (GWh)',title='Illustrative, uncalibrated finite mixture: not EUE');ax.grid(True,alpha=.22);fig.tight_layout();savefig(fig,'figS6_toy_mean_ree')

# Distinguish matched-assumption ordering from envelopes across different assumptions.
# A single comparison fixes q, retained reserve, buffer, and both boundary shifts.
matched = S[S.event.isin(ORDER[:3])].pivot(index=['shock_gw','retained_gw','basis','start_shift_h','end_shift_h'], columns='event', values='chi')
matched['january_le_elliott'] = matched.january_2025 <= matched.elliott_2022 + 1e-12
matched['elliott_le_uri'] = matched.elliott_2022 <= matched.uri_2021 + 1e-12
matched['weak_order_preserved'] = matched.january_le_elliott & matched.elliott_le_uri
matched.reset_index().to_csv(OUT/'matched_assumption_order.csv', index=False)
assert len(matched) == 1350 and matched.weak_order_preserved.all()

# Numerical checks and environment report.
for key in ORDER:
    for q in [10000,15000]:
        assert screen(D[key],q,3000)['chi']>=screen(D[key],q,0)['chi']-1e-12
        assert 0<=screen(D[key],q,3000)['chi']<=1
assert abs(fixed[(fixed.event=='january_2025')&(fixed.shock_gw==15)&(fixed.retained_gw==3)].iloc[0].chi-.424)<.0005
assert mc['mc_se_gwh']>0
report=dict(status='PASS',elapsed_seconds=time.perf_counter()-START,python=platform.python_version(),numpy=np.__version__,pandas=pd.__version__,matplotlib=matplotlib.__version__,five_events=len(D),sensitivity_cases=len(S),matched_assumption_cases=len(matched),matched_order_preserved=int(matched.weak_order_preserved.sum()),assertions='Coverage, hourly upper bound, nonnegative shocks, convexity, retained-reserve monotonicity, mixture probability normalization, and missing-slot bound')
(OUT/'verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2));print('\nFIXED SHOCKS\n',fixed.to_string(index=False));print('\nSENSITIVITY\n',pd.DataFrame(onefactor).to_string(index=False));print('\nDIAGNOSTICS\n',pd.DataFrame(diag).to_string(index=False));print('\nWIND R3\n',pd.DataFrame(windrows).query('retained_gw == 3').to_string(index=False))
