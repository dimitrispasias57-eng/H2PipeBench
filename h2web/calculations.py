"""Thin orchestration layer: all physical calculations use the public solver API."""
from dataclasses import asdict
from datetime import datetime, timezone
from importlib.metadata import version
import math
from h2pipebench import simulate, required_inlet_pressure, compressor_power, DomainError
from .inputs import validate_request
from . import __version__

ASSUMPTIONS = [
    'Steady, one-dimensional, horizontal straight pipe; normal pure hydrogen; no elevation, fittings, leaks, mixtures or gas transients.',
    'Absolute pressure in Pa and temperature in K internally; fixed positive mass flow.',
    'Real-gas thermodynamics use CoolProp HEOS::Hydrogen. Ideal modes retain HEOS viscosity, conductivity and transport heat capacity.',
    'Isothermal temperature is imposed; required heat and thermostat duty are accounted for separately from ground heat.',
    'Soil is homogeneous with stationary far-field temperature. No coupled transient solid mesh is solved by this interface.',
    'Successful integration and small residuals establish numerical checks, not experimental accuracy or industrial safety.',
]
UNITS = {
    'x_m':'m','p_Pa':'Pa absolute','T_K':'K','rho_kg_m3':'kg/m^3','u_m_s':'m/s',
    'h_J_kg':'J/kg','cp_J_kgK':'J/(kg K)','Re':'1','Mach':'1','Z':'1','f_D':'1',
    'friction_Pa_m':'Pa/m','q_ground_W_m':'W/m into gas','q_used_W_m':'W/m into gas',
    'thermostat_W_m':'W/m into gas','p_out_Pa':'Pa absolute','T_out_K':'K','dp_Pa':'Pa',
    'Q_ground_W':'W into gas','Q_required_W':'W into gas','Q_thermostat_W':'W into gas',
    'momentum_residual_Pa':'Pa','energy_residual_J_kg':'J/kg','mass_relative':'1',
    'momentum_relative':'1','energy_relative':'1','electric_power_W':'W electrical power',
    'aftercooler_heat_removed_W':'W removed from gas',
    'R_Km_W':'K m/W','Nu':'1','Pr':'1','film_fraction':'1',
    'det_normalized':'1','isothermal_margin':'1','required_inlet_Pa':'Pa absolute',
    'delivery_target_Pa':'Pa absolute','delivery_residual_Pa':'Pa',
    'incremental_electric_power_W':'W electrical power',
}

def public_error(exc):
    """Map known failures to useful messages; never send tracebacks or paths."""
    message = str(exc).lower()
    patterns = [
        ('burial', 'Burial depth must exceed the pipe outside radius; relative roughness must be at most 0.05.'),
        ('roughness', 'The requested roughness is outside the solver limits.'),
        ('transitional', 'The trajectory enters transitional flow. The adopted correlations reject Reynolds numbers from 2300 to below 4000.'),
        ('gnielinski', 'The Gnielinski heat-transfer correlation is outside its adopted range: turbulent Re 4000–5,000,000 and Pr 0.5–2000. Check mass flow, diameter and thermal conditions.'),
        ('dittus', 'The Dittus–Boelter correlation is outside its adopted turbulent range: Re 10,000–5,000,000 and Pr 0.6–160.'),
        ('bracket', 'The inlet-pressure search could not find two successful states bracketing the delivery target below 30 MPa. This is a search failure, not proof of global infeasibility.'),
        ('monoton', 'The inverse search encountered a non-monotone feasible region and stopped. No delivery solution is returned.'),
        ('incomplete', 'The solver stopped before the full pipeline length at a pressure, Mach or integration guard. No full-length result is reported.'),
        ('mach', 'The requested trajectory violates the conservative Mach-number guard. Review pressure, flow and diameter.'),
        ('singular', 'The momentum/energy system approached its numerical critical-state guard. No result is returned.'),
        ('temperature', 'A gas or compressor state is outside the adopted temperature range. Gas states require 200–500 K; compressor discharge must not exceed 1000 K.'),
        ('property envelope', 'A gas state left the adopted property envelope (200–500 K and pressure up to 30 MPa). No result is returned.'),
        ('compressor', 'The compression calculation is unsupported for these pressure, temperature or efficiency inputs.'),
        ('absolute', 'Use absolute pressure above 0.1 MPa and at most 30 MPa, and temperatures from 200 to 500 K.'),
    ]
    return next((text for token, text in patterns if token in message),
                'The solver rejected this input or trajectory. Review the documented geometry, property and correlation limits. No result was substituted.')

def clean(value):
    """JSON interoperability: optional unbounded diagnostics become null, never fake zero."""
    if isinstance(value, dict): return {str(k):clean(v) for k,v in value.items()}
    if isinstance(value, (list, tuple)): return [clean(v) for v in value]
    if hasattr(value, 'item'): value=value.item()
    if isinstance(value, float) and not math.isfinite(value): return None
    return value

def pack(result):
    return clean(dict(model=result.model, pipeline_inputs_si=asdict(result.pipeline),
                      summary=result.summary, profile=result.profile.to_dict(orient='records')))

def execute(request):
    p = validate_request(request)
    bundle = dict(schema_version=1, operation=request['operation'], request=request,
                  created_utc=datetime.now(timezone.utc).isoformat(),
                  versions={n:version(n) for n in ('h2pipebench','CoolProp','numpy','scipy','pandas')},
                  web_version=__version__, assumptions=ASSUMPTIONS, units=UNITS,
                  results=[], errors=[], compressor=None)
    if request['operation'] == 'compressor':
        c=request['compressor'];model=request['models'][0]
        try:
            delivery=required_inlet_pressure(p,c['delivery_MPa']*1e6,model)
            kwargs=dict(suction_pressure_Pa=c['suction_MPa']*1e6, suction_temperature_K=c['suction_K'],
                        isentropic_efficiency=c['eta_is'], motor_efficiency=c['eta_motor'])
            total=compressor_power(delivery.required_pressure_Pa,p.mass_flow_kg_s,p.inlet_temperature_K,**kwargs)
            baseline=compressor_power(c['delivery_MPa']*1e6,p.mass_flow_kg_s,p.inlet_temperature_K,**kwargs)
            bundle['results']=[pack(delivery.simulation)]
            bundle['compressor']=dict(required_inlet_Pa=delivery.required_pressure_Pa,
                delivery_target_Pa=c['delivery_MPa']*1e6, delivery_residual_Pa=delivery.delivery_residual_Pa,
                total=total, baseline=baseline,
                incremental_electric_power_W=total['electric_power_W']-baseline['electric_power_W'],
                assumptions='Single-stage real-H2 isentropic enthalpy calculation, specified efficiencies; aftercooling to pipeline inlet temperature. Baseline uses identical suction, mass flow, efficiencies and cooling boundary with discharge at delivery pressure. No compressor map, staging optimization, equipment rating or cooler electricity.')
        except DomainError as exc:
            bundle['errors'].append(dict(model=model,message=public_error(exc)))
    else:
        for model in request['models']:
            try:
                bundle['results'].append(pack(simulate(p,model,audit_points=801)))
            except DomainError as exc:
                bundle['errors'].append(dict(model=model,message=public_error(exc)))
    bundle['status']='complete' if not bundle['errors'] else 'partial' if bundle['results'] else 'unsupported'
    return clean(bundle)
