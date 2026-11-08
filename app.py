"""H2PipeBench — Hydrogen Pipeline Simulator. Run: streamlit run app.py."""
from pathlib import Path
import time
import streamlit as st
from h2pipebench import __version__ as SOLVER_VERSION
from h2web import __version__ as WEB_VERSION
from h2web.inputs import DEFAULTS, BOUNDS, COMPRESSOR_DEFAULTS, COMPRESSOR_BOUNDS, MODELS, make_request, InputError
from h2web.service import run_request, ServiceError, SESSION_INTERVAL_S
from h2web.exports import chart, comparison_table, frame, profiles_csv, csv_bytes, inputs_json, json_bytes, report_html, static_figure
from h2web.methodology import show_methodology

ROOT=Path(__file__).resolve().parent
st.set_page_config(page_title='H2PipeBench · Hydrogen Pipeline Simulator',page_icon='🔬',layout='wide',initial_sidebar_state='collapsed')
st.html('''<style>
.block-container{max-width:1540px;padding-top:4.5rem;padding-bottom:3rem}
h1,h2,h3{letter-spacing:-.025em}h1{font-size:2.8rem!important}
[data-testid="stMetric"]{background:#fff;border:1px solid #e0e8ed;border-radius:12px;padding:16px 18px}
[data-testid="stMetricLabel"]{color:#536b7d}[data-testid="stMetricValue"]{font-size:1.8rem}
[data-testid="stForm"]{background:white;border-color:#dce5eb;border-radius:14px}
[data-testid="stMarkdownContainer"]>.katex-display{max-width:100%;overflow-x:auto}
[data-testid="stMarkdownContainer"] table{display:block;max-width:100%;overflow-x:auto}
.eyebrow{color:#087f8c;font-size:.77rem;font-weight:700;letter-spacing:.13em;text-transform:uppercase}
.hero-sub{color:#536b7d;font-size:1.15rem;margin-top:-.5rem}.badge{display:inline-block;background:#e2f2f1;color:#075e68;padding:5px 10px;border-radius:20px;font-size:.8rem}
@media(max-width:700px){.block-container{padding:4rem 1rem 2rem}h1{font-size:2.1rem!important}[data-testid="stMetricValue"]{font-size:1.5rem}}
</style>''')
st.html('<div class="eyebrow">Pure hydrogen · steady flow · reproducible calculations</div>')
st.title('H2PipeBench')
st.html('<p class="hero-sub">Hydrogen Pipeline Thermal–Hydraulic Simulator</p>')
st.write('An open-source research tool for simulating pressure, temperature and energy behaviour in high-pressure hydrogen pipelines.')
st.caption('One-dimensional research model · MIT licence · Numerical verification is not experimental validation.')
page=st.radio('Workspace',['Simulator','Model comparison','Compression','Method & limits','Software'],horizontal=True,label_visibility='collapsed',key='workspace')

def number(label,key,limits,values,help=None,step=None,format=None):
    low,high=limits[key]
    kw={'min_value':float(low),'max_value':float(high),'value':float(values[key]),'key':key,'help':help}
    if step is not None:kw['step']=float(step)
    if format:kw['format']=format
    return st.number_input(label,**kw)

