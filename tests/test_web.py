from pathlib import Path
from copy import deepcopy
from io import BytesIO
import hashlib
import json
import numpy as np
import pandas as pd
import pytest
from h2web.inputs import DEFAULTS, COMPRESSOR_DEFAULTS, InputError, pipeline, make_request, validate_request
from h2web.calculations import execute, public_error
from h2web.exports import chart, series, profiles_csv, inputs_json, json_bytes, comparison_table, report_html, static_figure
from h2web.service import _run_worker, ServiceError

ROOT=Path(__file__).resolve().parents[1]

@pytest.fixture(scope='module')
def baseline():return execute(make_request(DEFAULTS))

@pytest.fixture(scope='module')
def comparison():
    values=DEFAULTS | dict(length_km=100., diameter_mm=300., inlet_MPa=12., inlet_K=333.15, mass_flow=3.)
    return execute(make_request(values,'comparison'))

def test_source_payload_unchanged():
    vendor=ROOT/'vendor/h2pipebench'
    manifest=json.loads((vendor/'SOURCE_HASHES.json').read_text())['sha256']
    actual={p.relative_to(vendor).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in (vendor/'src').rglob('*.py')}
    assert actual==manifest

def test_units_and_defaults():
    p=pipeline(DEFAULTS)
    assert (p.length_m,p.diameter_m,p.wall_thickness_m,p.roughness_m,p.inlet_pressure_Pa)==pytest.approx((50000,.5,.012,2e-5,8e6))
    assert p.inlet_temperature_K==313.15

@pytest.mark.parametrize('key,value',[('length_km',0),('diameter_mm',float('nan')),('roughness_um',float('inf')),
 ('inlet_MPa',31),('inlet_K',199),('mass_flow',True),('burial_m',.02),('friction','arbitrary'),('acceleration','true')])
def test_rejected_inputs_not_clamped(key,value):
    values=DEFAULTS|{key:value};snapshot=deepcopy(values)
    with pytest.raises(InputError):make_request(values)
    for k in values:
        if isinstance(values[k],float) and np.isnan(values[k]):continue
        assert values[k]==snapshot[k]

def test_reference_pressure_temperature_and_profile(baseline):
    saved=json.loads((ROOT/'tests/reference/01_steady.json').read_text())
    result=baseline['results'][0]
    assert baseline['status']=='complete'
    for key in result['summary']:
        if key in saved['summary'] and isinstance(saved['summary'][key],(float,int)):
            assert result['summary'][key]==pytest.approx(saved['summary'][key],rel=2e-9,abs=1e-7)
    ref=pd.read_csv(ROOT/'tests/reference/01_profile.csv')
    actual=pd.DataFrame(result['profile'])
    assert list(actual)==list(ref)
    np.testing.assert_allclose(actual,ref,rtol=2e-9,atol=1e-7)

def test_all_four_against_saved_example(comparison):
    saved=pd.read_csv(ROOT/'tests/reference/02_comparison.csv').set_index('model')
    assert comparison['status']=='complete' and len(comparison['results'])==4
    for r in comparison['results']:
        for key in ['p_out_Pa','T_out_K','dp_Pa','Q_ground_W','Q_required_W','Q_thermostat_W']:
            assert r['summary'][key]==pytest.approx(saved.loc[r['model'],key],rel=2e-9,abs=1e-6)
        assert r['pipeline_inputs_si']==comparison['results'][0]['pipeline_inputs_si']

def test_compressor_matches_verified_example():
    result=execute(make_request(DEFAULTS,'compressor',compressor=COMPRESSOR_DEFAULTS))
    assert result['status']=='complete'
    c=result['compressor'];ref=json.loads((ROOT/'tests/reference/01_steady.json').read_text())['summary']
    assert c['required_inlet_Pa']==pytest.approx(ref['required_inlet_Pa'],abs=.02)
    assert c['total']['electric_power_W']==pytest.approx(ref['compressor_electricity_W'],rel=2e-9)
    assert c['incremental_electric_power_W']==pytest.approx(ref['incremental_transport_electricity_W'],rel=2e-9)
    assert c['incremental_electric_power_W']==c['total']['electric_power_W']-c['baseline']['electric_power_W']
    assert abs(c['delivery_residual_Pa'])<.1
    assert result['results'][0]['pipeline_inputs_si']['inlet_pressure_Pa']==c['required_inlet_Pa']

def test_domain_failure_no_fabricated_result():
    result=execute(make_request(DEFAULTS|dict(mass_flow=100.)))
    assert result['status']=='unsupported' and result['results']==[]
    assert result['errors']

