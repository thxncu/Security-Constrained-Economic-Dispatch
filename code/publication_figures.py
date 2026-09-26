"""Generate the Submission-layout, color-plus-grayscale-safe article figures.

Each chart is drawn separately and then assembled. The two-column shock panels,
three-row native/hourly diagnostics, nested-band panels, and full-lookahead
persistence plot match the article. No manuscript files are needed at runtime.
"""
from pathlib import Path
from copy import deepcopy
import hashlib,json,re,xml.etree.ElementTree as ET
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
import matplotlib.dates as mdates
from PIL import Image
ROOT=Path(__file__).resolve().parent
F=ROOT/'figures';O=ROOT/'results';D=ROOT/'data';C=F/'components';C.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':9,'axes.labelsize':9,
    'axes.titlesize':9.5,'xtick.labelsize':8,'ytick.labelsize':8,'legend.fontsize':8,
    'svg.fonttype':'none','svg.hashsalt':'epsr-submission-merged','hatch.linewidth':0.55})
DPI=300
SPECS=json.loads((D/'events.json').read_text())
KEYS=['january_2025','elliott_2022','uri_2021','february_2022','july_2022']
# Original Submission colors, encoded redundantly by shape and line pattern.
PALETTE=['#2369a0','#d17c18','#37823c','#7654a1','#b84e5a']
MARKERS=['o','s','^','D','v'];DASHES=['-','--','-.',':',(0,(5,1.5,1,1.5,1,1.5))]
ST={k:dict(color=c,marker=m,linestyle=l) for k,c,m,l in zip(KEYS,PALETTE,MARKERS,DASHES)}
SVG='http://www.w3.org/2000/svg';XLINK='http://www.w3.org/1999/xlink'
ET.register_namespace('',SVG);ET.register_namespace('xlink',XLINK)
report={'status':'PASS','scope':'Numerical figure-source checks; not physical validation.','figures':{},'numeric_arrays_compared':0,'nested_sets_checked':0}


def save_component(fig,stem):
    fig.savefig(C/(stem+'.png'),dpi=DPI,facecolor='white')
    fig.savefig(C/(stem+'.svg'),facecolor='white',metadata={'Date':None})
    plt.close(fig);return C/stem


def common_axes(ax):
    ax.grid(True,axis='y',linestyle=':',linewidth=.5,color='0.78',zorder=0)
    for sp in ax.spines.values():sp.set_linewidth(.7);sp.set_color('0.2')
    ax.tick_params(width=.65,length=3)


def legend_panel(handles,labels,stem,width=6.6,height=.42,ncol=3,title=None):
    fig=plt.figure(figsize=(width,height))
    fig.legend(handles,labels,loc='center',ncol=ncol,frameon=False,handlelength=3.2,
               columnspacing=1.4,fontsize=8)
    if title:fig.text(.5,.98,title,ha='center',va='top',fontsize=9)
    return save_component(fig,stem)