def configuration(compression=False):
    values={};draft=st.session_state.get('draft',DEFAULTS)
    with st.expander('1 · Pipeline configuration',expanded=True):
        a,b=st.columns(2)
        with a:
            values['length_km']=number('Length (km)','length_km',BOUNDS,draft,step=1.,format='%.2f',
                help='Use the arrows for 1 km changes, or type a decimal length such as 12.5 km. This input sets physical pipe length, not the numerical integration step.')
            values['wall_mm']=number('Wall thickness (mm)','wall_mm',BOUNDS,draft,step=1.)
            values['burial_m']=number('Burial depth (m)','burial_m',BOUNDS,draft,help='Ground surface to pipe centreline; must exceed the outside radius.',step=.1)
        with b:
            values['diameter_mm']=number('Inner diameter (mm)','diameter_mm',BOUNDS,draft,step=50.)
            values['roughness_um']=number('Roughness (µm)','roughness_um',BOUNDS,draft,help='Equivalent sand-grain roughness, not a directly interchangeable surface metrology parameter.',step=5.)
            values['wall_conductivity']=number('Wall conductivity (W/(m K))','wall_conductivity',BOUNDS,draft,step=5.)
    with st.expander('2 · Hydrogen operating conditions',expanded=True):
        values['inlet_MPa']=number('Inlet pressure (MPa absolute)','inlet_MPa',BOUNDS,draft,step=.5,
            help='Forward-run inlet pressure. For delivery inversion, this value is only an initially valid configuration; the solver searches for the required inlet pressure.')
        a,b=st.columns(2)
        with a:values['inlet_K']=number('Inlet temperature (K)','inlet_K',BOUNDS,draft,help='313.15 K = 40 °C. Also the compressor aftercooler boundary.',step=5.)
        with b:values['mass_flow']=number('Mass flow (kg/s)','mass_flow',BOUNDS,draft,step=.5,format='%.4f')
    with st.expander('3 · Environmental & thermal conditions'):
        values['soil_K']=number('Soil temperature (K)','soil_K',BOUNDS,draft,help='Prescribed stationary far-field temperature. 283.15 K = 10 °C.',step=5.)
        values['soil_conductivity']=number('Soil conductivity (W/(m K))','soil_conductivity',BOUNDS,draft,step=.1)
        values['adiabatic']=st.checkbox('Adiabatic environment',value=draft['adiabatic'],key='adiabatic',help='Disable environmental heat only. Isothermal models can still require thermostat heat.')
    with st.expander('4 · Numerical model selection',expanded=True):
        if page=='Model comparison':
            st.selectbox('Physical models',['All four models (M1–M4)'],disabled=True,key='comparison_models')
            st.caption('Run Simulation solves M1, M2, M3 and M4 with identical pipeline inputs.')
            model='real_coupled'  # Ignored by make_request for a four-model comparison.
        else:
            model=st.selectbox('Physical model',list(MODELS),format_func=lambda m:' — '.join(MODELS[m]),key='model')
        st.caption('Isothermal: imposed constant temperature. Non-isothermal: pressure and energy solved together. Real gas uses HEOS; ideal gas retains HEOS transport properties.')
        values['friction']=st.selectbox('Darcy friction',['colebrook','haaland'],index=['colebrook','haaland'].index(draft['friction']),key='friction')
        values['heat']=st.selectbox('Internal heat transfer',['gnielinski','dittus_boelter'],index=['gnielinski','dittus_boelter'].index(draft['heat']),key='heat')
        values['acceleration']=st.checkbox('Include acceleration and kinetic energy',value=draft['acceleration'],key='acceleration')
        st.caption('DOP853 · relative tolerance 2×10⁻⁸ · maximum step L/40. Full-length and local admissibility checks remain active.')
    comp=None
    if compression:
        with st.expander('Compressor boundary conditions',expanded=True):
            d=st.session_state.get('compressor_draft',COMPRESSOR_DEFAULTS);comp={}
            comp['delivery_MPa']=number('Target outlet pressure (MPa absolute)','delivery_MPa',COMPRESSOR_BOUNDS,d,step=.5)
            comp['suction_MPa']=number('Suction pressure (MPa absolute)','suction_MPa',COMPRESSOR_BOUNDS,d,step=.5)
            comp['suction_K']=number('Suction temperature (K)','suction_K',COMPRESSOR_BOUNDS,d,step=5.)
            a,b=st.columns(2)
            with a:comp['eta_is']=number('Isentropic efficiency','eta_is',COMPRESSOR_BOUNDS,d,step=.01)
            with b:comp['eta_motor']=number('Motor efficiency','eta_motor',COMPRESSOR_BOUNDS,d,step=.01)
            st.caption('Uses the pipeline mass flow above. Aftercooler outlet equals the pipeline inlet temperature. The inverse search determines inlet pressure below 30 MPa.')
    return values,model,comp

