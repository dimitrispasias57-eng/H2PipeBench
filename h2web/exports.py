"""Charts and downloads all consume the same immutable result snapshot."""
from io import BytesIO
import json
import html
import threading
import pandas as pd
import plotly.graph_objects as go
from .inputs import MODELS

_plot_lock=threading.Lock()

COLORS={'ideal_isothermal':'#6688a5','real_isothermal':'#c97742','ideal_coupled':'#7868ac','real_coupled':'#087f8c'}
FIELDS={'Pressure':('p_Pa',1e6,'Pressure (MPa absolute)'),
        'Temperature':('T_K',1.,'Temperature (K)'),
        'Density':('rho_kg_m3',1.,'Density (kg/m³)'),
        'Velocity':('u_m_s',1.,'Velocity (m/s)'),
        'Reynolds number':('Re',1.,'Reynolds number (dimensionless)'),
        'Ground heat':('q_ground_W_m',1.,'Ground heat into gas (W/m)'),
        'Required heat':('q_used_W_m',1.,'Required heat into gas (W/m)'),
        'Thermostat duty':('thermostat_W_m',1.,'Thermostat heat into gas (W/m)')}

def frame(result):return pd.DataFrame(result['profile'])

def series(result,field,temperature_unit='K'):
    key,scale,label=FIELDS[field];data=frame(result)
    y=data[key]/scale
    if field=='Temperature' and temperature_unit=='°C':y=y-273.15;label='Temperature (°C)'
    return data.x_m/1000,y,label

def chart(results,field,temperature_unit='K'):
    fig=go.Figure()
    for result in results:
        x,y,label=series(result,field,temperature_unit);model=result['model']
        fig.add_scatter(x=x,y=y,mode='lines',name=' · '.join(MODELS[model]),
            line=dict(color=COLORS[model],width=2.5,dash='dash' if 'isothermal' in model else 'solid'),
            hovertemplate='%{x:.3f} km<br>%{y:.7g}<extra>%{fullData.name}</extra>')
    fig.update_layout(height=340,margin=dict(l=12,r=12,t=20,b=30),template='plotly_white',
        paper_bgcolor='rgba(0,0,0,0)',plot_bgcolor='rgba(0,0,0,0)',
        xaxis_title='Pipeline distance (km)',yaxis_title=label,
        legend=dict(orientation='h',y=-.25,x=0),hovermode='x unified',
        font=dict(family='Arial, sans-serif',color='#173044',size=13))
    return fig

def comparison_table(bundle):
    rows=[]
    for r in bundle['results']:
        s=r['summary'];end=r['profile'][-1]
        rows.append({'Model':MODELS[r['model']][0],'Formulation':MODELS[r['model']][1],
            'Outlet pressure (MPa)':s['p_out_Pa']/1e6,'Outlet temperature (K)':s['T_out_K'],
            'Pressure drop (kPa)':s['dp_Pa']/1000,'Outlet velocity (m/s)':end['u_m_s'],
            'Outlet Reynolds number':end['Re'],'Outlet Darcy factor':end['f_D'],
            'Ground heat (MW)':s['Q_ground_W']/1e6,'Required heat (MW)':s['Q_required_W']/1e6,
            'Thermostat duty (MW)':s['Q_thermostat_W']/1e6,'Status':'Full length reached'})
    return pd.DataFrame(rows)

def csv_bytes(data):return data.to_csv(index=False).encode('utf-8-sig')

def profiles_csv(bundle):
    frames=[]
    for r in bundle['results']:
        f=frame(r);f.insert(0,'model',r['model']);frames.append(f)
    return csv_bytes(pd.concat(frames,ignore_index=True)) if frames else b''

def json_bytes(bundle):return json.dumps(bundle,indent=2,ensure_ascii=False,allow_nan=False).encode('utf-8')

def inputs_json(bundle):
    return json_bytes({k:bundle[k] for k in ('schema_version','created_utc','operation','request','versions','web_version','assumptions','units')} | {
        'solved_pipeline_inputs_si':[{'model':r['model'],**r['pipeline_inputs_si']} for r in bundle['results']]})

def static_figure(bundle,field,fmt='svg',temperature_unit='K'):
    # Matplotlib is not generally thread-safe across concurrent Streamlit sessions.
    with _plot_lock:
        return _static_figure(bundle,field,fmt,temperature_unit)


def _static_figure(bundle,field,fmt,temperature_unit):
    # Server-side SVG/PNG uses the same returned profile arrays as Plotly.
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    fig=Figure(figsize=(8,4.5),layout='constrained');FigureCanvasAgg(fig);ax=fig.subplots()
    for r in bundle['results']:
        x,y,label=series(r,field,temperature_unit)
        ax.plot(x,y,label=' · '.join(MODELS[r['model']]),color=COLORS[r['model']],
                linestyle='--' if 'isothermal' in r['model'] else '-',linewidth=1.8)
    ax.set(xlabel='Pipeline distance (km)',ylabel=label);ax.grid(alpha=.2)
    ax.legend(fontsize=8);buf=BytesIO()
    fig.savefig(buf,format=fmt,dpi=180,metadata={'Date':None} if fmt=='svg' else {})
    return buf.getvalue()

def report_html(bundle):
    esc=html.escape
    table=comparison_table(bundle).to_html(index=False,float_format=lambda v:f'{v:.9g}')
    assumptions=''.join('<li>'+esc(a)+'</li>' for a in bundle['assumptions'])
    failures=''.join('<p>'+esc(e['model']+': '+e['message'])+'</p>' for e in bundle['errors'])
    comp=bundle['compressor'];comp_html=''
    if comp:
        comp_html='<h2>Compression accounting</h2><pre>'+esc(json.dumps(comp,indent=2))+'</pre>'
    diagnostics=[{'model':r['model'],**r['summary']} for r in bundle['results']]
    body=f'''<!doctype html><html lang="en"><meta charset="utf-8"><title>H2PipeBench simulation report</title>
    <style>body{{font:15px/1.6 Arial;color:#173044;max-width:1100px;margin:40px auto;padding:20px}}table{{border-collapse:collapse;font-size:12px}}th,td{{padding:8px;border-bottom:1px solid #ccc}}pre{{white-space:pre-wrap;overflow-wrap:anywhere}}.table{{overflow:auto}}</style>
    <h1>H2PipeBench · Simulation report</h1><p>{esc(bundle['created_utc'])} · Status: {esc(bundle['status'])}</p>
    <p><b>Research and educational use only.</b> Numerical verification does not establish full-scale experimental accuracy. Not certified for industrial design, safety, equipment selection or regulatory compliance.</p>
    <div class="table">{table}</div>{failures}{comp_html}<h2>Assumptions</h2><ul>{assumptions}</ul>
    <h2>Inputs, software and units</h2><pre>{esc(inputs_json(bundle).decode())}</pre>
    <h2>Numerical diagnostics</h2><pre>{esc(json.dumps(diagnostics,indent=2))}</pre>
    <p>Power is reported in W, kW or MW; no operating-duration energy calculation is implied. Missing/unbounded optional diagnostics are null, not zero.</p></html>'''
    return body.encode('utf-8')
