"""Forward-observation persistence sensitivity, not a physical capability model.

For D=1,2,4 hours, credit the minimum observed nominal buffer on [t,t+D).
The primary rule uses observations after the event end so every evaluation has
D hours of support. A secondary rule truncates the look-ahead at the event end.
D=0 denotes the original instantaneous nominal buffer. These are retrospective,
look-ahead diagnostics; they are not implementable real-time reserve forecasts.
"""
from pathlib import Path
from collections import deque
import json
import math
import numpy as np
import pandas as pd
from pandas.api.indexers import FixedForwardWindowIndexer

ROOT=Path(__file__).resolve().parent;D=ROOT/'data';O=ROOT/'results'
S=json.loads((D/'events.json').read_text());rows=[];max_check_error=0.

def forward_min_deque(values,n):
    """Independent right-truncated forward minimum, O(N)."""
    out=np.empty(len(values));queue=deque()
    for i in range(len(values)-1,-1,-1):
        while queue and queue[0]>=i+n:queue.popleft()
        while queue and values[queue[-1]]>=values[i]:queue.pop()
        queue.append(i);out[i]=values[queue[0]]
    return out

for key,(a,b,_,_) in S.items():
    a,b=pd.Timestamp(a),pd.Timestamp(b)
    x=pd.read_csv(D/f'{key}_reserve_extended.csv',parse_dates=['slot']).set_index('slot')
    central=x.loc[(x.index>=a)&(x.index<b)]
    if x.index[-1]+pd.Timedelta(minutes=5)<b+pd.Timedelta(hours=4):
        raise ValueError('Four hours of endpoint support are required.')
    if len(central)!=int((b-a).total_seconds()/300):raise ValueError('Incomplete central window')
    for mode in ('full_horizon','event_end_truncated'):
        source=x if mode=='full_horizon' else central
        for horizon in (0,1,2,4):
            n=max(1,horizon*12)
            prm=source.prc_mw.rolling(window=FixedForwardWindowIndexer(window_size=n),min_periods=n if mode=='full_horizon' else 1).min()
            cap=prm.reindex(central.index).to_numpy(float)
            independent=pd.Series(forward_min_deque(source.prc_mw.to_numpy(float),n),index=source.index).reindex(central.index).to_numpy(float)
            if not np.allclose(cap,independent,rtol=0,atol=1e-9):raise ValueError('Forward minimum algorithms disagree')
            max_check_error=max(max_check_error,float(np.abs(cap-independent).max()))
            if np.isnan(cap).any():raise ValueError('Look-ahead support missing')
            for qgw in (10,15):
                for rgw in (0,3):
                    q=qgw*1000;r=rgw*1000
                    z=np.maximum(q-np.maximum(cap-r,0),0)
                    baseline=np.maximum(q-np.maximum(central.prc_mw.to_numpy()-r,0),0)
                    value=math.fsum(z)/(q*len(z));base=math.fsum(baseline)/(q*len(z))
                    if value<base-1e-12:raise ValueError('Persistence minimum reduced exceedance')
                    rows.append(dict(event=key,boundary_rule=mode,horizon_h=horizon,shock_gw=qgw,retained_gw=rgw,
                        intervals=len(z),ree_gwh=math.fsum(z)/12000,chi=value,instantaneous_chi=base,delta_chi=value-base))
out=pd.DataFrame(rows)
for _,g in out.groupby(['event','boundary_rule','shock_gw','retained_gw']):
    if (np.diff(g.sort_values('horizon_h').chi)<-1e-12).any():raise ValueError('Nonmonotone horizon response')
wide=out.pivot(index=['event','horizon_h','shock_gw','retained_gw'],columns='boundary_rule',values='chi')
if (wide.full_horizon<wide.event_end_truncated-1e-12).any():raise ValueError('Full horizon smaller than truncated result')
out.to_csv(O/'persistence_sensitivity.csv',index=False)
report=dict(status='PASS',cases=len(rows),forward_minimum_algorithms=2,max_buffer_difference_mw=max_check_error,
    scope='Retrospective minimum of observed reserve capability, not energy-feasible reserve delivery or a calibration to unserved energy.')
(O/'persistence_verification.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
print(out.query("event=='january_2025' and shock_gw==15 and retained_gw==3").to_string(index=False))