def test_adiabatic_optional_infinity_becomes_null():
    result=execute(make_request(DEFAULTS|dict(adiabatic=True)))
    assert result['status']=='complete'
    r=result['results'][0]
    assert all(p['R_Km_W'] is None and p['q_ground_W_m']==0 for p in r['profile'])
    assert b'Infinity' not in json_bytes(result)

def test_downloads_and_charts_match_snapshot(baseline):
    r=baseline['results'][0];csv=pd.read_csv(BytesIO(profiles_csv(baseline)))
    assert csv['model'].unique().tolist()==['real_coupled']
    np.testing.assert_allclose(csv.p_Pa,[p['p_Pa'] for p in r['profile']])
    fig=chart(baseline['results'],'Pressure')
    np.testing.assert_allclose(fig.data[0].y,csv.p_Pa/1e6)
    _,y,label=series(r,'Temperature','°C');assert y.iloc[0]==pytest.approx(40.)
    assert '°C' in label
    decoded=json.loads(json_bytes(baseline));assert decoded==baseline
    inputs=json.loads(inputs_json(baseline));assert inputs['request']==baseline['request']
    assert 'solved_pipeline_inputs_si' in inputs
    table=comparison_table(baseline);assert table.iloc[0]['Pressure drop (kPa)']==r['summary']['dp_Pa']/1000
    report=report_html(baseline)
    assert b'Research and educational use only' in report
    for output in [report,inputs_json(baseline),json_bytes(baseline),profiles_csv(baseline)]:
        assert b'Users\\' not in output and b'Users/' not in output
    assert static_figure(baseline,'Pressure','png').startswith(b'\x89PNG')
    assert b'<svg' in static_figure(baseline,'Temperature','svg')
    assert set(r['profile'][0]) <= set(baseline['units'])

def test_unknown_failure_does_not_expose_details():
    message=public_error(ValueError('PRIVATE_PATH /home/private SECRET=abc'))
    assert 'PRIVATE' not in message and 'SECRET' not in message and '/home' not in message

def test_real_worker_and_timeout():
    r=_run_worker(make_request(DEFAULTS),35.)
    assert r['status']=='complete' and r['results'][0]['summary']['p_out_Pa']>0
    with pytest.raises(ServiceError,match='time limit'):_run_worker(make_request(DEFAULTS),.001)

def test_request_schema_and_compression_baseline():
    req=make_request(DEFAULTS);req['unknown']='value'
    with pytest.raises(InputError):validate_request(req)
    with pytest.raises(InputError):make_request(DEFAULTS,'compressor',compressor=COMPRESSOR_DEFAULTS|dict(suction_MPa=8.))


def test_every_configuration_field_is_transferred():
    values=dict(length_km=80.,diameter_mm=400.,wall_mm=10.,roughness_um=35.,
        wall_conductivity=42.,burial_m=2.,inlet_MPa=9.,inlet_K=320.,mass_flow=4.,
        soil_K=285.,soil_conductivity=1.8,friction='haaland',heat='dittus_boelter',
        adiabatic=True,acceleration=False)
    p=pipeline(values)
    numeric={'length_m':80000.,'diameter_m':.4,'wall_thickness_m':.01,'roughness_m':35e-6,
        'steel_conductivity_W_mK':42.,'burial_depth_m':2.,'inlet_pressure_Pa':9e6,
        'inlet_temperature_K':320.,'mass_flow_kg_s':4.,'soil_temperature_K':285.,
        'soil_conductivity_W_mK':1.8}
    for key,value in numeric.items():assert getattr(p,key)==pytest.approx(value)
    assert p.adiabatic and not p.include_acceleration
    assert p.friction_correlation=='haaland' and p.heat_correlation=='dittus_boelter'


@pytest.mark.parametrize('changes',[{'friction':'haaland'},{'heat':'dittus_boelter'},
    {'acceleration':False},{'adiabatic':True}])
def test_supported_alternative_controls_reach_solver(changes):
    result=execute(make_request(DEFAULTS|changes))
    assert result['status']=='complete'
    assert len(result['results'][0]['profile'])==801


def test_service_admission_and_startup_failure(monkeypatch):
    import h2web.service as service
    request=make_request(DEFAULTS)
    service._slot.acquire()
    try:
        with pytest.raises(ServiceError,match='busy'):service.run_request(request)
    finally:service._slot.release()
    monkeypatch.setattr(service,'_last_start',service.time.monotonic())
    with pytest.raises(ServiceError,match='wait'):service.run_request(request)
    def fail_start(*args,**kwargs):raise OSError('PRIVATE_PATH with SECRET')
    monkeypatch.setattr(service.subprocess,'Popen',fail_start)
    with pytest.raises(ServiceError,match='could not start') as exc:service._run_worker(request,1.)
    assert 'PRIVATE' not in str(exc.value) and 'SECRET' not in str(exc.value)
