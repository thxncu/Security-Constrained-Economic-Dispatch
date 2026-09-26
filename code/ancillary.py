"""Recompute ancillary tables directly from the current derived panels.

No previous release, manuscript file, nested archive or precomputed output is read.
Printed table values use Python's round (nearest, ties to even).
"""
from pathlib import Path
import numpy as np
import pandas as pd
from consistency import consistency_table

ROOT=Path(__file__).resolve().parent
DATA=ROOT/'data'; OUT=ROOT/'results'
KEYS=('january_2025','elliott_2022','uri_2021')
LABELS=dict(zip(KEYS,('January 2025 main','Winter Storm Elliott 2022','Winter Storm Uri 2021')))
SHORTS=dict(zip(KEYS,('Jan. 2025','Elliott 2022','Uri 2021')))
I={k:pd.read_csv(DATA/f'{k}_reserve.csv',parse_dates=['slot']) for k in KEYS}
H={k:pd.read_csv(DATA/f'{k}_hourly.csv',parse_dates=['datetime']) for k in KEYS}

def residual(key, shock_mw, retained_mw):
    return np.maximum(shock_mw-np.maximum(I[key].prc_mw.to_numpy()-retained_mw,0),0)

def chi(key, shock_mw, retained_mw):
    r=residual(key,shock_mw,retained_mw)
    return float((r.sum()/12)/(shock_mw*len(r)/12))

def save(rows,name):
    pd.DataFrame(rows).to_csv(OUT/f'{name}.csv',index=False)

anchors=[(0,'Full PRC buffer'),(1375,'EEA3 trigger in force at Uri (pre-Nov. 2021)'),
 (1430,'EEA3 trigger in force at Elliott'),(1500,'EEA3 trigger since Nov. 2023'),
 (1750,'EEA2 trigger before Nov. 2023'),(2000,'EEA2 trigger since Nov. 2023'),
 (2300,'EEA1 trigger before Nov. 2023'),(2500,'EEA1 trigger since Nov. 2023'),
 (3000,'ERCOT low-reserve analysis boundary; central retained case'),(5000,'Stringent screening case')]
save([dict(retained_gw=r/1000,operational_anchor=label,
           **{SHORTS[k]:round(chi(k,15000,r),3) for k in KEYS}) for r,label in anchors],
     'table5_retained_anchor_sweep')
rows=[]
for k in KEYS:
    for r in (0,3):
        rec=dict(event=LABELS[k],retained_gw=r)
        for target in (.05,.10,.25,.50):
            rec[f'chi>={target:g}']=next((float(q) for q in range(1,26) if chi(k,q*1000,r*1000)>=target),np.nan)
        rows.append(rec)
save(rows,'table6_chi_crossings')
rows=[]
for k in KEYS:
    for fraction in (.5,1.):
        q=float(H[k].res_irr_outage_mw.max())*fraction
        rows.append(dict(event=LABELS[k],envelope_fraction=f'{int(fraction*100)}%',shock_gw=round(q/1000,2),
                         chi_retained_0=round(chi(k,q,0),3),chi_retained_3=round(chi(k,q,3000),3)))
save(rows,'tableS7_envelope_shocks')
rows=[];context=[]
for k in KEYS:
    h=H[k];p=h.loc[h.load_mw.idxmax()]
    rows.append(dict(event=LABELS[k],peak_load_hour=str(p.datetime),
                     **{c:round(float(p[c])) for c in ('load_mw','wind_mw','solar_mw','gas_mw','coal_mw','nuclear_mw')}))
    for tight,label in ((True,'Tight'),(False,'Other')):
        d=h[(h.prc_min_mw<8000)==tight]
        if d.empty:continue
        context.append(dict(event=LABELS[k],hour_class=label,hours=len(d),mean_wind_mw=round(float(d.wind_mw.mean())),
            wind_share_of_event_max_pct=round(100*d.wind_mw.mean()/h.wind_mw.max()),mean_gas_mw=round(float(d.gas_mw.mean())),
            mean_res_irr_outage_mw=round(float(d.res_irr_outage_mw.mean())),mean_load_mw=round(float(d.load_mw.mean()))))
save(rows,'tableS9_peak_fuel');save(context,'tableS10_tight_hour_context')
rows=[]
for k in ('uri_2021','elliott_2022'):
    res=residual(k,15000,0);positive=res>0
    rows.append(dict(event=LABELS[k],incidence=round(float(positive.mean()),3),mean_depth_gw=round(float(res[positive].mean()/1000),2)))
save(rows,'incidence_depth')
rows=[];slot=I['uri_2021'].slot
shed=(slot>=pd.Timestamp('2021-02-15 01:20'))&(slot<pd.Timestamp('2021-02-17 23:55'))
eea=(slot>=pd.Timestamp('2021-02-15 00:15'))&(slot<pd.Timestamp('2021-02-19 09:00'))
for r in (0,3000):
    e=residual('uri_2021',15000,r)/12
    rows.append(dict(retained_gw=r/1000,ree_total_gwh=round(float(e.sum()/1000)),
        ree_in_shed_gwh=round(float(e[shed].sum()/1000)),share_in_shed_pct=round(float(100*e[shed].sum()/e.sum()),1),
        ree_in_eea_gwh=round(float(e[eea].sum()/1000)),share_in_eea_pct=round(float(100*e[eea].sum()/e.sum()),1)))
save(rows,'uri_window_decomposition')
consistency_table(I['january_2025'],H['january_2025']).to_csv(OUT/'tableS6_scarcity_consistency.csv',index=False)
print('Recomputed eight ancillary tables directly from current data.')