def reset_example():
    for k,v in DEFAULTS.items():st.session_state[k]=v
    for k,v in COMPRESSOR_DEFAULTS.items():st.session_state[k]=v
    st.session_state['model']='real_coupled'
    st.session_state['draft']=dict(DEFAULTS)
    st.session_state['compressor_draft']=dict(COMPRESSOR_DEFAULTS)
    st.session_state.pop('bundle',None);st.session_state.pop('run_error',None)

def show_downloads(bundle,tempunit):
    with st.expander('Download results, inputs & report'):
        st.caption('Exports describe the displayed completed run. CSV profiles use SI units; JSON records input conversions, model, software versions, assumptions and diagnostics. No session identifiers or server configuration are included.')
        a,b,c=st.columns(3)
        a.download_button('Profiles · CSV',profiles_csv(bundle),'h2pipebench_profiles.csv','text/csv',key='dl_profiles')
        b.download_button('Inputs · JSON',inputs_json(bundle),'h2pipebench_inputs.json','application/json',key='dl_inputs')
        c.download_button('Results · JSON',json_bytes(bundle),'h2pipebench_results.json','application/json',key='dl_results')
        a.download_button('Summary · CSV',csv_bytes(comparison_table(bundle)),'h2pipebench_summary.csv','text/csv',key='dl_summary')
        b.download_button('Simulation report',report_html(bundle),'h2pipebench_report.html','text/html',key='dl_report')
        field=st.selectbox('Figure to download',['Pressure','Temperature','Density','Velocity','Reynolds number','Ground heat','Required heat','Thermostat duty'],key='download_field')
        # Explicit preparation avoids generating static figures on every input rerun.
        if st.button('Prepare PNG and SVG',key='prepare_figures'):
            st.session_state['figure_download']=(bundle['created_utc'],field,tempunit,
                static_figure(bundle,field,'png',tempunit),static_figure(bundle,field,'svg',tempunit))
        saved=st.session_state.get('figure_download')
        if saved and saved[:3]==(bundle['created_utc'],field,tempunit):
            a,b=st.columns(2)
            a.download_button('Download PNG',saved[3],f'h2pipebench_{field.lower().replace(" ","_")}.png','image/png')
            b.download_button('Download SVG',saved[4],f'h2pipebench_{field.lower().replace(" ","_")}.svg','image/svg+xml')

