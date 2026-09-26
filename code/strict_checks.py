"""Additional, independently implemented R3 checks.

Run: python strict_checks.py
Uses included source executions; does not download data. Durations at actual
execution timestamps use a piecewise-constant (last-observation-carried-forward)
reconstruction; this is a sensitivity convention, not a physical dispatch model.
All dates in selected windows use local ERCOT time and exclude DST transitions.
"""
from pathlib import Path
import json, time
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from print_style import save_print

ROOT=Path(__file__).resolve().parent
D=ROOT/'data'; O=ROOT/'results'; F=ROOT/'figures'
S=json.loads((D/'events.json').read_text())
ORIG=['january_2025','elliott_2022','uri_2021']
C=['prc_mw','rtolcap_mw','rtoffcap_mw','rtordpa']
start_time=time.perf_counter()
rows=[]; typical=[]; distribution=[]; threshold=[]
fixed=pd.read_csv(O/'fixed_shocks.csv')
for key,(start,end,year,label) in S.items():
    a,b=pd.Timestamp(start),pd.Timestamp(end)
    x=pd.read_csv(D/f'{key}_reserve.csv',parse_dates=['slot']).set_index('slot')
    runs=pd.read_csv(D/f'{key}_selected_runs.csv',parse_dates=['stamp'])
    assert runs['repeat'].fillna('N').eq('N').all(), 'Repeated local clock requires explicit UTC conversion.'
    runs=runs.sort_values(['stamp','batch'],kind='stable').drop_duplicates('stamp',keep='last')
    assert (runs.stamp<=a).any() and (runs.stamp>=b).any(), 'Endpoint support is required.'
    before=runs.loc[runs.stamp<=a].iloc[[-1]].copy(); before['stamp']=a
    middle=runs.loc[(runs.stamp>a)&(runs.stamp<b)]
    held=pd.concat([before,middle],ignore_index=True)
    t=held.stamp.to_numpy('datetime64[ns]')
    dt=np.diff(np.append(t,b.to_datetime64())).astype('timedelta64[ns]').astype(float)/3.6e12
    assert np.all(dt>0) and abs(dt.sum()-(b-a).total_seconds()/3600)<1e-9
    for q in (10000.,15000.):
        for r in (0.,3000.):
            residual=np.maximum(q-np.maximum(x.prc_mw.to_numpy()-r,0),0)
            native=float(residual.sum()/12)
            claimed=fixed.loc[(fixed.event==key)&(fixed.shock_gw==q/1000)&(fixed.retained_gw==r/1000)].iloc[0]
            assert abs(native-claimed.ree_mwh)<1e-6
            actual=float(np.dot(np.maximum(q-np.maximum(held.prc_mw.to_numpy()-r,0),0),dt))
            stress=q*dt.sum()
            rows.append(dict(event=key,shock_gw=q/1000,retained_gw=r/1000,
                grid_ree_mwh=native,execution_hold_ree_mwh=actual,difference_mwh=actual-native,
                difference_pct=100*(actual-native)/native if native else np.nan,
                grid_chi=native/stress,execution_hold_chi=actual/stress,
                execution_segments=len(held),hours=dt.sum(),max_hold_minutes=dt.max()*60))
    if key=='uri_2021':
        first=runs.loc[(runs.stamp>=a)&(runs.stamp<b)&(runs.prc_mw<2300)].iloc[0]
        inside=(x.index>=pd.Timestamp('2021-02-15 00:15')) & (x.index<pd.Timestamp('2021-02-19 09:00'))
        below=x.prc_mw.to_numpy()<2300
        assert int((inside & below).sum())==420 and int(inside.sum())==1257
        assert int((~inside & below).sum())==1
        threshold.append(dict(event=key,threshold_mw=2300,first_execution_stamp=str(first.stamp),
            floored_slot=str(first.stamp.floor('5min')),prc_mw=float(first.prc_mw),
            declaration_stamp='2021-02-15 00:15:00',
            within_eea_grid_slots=int(inside.sum()),within_eea_below_threshold=int((inside & below).sum()),
            outside_eea_below_threshold=int((~inside & below).sum()),
            recorded_lead_minutes=(pd.Timestamp('2021-02-15 00:15')-first.stamp).total_seconds()/60))
    if key not in ORIG: continue
    # Same q=10 GW, R=0 convention as the main-text diagnostic illustrations.
    native=np.maximum(10000-x.prc_mw,0)
    minimum=x.prc_mw.groupby(x.index.floor('h')).transform('min')
    hourly=np.maximum(10000-minimum,0)
    gaps=((hourly-native)/12).groupby(x.index.floor('h')).sum()
    positive=gaps[gaps>1e-9]
    median=float(positive.median())
    distance=(positive-median).abs()
    target=distance.index[np.flatnonzero(np.isclose(distance,distance.min(),rtol=0,atol=1e-9))[0]]
    left=max(a,target-pd.Timedelta(hours=2)); right=min(b,left+pd.Timedelta(hours=6))
    left=max(a,right-pd.Timedelta(hours=6))
    sel=x.loc[(x.index>=left)&(x.index<right)]
    sn=native.loc[sel.index]; sh=hourly.loc[sel.index]
    typical.append(dict(event=key,target_hour=str(target),start=str(left),end_exclusive=str(right),
        median_positive_hour_gap_mwh=median,selected_hour_gap_mwh=float(gaps.loc[target]),
        grid_ree_gwh=sn.sum()/12000,hourly_min_ree_gwh=sh.sum()/12000,
        gap_gwh=(sh-sn).sum()/12000))
    distribution.append(dict(event=key,hours=len(gaps),positive_gap_hours=len(positive),
        all_hour_median_mwh=gaps.median(),positive_hour_median_mwh=median,
        all_hour_p95_mwh=gaps.quantile(.95),all_hour_max_mwh=gaps.max()))
    # Each is a standalone figure; all four requested traces remain visible.
    fig,ax=plt.subplots(figsize=(9,3.5))
    times=sel.index
    def step(y,**kw):
        ax.step(times.append(pd.DatetimeIndex([right])),np.append(np.asarray(y),np.asarray(y)[-1]),where='post',**kw)
    step(sel.prc_mw/1000,label='Five-minute PRC',linewidth=1.2)
    step(minimum.loc[times]/1000,label='Hourly-minimum PRC',linewidth=1.2,linestyle='--')
    ax.axhline(10,label='Imposed shock (10 GW)',linewidth=1,linestyle=':')
    step(sn/1000,label='Five-minute residual',linewidth=1.1)
    step(sh/1000,label='Hourly-minimum residual',linewidth=1.1,linestyle='--')
    ax.set_ylabel('Power (GW)');ax.set_xlabel('ERCOT local time');ax.set_title(f'{label} | {left:%d %b %Y} | median positive-gap example')
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'));ax.set_xlim(left,right)
    ax.grid(alpha=.2);ax.legend(loc='upper center',bbox_to_anchor=(.5,-.24),ncol=3,fontsize=8,frameon=False)
    fig.tight_layout()
    save_print(fig,f'figS7_{key}',F)
    pd.DataFrame({'time':times,'prc_mw':sel.prc_mw,'hourly_min_prc_mw':minimum.loc[times],
        'shock_mw':10000.,'native_residual_mw':sn,'hourly_residual_mw':sh}).to_csv(O/f'representative_series_{key}.csv',index=False)

