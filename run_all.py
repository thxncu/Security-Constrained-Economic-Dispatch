"""Reproduce and verify reviewer results in a NEW isolated directory.

Usage: python run_all.py [--output PATH]
No manuscript, archived release, network connection or pre-existing result is used.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata as metadata
import json
import math
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import time
sys.dont_write_bytecode=True
from verify_release import verify

ROOT=Path(__file__).resolve().parent
PACKAGES=('numpy','pandas','matplotlib','scipy','scikit-learn','Pillow')

def dump(path,value):
    path.write_text(json.dumps(value,indent=2,ensure_ascii=False,allow_nan=False)+'\n',encoding='utf-8')

def compare_csv(actual,expected):
    import numpy as np
    import pandas as pd
    a,b=pd.read_csv(actual),pd.read_csv(expected)
    if a.shape!=b.shape or list(a.columns)!=list(b.columns):raise ValueError(f'CSV structure mismatch: {actual.name}')
    error=0.;n=0
    for c in b.columns:
        if pd.api.types.is_numeric_dtype(a[c]) and pd.api.types.is_numeric_dtype(b[c]):
            x,y=a[c].to_numpy(float),b[c].to_numpy(float)
            if not np.allclose(x,y,rtol=1e-12,atol=1e-9,equal_nan=True):raise ValueError(f'Numerical mismatch: {actual.name}/{c}')
            finite=np.isfinite(x)&np.isfinite(y)
            if finite.any():error=max(error,float(np.max(np.abs(x[finite]-y[finite]))))
            n+=len(x)
        elif not a[c].fillna('<NA>').astype(str).equals(b[c].fillna('<NA>').astype(str)):
            raise ValueError(f'Text mismatch: {actual.name}/{c}')
    return dict(file=actual.name,status='PASS',rows=len(a),numeric_cells=n,max_absolute_difference=error)

def compare_json(a,b,key='root'):
    if isinstance(b,dict):
        if not isinstance(a,dict) or set(a)!=set(b):raise ValueError(f'JSON keys differ: {key}')
        for k in b:compare_json(a[k],b[k],f'{key}/{k}')
    elif isinstance(b,list):
        if not isinstance(a,list) or len(a)!=len(b):raise ValueError(f'JSON lists differ: {key}')
        for i,(x,y) in enumerate(zip(a,b)):compare_json(x,y,f'{key}/{i}')
    elif isinstance(b,(int,float)) and not isinstance(b,bool):
        if not isinstance(a,(int,float)) or not math.isclose(a,b,rel_tol=1e-12,abs_tol=1e-9):raise ValueError(f'JSON numbers differ: {key}')
    elif a!=b:raise ValueError(f'JSON values differ: {key}')

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=Path('reviewer_run'),help='New directory; relative paths are relative to the package.')
    args=p.parse_args()
    if sys.flags.optimize:p.error('Do not use -O; the scientific checks use assertions.')
    output=(args.output if args.output.is_absolute() else ROOT/args.output).resolve()
    if output.exists():p.error(f'Output already exists: {output}. Choose another --output path.')
    if output==ROOT or any(output.is_relative_to(ROOT/x) for x in ('data','code','reference')):
        p.error('Output must not be inside the source/reference directories.')
    verified=verify(ROOT)
    versions={name:metadata.version(name) for name in PACKAGES}
    output.mkdir(parents=True)
    work=output/'work';work.mkdir();logs=output/'logs';logs.mkdir()
    for path in (ROOT/'code').glob('*.py'):shutil.copy2(path,work/path.name)
    shutil.copytree(ROOT/'data',work/'data')
    (work/'results').mkdir();(work/'figures').mkdir()
    if any((work/'results').iterdir()):raise RuntimeError('Fresh results directory was not empty')
    started=time.perf_counter()
    report=dict(status='RUNNING',started_utc=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),
        dependencies=versions,manifest_files_verified=verified,reference_results_preseeded=False,steps=[])
    report_path=output/'run_report.json';dump(report_path,report)
    env=os.environ.copy();env.update(PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1',PYTHONIOENCODING='utf-8',MPLBACKEND='Agg',MPLCONFIGDIR=str(output/'plot_cache'))
    scripts=('verify_panels.py','analyze_r3.py','strict_checks.py','independent_numeric_audit.py','ancillary.py','supplement_figures.py','persistence_sensitivity.py','selection_check.py','reserve_tail_summary.py','publication_figures.py','check_figure_style.py')
    try:
        for script in scripts:
            print(f'Running {script} ...',flush=True);t=time.perf_counter()
            with (logs/(script[:-3]+'.log')).open('w',encoding='utf-8') as log:
                done=subprocess.run([sys.executable,str(work/script)],cwd=work,env=env,stdout=log,stderr=subprocess.STDOUT,check=False)
            step=dict(script=script,returncode=done.returncode,seconds=round(time.perf_counter()-t,6));report['steps'].append(step);dump(report_path,report)
            if done.returncode:raise RuntimeError(f'{script} failed. See logs/{script[:-3]}.log')
            print(f'  PASS ({step["seconds"]:.2f} s)',flush=True)
        comparisons=[]
        for ref in sorted((ROOT/'reference').iterdir()):
            actual=work/'results'/ref.name
            if not actual.is_file():raise FileNotFoundError(f'Not regenerated: {ref.name}')
            if ref.suffix=='.csv':comparisons.append(compare_csv(actual,ref))
            elif ref.suffix=='.json':
                compare_json(json.loads(actual.read_text()),json.loads(ref.read_text()),ref.name)
                comparisons.append(dict(file=ref.name,status='PASS'))
            else:raise ValueError(f'Unexpected reference type: {ref.name}')
        dump(output/'reference_comparison.json',dict(status='PASS',relative_tolerance=1e-12,absolute_tolerance=1e-9,files=comparisons))
        reports={name:json.loads((work/'results'/f'{name}.json').read_text()) for name in
                 ('verification','source_execution_verification','strict_verification','independent_numeric_audit','persistence_verification','selection_verification','reserve_tail_verification','figure_style_verification','publication_figure_verification')}
        if any(x['status']!='PASS' for x in reports.values()):raise ValueError('A scientific check did not pass')
        for original in (ROOT/'data').iterdir():
            if original.read_bytes()!=(work/'data'/original.name).read_bytes():raise ValueError(f'Input mutated: {original.name}')
        for svg in (work/'figures').glob('*.svg'):
            if '\u2014' in svg.read_text(encoding='utf-8'):raise ValueError(f'Em dash in figure: {svg.name}')
        manifest_after=verify(ROOT)
        n=reports['independent_numeric_audit']
        report.update(status='PASS',elapsed_seconds=round(time.perf_counter()-started,6),manifest_files_verified_after_run=manifest_after,
            compared_reference_files=len(comparisons),fixed_decimal_cases=n['fixed_decimal_cases'],wind_cases=n['wind_cases'],
            sensitivity_cases=n['sensitivity_cases'],randomized_property_assertions=n['randomized_property_assertions'],
            persistence_cases=reports['persistence_verification']['cases'],
            primary_full_lookahead_cases=80, boundary_convention_cases=80,
            selection_days_checked=reports['selection_verification']['days'],
            reserve_tail_events=reports['reserve_tail_verification']['events'],
            publication_figure_sets=len(reports['publication_figure_verification']['figures']),
            source_executions_checked=sum(x['source_executions_with_margins'] for x in reports['source_execution_verification']['events']),
            png_figures_generated=len(list((work/'figures').glob('*.png'))),
            figure_style_checked=reports['figure_style_verification']['png_files'],
            color_and_grayscale_safe=reports['figure_style_verification']['all_png_have_grayscale_contrast'],
            toy_normal_mean_sd_clip_bounds_mw=reports['figure_style_verification']['sampling_normal_mean_sd_clip_bounds_mw'],
            scope='Reproduction from included derived data. Does not audit DOCX, bibliography, upstream source measurements, or physical adequacy.')
        dump(report_path,report)
        print(f'PASS: {len(comparisons)} reference files matched; report: {report_path}',flush=True)
        return 0
    except Exception as e:
        report.update(status='FAIL',error=f'{type(e).__name__}: {e}',elapsed_seconds=round(time.perf_counter()-started,6));dump(report_path,report)
        print(f'FAIL: {e}',file=sys.stderr);return 1

if __name__=='__main__':
    raise SystemExit(main())