def show_results(bundle):
    st.subheader('Simulation results' if bundle['operation']!='compressor' else 'Delivery & compressor results')
    for error in bundle['errors']:st.error(MODELS[error['model']][0]+': '+error['message'])
    if not bundle['results']:return
    st.caption(f"Completed run · {bundle['created_utc']} · H2PipeBench {bundle['versions']['h2pipebench']}. Results below use this run’s saved inputs; editing the form does not recompute them.")
    if bundle['status']=='partial':st.warning('Only the successful models are plotted. Failed models have no substituted results; this is an incomplete comparison.')
    tempunit=st.radio('Temperature display',['K','°C'],horizontal=True,key='display_temperature')
    comp=bundle['compressor']
    if comp:
        a,b,c=st.columns(3)
        a.metric('Required inlet pressure',f"{comp['required_inlet_Pa']/1e6:.6f} MPa")
        b.metric('Total electrical power',f"{comp['total']['electric_power_W']/1e6:.6f} MW")
        c.metric('Incremental transport power',f"{comp['incremental_electric_power_W']/1000:.3f} kW")
        st.write(f"Common delivery baseline: **{comp['baseline']['electric_power_W']/1e6:.6f} MW**. Aftercooler heat removed: **{comp['total']['aftercooler_heat_removed_W']/1e6:.6f} MW**. Delivery residual: **{comp['delivery_residual_Pa']:.3g} Pa**.")
        st.caption(comp['assumptions'])
        st.info('These are power rates, not energy in kWh/MWh or equipment ratings. Negative aftercooler duty means heating is required. Cooling-system electricity is not included.')
    if len(bundle['results'])==1:
        r=bundle['results'][0];s=r['summary'];end=r['profile'][-1]
        a,b,c=st.columns(3)
        a.metric('Outlet pressure',f"{s['p_out_Pa']/1e6:.6f} MPa")
        b.metric('Outlet temperature',f"{s['T_out_K']-(273.15 if tempunit=='°C' else 0):.3f} {tempunit}")
        c.metric('Pressure drop',f"{s['dp_Pa']/1000:.3f} kPa")
        a,b,c=st.columns(3)
        a.metric('Outlet velocity',f"{end['u_m_s']:.4f} m/s")
        b.metric('Outlet Reynolds number',f"{end['Re']:,.0f}")
        c.metric('Outlet Darcy factor',f"{end['f_D']:.6f}")
    st.success('Full pipeline length reached for every displayed profile. Numerical checks are reported below; this is not experimental validation.')
    # Stack the two primary plots to keep all model legends readable on laptops and phones.
    for field in ('Pressure','Temperature'):
        st.markdown('**'+field+' profile**')
        st.plotly_chart(chart(bundle['results'],field,tempunit),width='stretch',key='plot_'+field,
            config={'displaylogo':False,'toImageButtonOptions':{'format':'png','filename':'h2pipebench_'+field.lower(),'scale':2}})
    if len(bundle['results'])>1:
        st.markdown('**Model comparison · identical geometry and inlet conditions**')
        st.dataframe(comparison_table(bundle),hide_index=True,width='stretch')
        st.caption('Differences are formulation sensitivity, not measured accuracy. M4 is a real-gas coupled prediction, not experimentally validated truth.')
    with st.expander('Heat accounting & numerical diagnostics'):
        for r in bundle['results']:
            s=r['summary'];st.markdown('**'+' — '.join(MODELS[r['model']])+'**')
            st.write(f"Ground heat: {s['Q_ground_W']/1e6:.6g} MW · required heat: {s['Q_required_W']/1e6:.6g} MW · thermostat: {s['Q_thermostat_W']/1e6:.6g} MW. Positive heat enters the gas.")
            st.write(f"Mass consistency: {s['mass_relative']:.3g} · normalized momentum residual: {s['momentum_relative']:.3g} · normalized energy residual: {s['energy_relative']:.3g}.")
            st.caption(f"Momentum residual {s['momentum_residual_Pa']:.6g} Pa; total-energy residual {s['energy_residual_J_kg']:.6g} J/kg; {s['accepted_steps']} accepted steps; {s['nfev']} RHS evaluations; {s['audit_points']} audit samples. A returned result has status {s['status']} in the solver.")
            st.json(s,expanded=False)
    with st.expander('Additional profiles & full numerical data'):
        field=st.selectbox('Diagnostic profile',['Density','Velocity','Reynolds number','Ground heat','Required heat','Thermostat duty'])
        st.plotly_chart(chart(bundle['results'],field,tempunit),width='stretch',key='diagnostic_chart',config={'displaylogo':False})
        for r in bundle['results']:
            st.caption(' — '.join(MODELS[r['model']])+' · SI data; null means unavailable/unbounded, not zero.')
            st.dataframe(frame(r),hide_index=True,width='stretch',height=230)
    show_downloads(bundle,tempunit)

