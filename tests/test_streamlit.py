from pathlib import Path
from io import BytesIO
import time
import numpy as np
import pandas as pd
import pytest
from streamlit.testing.v1 import AppTest

APP=Path(__file__).resolve().parents[1]/'app.py'

def app():
    at=AppTest.from_file(str(APP),default_timeout=110).run()
    assert not at.exception
    return at

def submit(at,label):
    at.session_state['last_request']=0.
    import h2web.service as service
    service._last_start=0.
    next(b for b in at.button if b.label==label).click().run()
    assert not at.exception

def test_initial_screen_and_real_forward_result():
    at=app()
    assert len(at.metric)==0
    submit(at,'Run Simulation')
    assert len(at.metric)==6
    assert at.metric[0].value=='7.912069 MPa'
    assert at.metric[1].value=='286.420 K'
    assert at.session_state['bundle']['results'][0]['summary']['audit_points']==801
    at.radio(key='display_temperature').set_value('°C').run()
    assert at.metric[1].value=='13.270 °C'
    at.button(key='prepare_figures').click().run()
    assert not at.exception
    assert at.session_state['figure_download'][3].startswith(b'\x89PNG')
    # Invalid geometry must discard the former result, not leave it looking current.
    at.number_input(key='burial_m').set_value(.02)
    submit(at,'Run Simulation')
    assert at.error and 'outside radius' in at.error[0].value
    assert len(at.metric)==0

def test_comparison_compression_and_information_pages():
    at=app();at.radio(key='workspace').set_value('Model comparison').run()
    selector=at.selectbox(key='comparison_models')
    assert selector.value=='All four models (M1–M4)'
    assert selector.options==['All four models (M1–M4)'] and selector.disabled
    assert not any(s.key=='model' for s in at.selectbox)
    submit(at,'Run Simulation')
    assert len(at.session_state['bundle']['results'])==4
    at.radio(key='workspace').set_value('Compression').run()
    submit(at,'Calculate delivery & power')
    assert at.metric[0].value=='7.098695 MPa'
    assert at.metric[1].value=='16.147618 MW'
    assert at.metric[2].value=='214.489 kW'
    at.radio(key='workspace').set_value('Method & limits').run()
    from h2web.methodology import EQUATIONS
    assert not at.exception
    displayed=[e.value.removeprefix('$$\n').removesuffix('\n$$') for e in at.latex]
    assert sorted(displayed)==sorted(v[0] for v in EQUATIONS.values())
    assert 'Nomenclature — Symbols and Units' in [e.label for e in at.expander]
    assert 'Numerical verification versus experimental validation' in [e.label for e in at.expander]
    assert all(not any(ord(c)<32 for c in equation) for equation in displayed)
    # Comparison mode must not remove the selectable single-model control elsewhere.
    at.radio(key='workspace').set_value('Simulator').run()
    at.selectbox(key='model').set_value('ideal_isothermal')
    submit(at,'Run Simulation')
    assert not at.exception and at.selectbox(key='model').value=='ideal_isothermal'
    assert at.session_state['bundle']['results'][0]['model']=='ideal_isothermal'
    at.radio(key='workspace').set_value('Software').run()
    assert not at.exception
    next(b for b in at.button if b.label=='Clear session results').click().run()
    assert 'bundle' not in at.session_state


@pytest.mark.parametrize('page,button,count',[
    ('Simulator','Run Simulation',1),
    ('Model comparison','Run Simulation',4),
    ('Compression','Calculate delivery & power',1),
])
def test_decimal_length_reaches_solver_and_csv(page,button,count):
    from h2web.exports import profiles_csv
    at=app()
    if page!='Simulator':at.radio(key='workspace').set_value(page).run()
    length=at.number_input(key='length_km')
    assert length.value==50.
    assert (length.proto.min,length.proto.max,length.proto.step)==(.01,200.,1.)
    length.set_value(12.5)
    submit(at,button)
    assert at.number_input(key='length_km').value==12.5
    bundle=at.session_state['bundle']
    assert bundle['request']['inputs']['length_km']==12.5
    assert bundle['status']=='complete' and len(bundle['results'])==count
    csv=pd.read_csv(BytesIO(profiles_csv(bundle)))
    for result in bundle['results']:
        assert result['pipeline_inputs_si']['length_m']==12500.
        data=pd.DataFrame(result['profile'])
        exported=csv[csv.model==result['model']]
        assert data.x_m.iloc[0]==0. and data.x_m.iloc[-1]==12500.
        assert exported.x_m.iloc[-1]==12500.
        np.testing.assert_allclose(exported[data.columns],data,rtol=1e-12,atol=1e-12)
        assert exported.p_Pa.iloc[-1]==pytest.approx(result['summary']['p_out_Pa'],rel=1e-12)
        assert exported.T_K.iloc[-1]==pytest.approx(result['summary']['T_out_K'],rel=1e-12)
        assert result['summary']['rtol']==2e-8
        assert result['summary']['max_step_m']==12500./40  # Existing L/40 rule.
    if page=='Compression':
        assert abs(bundle['compressor']['delivery_residual_Pa'])<.1
        assert bundle['results'][0]['summary']['p_out_Pa']==pytest.approx(7e6,abs=.1)
    else:
        from h2pipebench import Pipeline, simulate
        # Direct API call bypasses the UI conversion and supplies SI length explicitly.
        expected=simulate(Pipeline(length_m=12500.),'real_coupled',audit_points=801)
        actual=next(r for r in bundle['results'] if r['model']=='real_coupled')
        assert actual['summary']['p_out_Pa']==pytest.approx(expected.summary['p_out_Pa'],rel=1e-12)
        assert actual['summary']['T_out_K']==pytest.approx(expected.summary['T_out_K'],rel=1e-12)