def compose(stem,pieces):
    """pieces: (source stem, x in inch, y in inch); compose both raster and vector."""
    loaded=[];W=H=0.
    for source,x,y in pieces:
        im=Image.open(str(source)+'.png').convert('RGB')
        svg=ET.parse(str(source)+'.svg').getroot()
        vb=[float(v) for v in svg.attrib['viewBox'].split()];wi,hi=vb[2]/72,vb[3]/72
        loaded.append((source,x,y,wi,hi,im,svg));W=max(W,x+wi);H=max(H,y+hi)
    canvas=Image.new('RGB',(round(W*DPI),round(H*DPI)),(255,255,255))
    root=ET.Element('{'+SVG+'}svg',{'width':f'{W*72:g}pt','height':f'{H*72:g}pt','viewBox':f'0 0 {W*72:g} {H*72:g}'})
    ET.SubElement(root,'{'+SVG+'}rect',{'width':'100%','height':'100%','fill':'white'})
    for j,(source,x,y,wi,hi,im,svg) in enumerate(loaded):
        canvas.paste(im,(round(x*DPI),round(y*DPI)))
        ids={n.attrib['id']:f'p{j}_{n.attrib["id"]}' for n in svg.iter() if 'id' in n.attrib}
        for node in svg.iter():
            if 'id' in node.attrib:node.attrib['id']=ids[node.attrib['id']]
            for att,v in list(node.attrib.items()):
                if v.startswith('#') and v[1:] in ids:node.attrib[att]='#'+ids[v[1:]]
                else:node.attrib[att]=re.sub(r'url\(#([^\)]+)\)',lambda m:'url(#'+ids.get(m[1],m[1])+')',v)
        svg.set('x',f'{x*72:g}');svg.set('y',f'{y*72:g}');svg.set('width',f'{wi*72:g}');svg.set('height',f'{hi*72:g}')
        root.append(svg)
    canvas.save(F/(stem+'.png'),dpi=(DPI,DPI));ET.ElementTree(root).write(F/(stem+'.svg'),encoding='utf-8',xml_declaration=True)
    gray=canvas.convert('L');gray.save(F/(stem+'_grayscale.png'),dpi=(DPI,DPI))
    return {'png':stem+'.png','svg':stem+'.svg','width_px':canvas.width,'height_px':canvas.height,'grayscale_preview':stem+'_grayscale.png'}


def assert_line(line,x,y):
    assert np.array_equal(np.asarray(line.get_xdata(orig=False)),np.asarray(x,dtype=float))
    assert np.allclose(np.asarray(line.get_ydata(orig=False)),np.asarray(y,dtype=float),rtol=0,atol=1e-14)
    report['numeric_arrays_compared']+=1

surf=pd.read_csv(O/'sensitivity_surface.csv')
# Fig. 2 and Fig. 6: independent plots composed side by side.
for fname,keys in [('fig2_submission',KEYS[:3]),('fig6_submission',KEYS[3:])]:
    pieces=[]
    for j,r in enumerate([0,3]):
        fig=plt.figure(figsize=(3.3,2.6));ax=fig.add_axes([.18,.23,.78,.64]);common_axes(ax)
        for k in keys:
            g=surf.query('event==@k and retained_gw==@r and basis=="PRC" and start_shift_h==0 and end_shift_h==0').sort_values('shock_gw')
            assert len(g)==25
            line,=ax.plot(g.shock_gw,g.chi,**ST[k],markerfacecolor='white',markersize=4.3,markevery=3,linewidth=1.4,label=SPECS[k][3])
            assert_line(line,g.shock_gw,g.chi)
        ax.set(xlim=(1,25),ylim=(0,1),xlabel='Shock magnitude (GW)',ylabel='Conditional attenuation, χ',title=f'({"ab"[j]}) Retained reserve {r} GW')
        ax.set_xticks([1,5,10,15,20,25]);ax.set_yticks(np.arange(0,1.01,.2))
        pieces.append((save_component(fig,fname+f'_r{r}'),j*3.3,.33))
    fig=plt.figure(figsize=(6.6,.33));fig.text(.5,.5,'Higher χ indicates a larger nominal reserve-exceedance share',ha='center',va='center',fontsize=9)
    pieces.append((save_component(fig,fname+'_title'),0,0))
    handles=[Line2D([],[],**ST[k],markerfacecolor='white',linewidth=1.4,markersize=4.3) for k in keys]
    pieces.append((legend_panel(handles,[SPECS[k][3] for k in keys],fname+'_legend',ncol=len(keys)),0,2.93))
    report['figures'][fname]=compose(fname,pieces)
    report['figures'][fname]['panels']=2
    report['figures'][fname]['color_independent_encodings']=[{'event':k,**{a:str(b) for a,b in ST[k].items()}} for k in keys]

# Fig. 4: 3 independent stepped plots with shared outside legend.
TRACE=[('prc_mw','Five-minute PRC','#2369a0','-',None),
       ('hourly_min_prc_mw','Hourly-minimum PRC','#7654a1','--',None),
       ('shock_mw','Imposed shock','0.20',':',None),
       ('native_residual_mw','Native residual','#d17c18','-.','s'),
       ('hourly_min_residual_mw','Hourly-minimum residual','#b84e5a',(0,(6,2,1,2,1,2)),'o')]
