from dataclasses import replace
import numpy as np
import pytest
from h2pipebench import Pipeline, simulate, required_inlet_pressure, compressor_power, DomainError
from h2pipebench.benchmarks import annulus_decay

@pytest.mark.parametrize("field,value",[
    ("length_m",0),("diameter_m",float("nan")),("mass_flow_kg_s",True),
    ("roughness_m",float("inf")),("inlet_pressure_Pa","80bar"),
    ("inlet_temperature_K",25),("burial_depth_m",.1),("maximum_mach",.9),
    ("adiabatic",1),("include_acceleration","yes"),("constant_darcy_factor",float("nan"))])
def test_invalid_pipeline(field,value):
    with pytest.raises(DomainError):
        simulate(replace(Pipeline(),**{field:value}))

@pytest.mark.parametrize("options",[
    {"max_step_m":0},{"max_step_m":float("nan")},{"relative_tolerance":0},
    {"audit_points":201.5},{"audit_points":True},{"audit_points":20},{"model":"M4"}])
def test_invalid_numerical_inputs(options):
    with pytest.raises(DomainError): simulate(Pipeline(),**options)

def test_public_result_and_delivery_contract():
    pipe=Pipeline(length_m=10_000.)
    result=simulate(pipe)
    assert {"x_m","p_Pa","T_K"} <= set(result.profile)
    assert result.model=="real_coupled"
    inverse=required_inlet_pressure(pipe,result.summary["p_out_Pa"])
    assert abs(inverse.required_pressure_Pa-pipe.inlet_pressure_Pa)<.1
    assert abs(inverse.delivery_residual_Pa)<.1

@pytest.mark.parametrize("options",[
    {"mass_flow_kg_s":float("inf")},{"suction_pressure_Pa":100.},
    {"isentropic_efficiency":1.01},{"suction_temperature_K":float("nan")}])
def test_compression_bad_inputs(options):
    kwargs=dict(discharge_pressure_Pa=8e6,mass_flow_kg_s=6.,aftercooler_temperature_K=313.15)
    kwargs.update(options)
    with pytest.raises(DomainError): compressor_power(**kwargs)

def test_no_compression_no_electricity():
    result=compressor_power(2e6,6.,298.15)
    assert result["electric_power_W"]==pytest.approx(0,abs=1e-6)

@pytest.mark.parametrize("options",[{"time_step_s":0},{"radial_cells":10},{"angular_cells":16.2}])
def test_thermal_invalid(options):
    with pytest.raises(DomainError): annulus_decay(**options)

def test_thermal_analytic_and_energy():
    summary,nodes=annulus_decay(angular_cells=32,radial_cells=24,time_step_s=200.,duration_s=20_000.)
    assert summary["max_error_K"]<.01
    assert summary["energy_relative"]<1e-10
    assert np.isfinite(nodes.to_numpy()).all()

def test_inverse_upper_guard():
    with pytest.raises(DomainError): required_inlet_pressure(Pipeline(),7e6,upper_pressure_Pa=31e6)

