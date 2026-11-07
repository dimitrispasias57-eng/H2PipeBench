"""Explicit UI-to-SI conversion and bounded public-service inputs."""
from dataclasses import asdict
import math
from h2pipebench import Pipeline

MODELS = {
    'real_coupled': ('M4', 'Real gas · non-isothermal'),
    'ideal_isothermal': ('M1', 'Ideal gas · isothermal'),
    'real_isothermal': ('M2', 'Real gas · isothermal'),
    'ideal_coupled': ('M3', 'Ideal gas · non-isothermal'),
}
MODEL_ORDER = ['ideal_isothermal', 'real_isothermal', 'ideal_coupled', 'real_coupled']
DEFAULTS = dict(length_km=50., diameter_mm=500., wall_mm=12., roughness_um=20.,
                wall_conductivity=45., burial_m=1.5, inlet_MPa=8., inlet_K=313.15,
                mass_flow=6., soil_K=283.15, soil_conductivity=1.5,
                friction='colebrook', heat='gnielinski', adiabatic=False,
                acceleration=True)
# Interface limits bound public compute requests. They are not validated design ranges.
BOUNDS = {
    'length_km': (.01, 200.), 'diameter_mm': (10., 1500.), 'wall_mm': (.1, 100.),
    'roughness_um': (0., 2000.), 'wall_conductivity': (.1, 500.), 'burial_m': (.02, 20.),
    'inlet_MPa': (.100001, 30.), 'inlet_K': (200., 500.), 'mass_flow': (.0001, 100.),
    'soil_K': (200., 500.), 'soil_conductivity': (.05, 20.),
}
COMPRESSOR_DEFAULTS = dict(suction_MPa=2., suction_K=298.15, delivery_MPa=7., eta_is=.75, eta_motor=.95)
COMPRESSOR_BOUNDS = dict(suction_MPa=(.1, 29.9), suction_K=(200., 500.),
                         delivery_MPa=(.100001, 29.9), eta_is=(.1, 1.), eta_motor=(.1, 1.))

class InputError(ValueError):
    pass

def bounded(values, limits):
    for key, (low, high) in limits.items():
        value = values.get(key)
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise InputError(f'{key}: enter a finite number.')
        if not low <= value <= high:
            raise InputError(f'{key}: the web service accepts {low:g} to {high:g}.')

def pipeline(values):
    if set(values) != set(DEFAULTS):
        raise InputError('The pipeline configuration is incomplete or contains unknown fields.')
    bounded(values, BOUNDS)
    if values['friction'] not in ('colebrook', 'haaland') or values['heat'] not in ('gnielinski', 'dittus_boelter'):
        raise InputError('Select a supported friction and heat-transfer correlation.')
    if type(values['adiabatic']) is not bool or type(values['acceleration']) is not bool:
        raise InputError('Thermal and acceleration switches must be true or false.')
    p = Pipeline(length_m=values['length_km'] * 1000, diameter_m=values['diameter_mm'] / 1000,
                 wall_thickness_m=values['wall_mm'] / 1000, roughness_m=values['roughness_um'] * 1e-6,
                 steel_conductivity_W_mK=values['wall_conductivity'], burial_depth_m=values['burial_m'],
                 inlet_pressure_Pa=values['inlet_MPa'] * 1e6, inlet_temperature_K=values['inlet_K'],
                 mass_flow_kg_s=values['mass_flow'], soil_temperature_K=values['soil_K'],
                 soil_conductivity_W_mK=values['soil_conductivity'], friction_correlation=values['friction'],
                 heat_correlation=values['heat'], adiabatic=values['adiabatic'],
                 include_acceleration=values['acceleration'])
    # Usability checks are duplicated at the boundary; simulate remains the
    # authority for input and trajectory admissibility. Nothing is clamped.
    if p.burial_depth_m <= p.diameter_m / 2 + p.wall_thickness_m:
        raise InputError('Burial depth is measured to the pipe centreline and must exceed the outside radius (diameter/2 + wall thickness).')
    if p.roughness_m / p.diameter_m > .05:
        raise InputError('Relative roughness must not exceed 0.05. Review roughness and diameter.')
    return p

def validate_request(request):
    if not isinstance(request, dict) or set(request) != {'operation', 'inputs', 'models', 'compressor'}:
        raise InputError('Unsupported calculation request.')
    if request['operation'] not in ('forward', 'comparison', 'compressor'):
        raise InputError('Unsupported calculation type.')
    models = request['models']
    if not isinstance(models, list) or not models or any(not isinstance(m,str) or m not in MODELS for m in models):
        raise InputError('Select one of the four supported models.')
    if request['operation'] == 'comparison':
        if models != MODEL_ORDER:
            raise InputError('A comparison must use all four models with identical inputs.')
    elif len(models) != 1:
        raise InputError('Select one model for this calculation.')
    p = pipeline(request['inputs'])
    c = request['compressor']
    if request['operation'] == 'compressor':
        if not isinstance(c, dict) or set(c) != set(COMPRESSOR_DEFAULTS):
            raise InputError('The compressor boundary conditions are incomplete.')
        bounded(c, COMPRESSOR_BOUNDS)
        if c['delivery_MPa'] < c['suction_MPa']:
            raise InputError('Delivery pressure must be at least suction pressure for the common compression baseline.')
    elif c is not None:
        raise InputError('Unexpected compressor parameters in a forward calculation.')
    return p

def make_request(values, operation='forward', model='real_coupled', compressor=None):
    request = dict(operation=operation, inputs=dict(values),
                   models=list(MODEL_ORDER) if operation == 'comparison' else [model], compressor=compressor)
    validate_request(request)
    return request