pieces=[]
handles=[Line2D([],[],color=c,linestyle=ls,marker=mk,markerfacecolor='white',linewidth=1.3,markersize=4) for _,_,c,ls,mk in TRACE]
pieces.append((legend_panel(handles,[t[1] for t in TRACE],'fig4_submission_legend',height=.65,ncol=3),0,0))
for j,k in enumerate(KEYS[:3]):
    g=pd.read_csv(O/f'diagnostic_{k}.csv',parse_dates=['slot']);end=g.slot.iloc[-1]+pd.Timedelta(minutes=5)
    gx=pd.concat([g,pd.DataFrame([{**g.iloc[-1].to_dict(),'slot':end}])],ignore_index=True)
    fig=plt.figure(figsize=(6.6,2.0));ax=fig.add_axes([.10,.25,.87,.57]);common_axes(ax)
    for col,label,c,ls,mk in TRACE:
        yy=gx[col].to_numpy(float)/1000
        line,=ax.step(gx.slot,yy,where='post',color=c,linestyle=ls,marker=mk,markerfacecolor='white',markeredgecolor=c,
                     markersize=3.8,markevery=8,linewidth=1.3,label=label)
        assert_line(line,mdates.date2num(gx.slot),yy)
    ax.set(xlim=(g.slot.iloc[0],end),ylabel='Power (GW)',xlabel='ERCOT local time',title=f'({"abc"[j]}) {SPECS[k][3]}: {g.slot.iloc[0]:%d %B %Y}')
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1));ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    # Independent integration of the plotted source arrays.
    native=g.native_residual_mw.sum()/12000;hourly=g.hourly_min_residual_mw.sum()/12000
    win=pd.read_csv(O/'diagnostic_windows.csv');row=win[win.event==k].iloc[0]
    # Compare integrated plotted traces directly with the diagnostic source table.
    assert np.isclose(native,row.native_gwh,rtol=0,atol=1e-10)
    assert np.isclose(hourly,row.hourly_min_gwh,rtol=0,atol=1e-10)
    assert hourly>=native
    pieces.append((save_component(fig,f'fig4_submission_{k}'),0,.65+j*2.0))
report['figures']['fig4_submission']=compose('fig4_submission',pieces)
report['figures']['fig4_submission'].update(panels=3,trace_encodings=[{'label':lab,'color':c,'linestyle':str(ls),'marker':str(mk)} for _,lab,c,ls,mk in TRACE])

# Fig. 5: nested deterministic sets with sparse/medium/dense hatching.
BANDS=[('All buffers + retention + endpoints',54,'#d2d9df','/',1),
       ('Retention + endpoints (PRC)',18,'#9dbacf','///',2),
       ('Endpoints only (PRC, retained 3 GW)',9,'#edc995','//////',3)]
