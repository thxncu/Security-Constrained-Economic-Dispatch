"""Regenerate Supplement Figures S1-S5 from the corrected R3 panels.

Each time-series component is a separate figure, then composited for the article.
The data CSVs remain authoritative. Hour-start labels and exclusive right endpoints
are retained; time traces are piecewise constant wherever that is the model.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from PIL import Image
from print_style import save_print
R=Path(__file__).resolve().parent; F=R/'figures'; F.mkdir(exist_ok=True)
S=json.loads((R/'data/events.json').read_text()); ORDER=['uri_2021','elliott_2022','january_2025']
H={k:pd.read_csv(R/'data'/f'{k}_hourly.csv',parse_dates=['datetime']).set_index('datetime') for k in ORDER}
D={k:pd.read_csv(R/'data'/f'{k}_reserve.csv',parse_dates=['slot']).set_index('slot') for k in ORDER}
def save(fig,name):
    save_print(fig,name,F)
def timed(fig,ax,k):
    ax.set_title(S[k][3],fontsize=11);ax.set_xlabel('ERCOT local time',fontsize=9)
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %d'))
    ax.tick_params(labelsize=9);ax.grid(True,alpha=.18)
    ax.set_xlim(pd.Timestamp(S[k][0]),pd.Timestamp(S[k][1]))
    fig.tight_layout(pad=.8)
def extend(series,end):
    out=series.copy();out.loc[pd.Timestamp(end)]=out.iloc[-1];return out
for k in ORDER:
    h=H[k]; d=D[k]; end=S[k][1]
    # S1: reported hourly load and minimum PRC in each covered hour.
    fig,ax=plt.subplots(figsize=(7.3,2.75));
    for series,label,style in [(h.load_mw,'Hourly load','-'),(d.prc_mw.groupby(d.index.floor('h')).min(),'Hourly-minimum PRC','--')]:
        z=extend(series,end);ax.step(z.index,z/1000,where='post',label=label,linestyle=style,linewidth=1.1)
    ax.set_ylabel('Power (GW)',fontsize=9);ax.legend(fontsize=8,ncol=2);timed(fig,ax,k);save(fig,'s1_'+k)
    # S2: mean hourly residual and maximum hourly adder; dual axes explicitly identified.
    res=np.maximum(15000-np.maximum(d.prc_mw-3000,0),0).groupby(d.index.floor('h')).mean()/1000
    ad=d.rtordpa.groupby(d.index.floor('h')).max()
    fig,ax=plt.subplots(figsize=(7.3,2.75));z=extend(res,end)
    a=ax.step(z.index,z,where='post',label='Mean hourly residual (left)',linewidth=1.1)
    ax.set_ylabel('Residual (GW)',fontsize=9)
    ar=ax.twinx();z=extend(ad,end);b=ar.step(z.index,z,where='post',label='Hourly maximum RTORDPA (right)',linestyle='--',linewidth=1.0)
    ar.set_yscale('symlog',linthresh=1);ar.set_ylabel('Adder (USD/MWh)',fontsize=9);ar.tick_params(labelsize=8)
    ax.legend(a+b,[x.get_label() for x in a+b],fontsize=7.5,ncol=2,loc='upper right');timed(fig,ax,k);save(fig,'s2_'+k)
    # S4: no raw five-minute trajectory is mislabeled as an hourly minimum.
    fig,ax=plt.subplots(figsize=(7.3,2.75));
    for series,label,style in [(d.prc_mw.groupby(d.index.floor('h')).min(),'Hourly-minimum PRC','-'),(h.wind_mw,'100% wind-shaped shock','--'),(.5*h.wind_mw,'50% wind-shaped shock',':')]:
        z=extend(series,end);ax.step(z.index,z/1000,where='post',label=label,linestyle=style,linewidth=1.0)
    ax.set_ylabel('Power (GW)',fontsize=9);ax.legend(fontsize=7.5,ncol=3,loc='upper right');timed(fig,ax,k);save(fig,'s4_'+k)
for n in ['s1','s2','s4']:
    ims=[Image.open(F/f'{n}_{k}.png').convert('RGB') for k in ORDER];w=max(im.width for im in ims)
    canvas=Image.new('RGB',(w,sum(im.height for im in ims)),(255,255,255));y=0
    for im in ims:canvas.paste(im,(0,y));y+=im.height
    canvas.save(F/f'fig_{n}_corrected.png')
# S3: the common fixed-shock comparison is unchanged by hourly fuel corrections.
df=pd.read_csv(R/'results/fixed_shocks.csv');keys=['january_2025','elliott_2022','uri_2021']
fig,ax=plt.subplots(figsize=(7.3,3.8));x=np.arange(3);width=.34
for j,r in enumerate([0,3]):
    vals=[float(df[(df.event==k)&(df.shock_gw==15)&(df.retained_gw==r)].chi.iloc[0]) for k in keys]
    bars=ax.bar(x+(j-.5)*width,vals,width,label=f'Retained reserve {r} GW')
    ax.bar_label(bars,labels=[f'{v:.3f}' for v in vals],fontsize=9,padding=3)
ax.set_xticks(x,['January 2025','Elliott 2022','Uri 2021']);ax.set_ylabel('Conditional attenuation factor, χ');ax.set_ylim(0,1.05)
ax.legend(fontsize=9);fig.tight_layout();save(fig,'fig_s3_corrected')
# S5: all five category values are read at the exact peak-load hour.
fig,ax=plt.subplots(figsize=(7.3,3.8));cols=['wind_mw','solar_mw','gas_mw','coal_mw','nuclear_mw'];x=np.arange(len(cols));width=.24
for j,k in enumerate(ORDER):
    h=H[k];t=h.load_mw.idxmax();vals=h.loc[t,cols].astype(float).to_numpy()/1000
    ax.bar(x+(j-1)*width,vals,width,label=f'{S[k][3]} ({t:%b %d %H:%M})')
ax.set_xticks(x,['Wind','Solar','Gas','Coal','Nuclear']);ax.set_ylabel('Hourly-average output (GW)');ax.legend(fontsize=8)
fig.tight_layout();save(fig,'fig_s5_corrected')
print('Regenerated Figures S1-S5 from corrected working panels.')