if page in ('Simulator','Model comparison','Compression'):
    if page=='Model comparison':st.info('Compare M1–M4 with exactly the same inputs. Each model must independently satisfy its trajectory and correlation checks.')
    left,right=st.columns([.38,.62],gap='large')
    with left:
        st.button('Reset to verified 50 km example',on_click=reset_example,width='stretch')
        with st.form('configuration',border=True):
            values,model,comp=configuration(page=='Compression')
            submitted=st.form_submit_button('Calculate delivery & power' if page=='Compression' else 'Run Simulation',type='primary',width='stretch')
        st.caption('Public interface limits are computational safeguards, not physical accuracy bounds. No login or saved simulation history is required.')
    with right:
        if submitted:
            st.session_state['draft']=dict(values)
            if comp:st.session_state['compressor_draft']=dict(comp)
            st.session_state.pop('bundle',None);st.session_state.pop('figure_download',None)
            try:
                operation={'Simulator':'forward','Model comparison':'comparison','Compression':'compressor'}[page]
                request=make_request(values,operation,model,comp)
                elapsed=time.monotonic()-st.session_state.get('last_request',0.)
                if elapsed<SESSION_INTERVAL_S:raise ServiceError('Please allow five seconds between requests in this session.')
                st.session_state['last_request']=time.monotonic()
                with st.spinner('Running the H2PipeBench numerical solver…'):
                    st.session_state['bundle']=run_request(request)
                st.session_state.pop('run_error',None)
            except (InputError,ServiceError) as exc:st.session_state['run_error']=str(exc)
        if st.session_state.get('run_error'):st.error(st.session_state['run_error'])
        bundle=st.session_state.get('bundle')
        expected={'Simulator':'forward','Model comparison':'comparison','Compression':'compressor'}[page]
        if bundle and bundle['operation']==expected:show_results(bundle)
        else:
            st.subheader('Trace hydrogen from inlet to delivery')
            st.write('Set the pipe, operating conditions and model, then run a calculation. Pressure, temperature and conservation diagnostics will appear here.')
            st.image(str(ROOT/'assets/geometry.png'),width='stretch')
            st.caption('Conceptual geometry from the scientific manuscript. Not to scale. The solid-conduction benchmark shown in the workflow is separate from this steady gas calculation.')
            with st.container(border=True):
                st.markdown('**Start with a reproducible case**')
                st.write('50 km length · 500 mm bore · 6 kg/s · 8 MPa absolute · 313.15 K inlet · 283.15 K soil. These are inputs from the retained Example A, not preloaded simulation outputs.')
elif page=='Method & limits':
    show_methodology()
else:
    st.subheader('Software information and references')
    st.write(f'H2PipeBench solver {SOLVER_VERSION} · Web interface {WEB_VERSION} · Python 3.12. The web interface calls the unmodified Python package through its public API.')
    st.markdown('Source and reproducibility files: [dimitrispasias57-eng/H2PipeBench](https://github.com/dimitrispasias57-eng/H2PipeBench). Project code is distributed under the MIT licence; dependencies retain their upstream terms.')
    st.markdown('''**References**

- [CoolProp hydrogen property model](https://coolprop.org/fluid_properties/fluids/Hydrogen.html).
- Leachman et al. (2009), fundamental hydrogen equations of state. [DOI](https://doi.org/10.1063/1.3160306).
- Bell et al. (2014), the CoolProp thermophysical property library. [DOI](https://doi.org/10.1021/ie4033999).
- Lohmeier et al. (2020), pandapipes. [DOI](https://doi.org/10.3390/su12239899). The retained comparison is a matched numerical limit, not an accuracy ranking.
- Yang et al. (2025), published hydrogen pipeline comparisons. [DOI](https://doi.org/10.3969/j.issn.1006-5539.2025.05.011). Laboratory discrepancies remain unresolved.
''')
    with st.expander('Privacy and resource use',expanded=True):
        st.write('Simulation inputs and the latest results are held in memory for the active session; the app does not write them to disk, a database or a shared result cache. Use “Clear session results” to discard the stored result. Downloads are generated from your completed run. Do not enter confidential operating data into a public research service. The hosting provider may process connection metadata under its own privacy terms; this application does not control those platform logs.')
        st.write('No app-level analytics, accounts, uploaded files, credentials or external calculation APIs are used. Numerical workers run one at a time per server process with a 35/75/90-second limit for a single model, four-model comparison or inverse compression calculation. The controls mitigate ordinary overload; they are not a distributed abuse-prevention service.')
    st.caption('AI assistance was used for interface development and verification. Scientific users remain responsible for reviewing the assumptions and interpreting the results within the documented limits.')

st.divider()
st.caption('Research and educational use only. H2PipeBench predictions are not certified for industrial pipeline design, safety assessments, equipment selection or regulatory compliance. Full-scale experimental accuracy has not been established.')
if st.button('Clear session results'):
    for key in ('bundle','run_error','figure_download'):st.session_state.pop(key,None)
    st.rerun()
