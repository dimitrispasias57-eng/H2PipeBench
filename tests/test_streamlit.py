from pathlib import Path
import time
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
    submit(at,'Run Simulation')
    assert len(at.session_state['bundle']['results'])==4
    at.radio(key='workspace').set_value('Compression').run()
    submit(at,'Calculate delivery & power')
    assert at.metric[0].value=='7.098695 MPa'
    assert at.metric[1].value=='16.147618 MW'
    assert at.metric[2].value=='214.489 kW'
    at.radio(key='workspace').set_value('Method & limits').run()
    assert not at.exception and len(at.latex)>=6
    at.radio(key='workspace').set_value('Software').run()
    assert not at.exception
    next(b for b in at.button if b.label=='Clear session results').click().run()
    assert 'bundle' not in at.session_state