stamp=pd.DataFrame(rows);stamp.to_csv(O/'execution_time_sensitivity.csv',index=False)
pd.DataFrame(typical).to_csv(O/'representative_periods.csv',index=False)
pd.DataFrame(distribution).to_csv(O/'hourly_gap_distribution.csv',index=False)
pd.DataFrame(threshold).to_csv(O/'exact_threshold_timing.csv',index=False)
# Idealized physical counterexamples. These are not fitted or simulated ERCOT cases.
cases=[]
for duration in (.25,1.,4.,12.):
    # A fully charged 1 GW / 1 GWh store, no recharge, unit efficiency, q=1 GW.
    cases.append(dict(case='Energy-limited store',duration_h=duration,shock_gw=1.,nominal_buffer_gw=1.,
        initial_energy_gwh=1.,activation_delay_h=0.,ree_gwh=0.,physical_ue_gwh=max(duration-1.,0)))
cases.append(dict(case='Uncredited corrective supply',duration_h=4.,shock_gw=1.,nominal_buffer_gw=0.,
    initial_energy_gwh=np.nan,activation_delay_h=.25,ree_gwh=4.,physical_ue_gwh=.25))
pd.DataFrame(cases).to_csv(O/'physical_boundary_examples.csv',index=False)
# Equal expectations need not imply state-by-state equality.
prob=np.array([.5,.5]);ree=np.array([0.,2.]);ue=np.array([1.,1.])
assert prob@ree==prob@ue and not np.array_equal(ree,ue)
maxrow=stamp.loc[stamp.difference_pct.abs().idxmax()]
report=dict(status='PASS',elapsed_seconds=time.perf_counter()-start_time,
    original_fixed_result_checks=len(stamp),execution_time_cases=len(stamp),
    max_absolute_difference_pct=float(stamp.difference_pct.abs().max()),
    max_difference_case=maxrow.to_dict(),
    matched_original_order_at_15gw_retained3=bool(stamp.query('shock_gw==15 and retained_gw==3').set_index('event').loc[ORIG,'execution_hold_chi'].is_monotonic_increasing),
    typical_example_count=len(typical),physical_examples=len(cases),
    expectation_equality_not_state_equality=True,
    limitations='Execution-time hold is an alternative temporal reconstruction, not continuous physical dispatch; toy examples are not ERCOT validation.')
(O/'strict_verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
print(stamp.to_string(index=False));print(pd.DataFrame(typical).to_string(index=False));print(pd.DataFrame(distribution).to_string(index=False))
