"""Color styling that remains interpretable in grayscale print.

Series are distinguished redundantly by color, dash pattern, marker shape and,
where relevant, hatch pattern. Legends are outside the plotting area. Every
save records before/after data fingerprints for plotted curves so styling never
changes the underlying data.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.container import BarContainer
from matplotlib.collections import PolyCollection
from matplotlib.text import Text

mpl.rcParams.update({'font.family':'DejaVu Sans','font.size':9,
    'axes.titlesize':10,'axes.labelsize':9,'xtick.labelsize':8,'ytick.labelsize':8,
    'legend.fontsize':8,'svg.fonttype':'none','svg.hashsalt':'epsr-color-safe-20260923',
    'hatch.linewidth':.55,'figure.facecolor':'white','axes.facecolor':'white'})

# Okabe-Ito style palette for print and color-blind robustness.
COLORS={
    'blue':'#0072B2', 'orange':'#D55E00', 'green':'#009E73', 'red':'#CC79A7',
    'yellow':'#E69F00', 'sky':'#56B4E9', 'black':'#000000', 'gray':'#666666'
}
EVENT_STYLE={
    'january':dict(marker='o', color=COLORS['blue']),
    'elliott':dict(marker='s', color=COLORS['orange']),
    'uri':dict(marker='^', color=COLORS['green']),
    'february':dict(marker='D', color=COLORS['red']),
    'july':dict(marker='v', color=COLORS['yellow']),
}
DASHES=('-', '--', '-.', ':', (0,(6,2,1,2,1,2)))
HATCHES=('///','\\\\','...','xxx','+++')
PATCH_FACE=['#dbe9f6','#f8decc','#d8efe7','#eddaf0','#f6e3bf']


def area_geometry(fig):
    h = hashlib.sha256()
    for ax in fig.axes:
        for col in ax.collections:
            for path in col.get_paths():
                h.update(np.asarray(path.vertices, dtype=np.float64).tobytes())
                if path.codes is not None:
                    h.update(np.asarray(path.codes).tobytes())
        for container in ax.containers:
            if isinstance(container, BarContainer):
                for bar in container:
                    h.update(np.asarray([bar.get_x(), bar.get_y(), bar.get_width(), bar.get_height()], dtype=np.float64).tobytes())
    return h.hexdigest()


def _event_style_from_label(label):
    for event,style in EVENT_STYLE.items():
        if event in label:
            return style
    return dict(marker='o', color=COLORS['black'])


def style_line(line,index,name):
    label=line.get_label().lower()
    line.set_linewidth(1.35)
    line.set_markerfacecolor('white')
    line.set_markersize(4.3)
    line.set_markeredgewidth(.9)
    line.set_alpha(1)
    line.set_color(COLORS['black'])
    line.set_markeredgecolor(COLORS['black'])

    if name in ('fig2_shock_sweep','fig6_added_seasons'):
        s=_event_style_from_label(label)
        line.set_color(s['color'])
        line.set_markeredgecolor(s['color'])
        line.set_marker(s['marker'])
        line.set_linestyle('--' if 'retained 0' in label else '-')
        line.set_markevery(3)
    elif name.startswith(('fig4_','figS7_')):
        if 'shock' in label:
            line.set_linestyle(':')
            line.set_color(COLORS['orange'])
            line.set_markeredgecolor(COLORS['orange'])
            line.set_linewidth(1.45)
        elif 'residual' in label:
            hourly='hourly' in label
            line.set_linestyle((0,(6,2,1,2,1,2)) if hourly else '-.')
            line.set_marker('o' if hourly else 's')
            line.set_color(COLORS['red'] if hourly else COLORS['blue'])
            line.set_markeredgecolor(COLORS['red'] if hourly else COLORS['blue'])
            line.set_markevery(max(1,len(line.get_xdata())//10))
        elif 'minimum' in label:
            line.set_linestyle('--')
            line.set_color(COLORS['green'])
            line.set_markeredgecolor(COLORS['green'])
        else:
            line.set_linestyle('-')
            line.set_color(COLORS['black'])
            line.set_markeredgecolor(COLORS['black'])
    else:
        line.set_linestyle(DASHES[index%len(DASHES)])
        base_colors=[COLORS['blue'],COLORS['orange'],COLORS['green'],COLORS['red'],COLORS['yellow']]
        line.set_color(base_colors[index%len(base_colors)])
        line.set_markeredgecolor(base_colors[index%len(base_colors)])
        if index>1 and len(line.get_xdata())>20 and 'trigger' not in label:
            line.set_marker(('o','s','^','D','v')[index%5])
            line.set_markevery(max(1,len(line.get_xdata())//9))
        if 'hourly maximum rtordpa' in label:
            line.set_linestyle('--'); line.set_color(COLORS['gray']); line.set_markeredgecolor(COLORS['gray'])
        if '100% wind' in label:
            line.set_linestyle('--'); line.set_color(COLORS['green']); line.set_markeredgecolor(COLORS['green'])
        if '50% wind' in label:
            line.set_linestyle(':'); line.set_color(COLORS['sky']); line.set_markeredgecolor(COLORS['sky'])


def save_print(fig,name,directory,dpi=300):
    directory=Path(directory);directory.mkdir(exist_ok=True,parents=True)
    before_arrays=[(np.asarray(l.get_xdata(orig=False)).copy(),np.asarray(l.get_ydata(orig=False)).copy()) for a in fig.axes for l in a.lines]
    limits=[(a.get_xlim(),a.get_ylim()) for a in fig.axes]
    areas_before = area_geometry(fig)
    semantic=[];all_handles=[];all_labels=[];seen=set();line_index=0
    for ax in fig.axes:
        for line in ax.lines:
            style_line(line,line_index,name);line_index+=1
            if not line.get_label().startswith('_'):
                semantic.append({'label':line.get_label(),'linestyle':str(line.get_linestyle()),'marker':str(line.get_marker()),'color':str(line.get_color())})
        for j,col in enumerate(ax.collections):
            if isinstance(col,PolyCollection):
                face=PATCH_FACE[j%len(PATCH_FACE)]
                col.set_facecolor(face); col.set_edgecolor(COLORS['gray'])
                col.set_hatch(HATCHES[j%5]); col.set_alpha(.85); col.set_linewidth(.55); col.set_zorder(1)
        for j,c in enumerate(ax.containers):
            if isinstance(c,BarContainer):
                face=PATCH_FACE[j%len(PATCH_FACE)]
                for bar in c:
                    bar.set_facecolor(face); bar.set_edgecolor(COLORS['black']); bar.set_linewidth(.75)
                    bar.set_hatch(HATCHES[j%5]); bar.set_alpha(1)
        bar_ids={id(p) for c in ax.containers if isinstance(c,BarContainer) for p in c}
        for j,p in enumerate(ax.patches):
            if id(p) in bar_ids:continue
            if name=='fig1_workflow':
                p.set_edgecolor(COLORS['black']); p.set_facecolor('white'); p.set_fill(False)
            else:
                p.set_facecolor(PATCH_FACE[j%len(PATCH_FACE)]); p.set_edgecolor(COLORS['gray']); p.set_alpha(.9)
                p.set_hatch(HATCHES[j%5]); p.set_linewidth(.5); p.set_zorder(0.5)
        for line in ax.lines: line.set_zorder(3)
        for line in ax.get_xgridlines()+ax.get_ygridlines():
            line.set_color('#d0d0d0'); line.set_alpha(1); line.set_linewidth(.4); line.set_linestyle(':')
        for spine in ax.spines.values(): spine.set_color(COLORS['black']); spine.set_linewidth(.65)
        ax.tick_params(colors=COLORS['black'])
        ax.xaxis.label.set_color(COLORS['black']); ax.yaxis.label.set_color(COLORS['black'])
        handles,labels=ax.get_legend_handles_labels()
        for handle,label in zip(handles,labels):
            if label not in seen:
                all_handles.append(handle); all_labels.append(label); seen.add(label)
        if ax.legend_ is not None: ax.legend_.remove()
    for text in fig.findobj(Text): text.set_color(COLORS['black'])
    for legend in list(fig.legends): legend.remove()
    if all_handles:
        ncol=2 if len(all_handles)<=6 else 3
        rows=int(np.ceil(len(all_handles)/ncol)); extra=.26*rows+.18
        w,h=fig.get_size_inches(); fig.set_size_inches(w,h+extra)
        fig.tight_layout(rect=(0,extra/(h+extra),1,1),pad=.8)
        fig.legend(all_handles,all_labels,loc='lower center',bbox_to_anchor=(.5,.005),
            ncol=ncol,frameon=False,fontsize=7.4,handlelength=3.6,columnspacing=1.35)
    for ax,(xlim,ylim) in zip(fig.axes,limits): ax.set_xlim(xlim); ax.set_ylim(ylim)
    after_arrays=[(np.asarray(l.get_xdata(orig=False)),np.asarray(l.get_ydata(orig=False))) for a in fig.axes for l in a.lines]
    assert len(before_arrays)==len(after_arrays)
    for (x,y),(xx,yy) in zip(before_arrays,after_arrays):
        assert np.array_equal(x,xx,equal_nan=True) and np.array_equal(y,yy,equal_nan=True),name
    assert area_geometry(fig) == areas_before, (name, 'area geometry changed')
    assert all(a.get_xlim() == lim[0] and a.get_ylim() == lim[1] for a, lim in zip(fig.axes, limits)), (name, 'axis limits changed')
    fig.savefig(directory/f'{name}.png',dpi=dpi,bbox_inches='tight',facecolor='white')
    fig.savefig(directory/f'{name}.svg',bbox_inches='tight',facecolor='white',metadata={'Date':None})
    row={'figure':name,'plotted_arrays_unchanged':True,'axis_limits_unchanged':True,'area_geometry_unchanged':True,
         'raster_dpi':dpi,'series':semantic,'style':'color-plus-grayscale-safe'}
    log=directory/'figure_style_checks.json'
    info=json.loads(log.read_text()) if log.exists() else {}
    info[name]=row;log.write_text(json.dumps(info,indent=2,ensure_ascii=False)+'\n')
    plt.close(fig)