handles=[Patch(facecolor=c,edgecolor='0.35',hatch=h,linewidth=.45,label=label) for label,_,c,h,_ in BANDS]
handles.append(Line2D([],[],color='black',linewidth=1.5,marker='o',markerfacecolor='white',markersize=3.5))
labels=[b[0] for b in BANDS]+['Central PRC, retained 3 GW']
pieces=[(legend_panel(handles,labels,'fig5_submission_legend',height=.68,ncol=2),0,0)];outrows=[]
for j,k in enumerate(KEYS[:3]):
    g=surf[surf.event==k];xs=np.arange(1,26);bounds=[]
    for _,n,_,_,_ in BANDS:
        sub=g if n==54 else g[g.basis=='PRC'] if n==18 else g[(g.basis=='PRC')&(g.retained_gw==3)]
        assert (sub.groupby('shock_gw').size()==n).all()
        v=sub.groupby('shock_gw').chi.agg(['min','max']).reindex(xs);bounds.append((v['min'].to_numpy(),v['max'].to_numpy()))
    for a,b in zip(bounds,bounds[1:]):
        assert (a[0]<=b[0]+1e-12).all() and (a[1]>=b[1]-1e-12).all()
    central=g.query('basis=="PRC" and retained_gw==3 and start_shift_h==0 and end_shift_h==0').sort_values('shock_gw').chi.to_numpy()
    report['nested_sets_checked']+=25
    for i,qgw in enumerate(xs):outrows.append(dict(event=k,shock_gw=int(qgw),outer_min=bounds[0][0][i],outer_max=bounds[0][1][i],middle_min=bounds[1][0][i],middle_max=bounds[1][1][i],inner_min=bounds[2][0][i],inner_max=bounds[2][1][i],central_chi=central[i]))
    fig=plt.figure(figsize=(6.6,1.78));ax=fig.add_axes([.10,.27,.87,.54]);common_axes(ax)
    for (_,_,color,hatch,z),(lo,hi) in zip(BANDS,bounds):
        ax.fill_between(xs,lo,hi,facecolor=color,edgecolor='0.35',hatch=hatch,linewidth=.45,zorder=z,alpha=1)
    line,=ax.plot(xs,central,color='black',linestyle='-',marker='o',markevery=4,markerfacecolor='white',markersize=3.5,linewidth=1.45,zorder=5)
    assert_line(line,xs,central)
    ax.set(xlim=(1,25),ylim=(0,1),ylabel='χ',xlabel='Shock magnitude (GW)',title=f'({"abc"[j]}) {SPECS[k][3]}')
    ax.set_xticks([1,5,10,15,20,25]);ax.set_yticks([0,.25,.5,.75,1])
    pieces.append((save_component(fig,f'fig5_submission_{k}'),0,.68+j*1.78))
pd.DataFrame(outrows).to_csv(O/'publication_nested_bands.csv',index=False)
report['figures']['fig5_submission']=compose('fig5_submission',pieces)
report['figures']['fig5_submission'].update(panels=3,nested_counts=[9,18,54],hatches_by_increasing_set_size=['//////','///','/'])

# Fig. 7: full lookahead only; no truncated rows may enter this plot.
persist=pd.read_csv(O/'persistence_sensitivity.csv')
g=persist.query('boundary_rule=="full_horizon" and shock_gw==15 and retained_gw==3')
assert len(g)==20
fig=plt.figure(figsize=(6.6,2.8));ax=fig.add_axes([.10,.23,.87,.68]);common_axes(ax)
for k in KEYS:
    z=g[g.event==k].sort_values('horizon_h');line,=ax.plot(z.horizon_h,z.chi,**ST[k],markerfacecolor='white',markersize=5,linewidth=1.4,label=SPECS[k][3])
    assert_line(line,z.horizon_h,z.chi)
ax.set(xlim=(-.1,4.1),ylim=(0,1),xticks=[0,1,2,4],xlabel='Forward-minimum horizon (hours; 0 = native)',ylabel='Conditional attenuation, χ')
pieces=[(save_component(fig,'fig7_submission_core'),0,0)]
handles=[Line2D([],[],**ST[k],markerfacecolor='white',linewidth=1.4,markersize=4.3) for k in KEYS]
pieces.append((legend_panel(handles,[SPECS[k][3] for k in KEYS],'fig7_submission_legend',height=.6,ncol=3),0,2.8))
report['figures']['fig7_submission']=compose('fig7_submission',pieces)
report['figures']['fig7_submission'].update(panels=1,boundary_rule='full_horizon',plotted_cases=20)
# Redundant shape/pattern encodings remain unique without the color attribute.
assert len({(str(ST[k]['linestyle']),ST[k]['marker']) for k in KEYS})==len(KEYS)
assert len({(str(t[3]),str(t[4])) for t in TRACE})==len(TRACE)
assert len({b[3] for b in BANDS})==3
for figrec in report['figures'].values():
    sx=ET.parse(F/figrec['svg']).getroot()
    ids=[n.attrib['id'] for n in sx.iter() if 'id' in n.attrib]
    assert len(ids)==len(set(ids)),figrec['svg']
report['grayscale_independent_encodings_unique']=True
report['composite_svg_ids_unique']=True
# Core snapshot excludes data arrays from stylistic validation only; numerical assertions above bind them.
(O/'publication_figure_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='figures'},indent=2))
