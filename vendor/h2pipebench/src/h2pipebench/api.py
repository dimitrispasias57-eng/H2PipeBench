"""Validated public interfaces; internal research names are not API contracts."""
from dataclasses import dataclass, replace
from numbers import Real, Integral
import math
import pandas as pd
from ._core.config import Case
from ._core.solver import solve
from ._core.compression import required_inlet, compressor
from ._core.properties import DomainError

MODELS = {"ideal_isothermal": "M1", "real_isothermal": "M2",
          "ideal_coupled": "M3", "real_coupled": "M4"}

def _positive(name, value):
    if isinstance(value, bool) or not isinstance(value, Real) or not math.isfinite(value) or value <= 0:
        raise DomainError(f"{name} must be a finite positive number in the documented SI units")

def _model(model):
    if not isinstance(model, str) or model not in MODELS:
        raise DomainError(f"model must be one of {tuple(MODELS)}")
    return MODELS[model]

@dataclass(frozen=True)
class Pipeline:
    """One horizontal pipe. All pressures are absolute Pa, temperatures K."""
    length_m: float = 50_000.0
    diameter_m: float = 0.5
    inlet_pressure_Pa: float = 8e6
    inlet_temperature_K: float = 313.15
    soil_temperature_K: float = 283.15
    mass_flow_kg_s: float = 6.0
    roughness_m: float = 2e-5
    wall_thickness_m: float = 0.012
    steel_conductivity_W_mK: float = 45.0
    burial_depth_m: float = 1.5
    soil_conductivity_W_mK: float = 1.5
    friction_correlation: str = "colebrook"
    heat_correlation: str = "gnielinski"
    adiabatic: bool = False
    include_acceleration: bool = True
    minimum_pressure_Pa: float = 1e5
    maximum_mach: float = 0.8
    constant_darcy_factor: float | None = None

    def _case(self):
        mapping = {
            "length_m": "L", "diameter_m": "D", "inlet_pressure_Pa": "p_in",
            "inlet_temperature_K": "T_in", "soil_temperature_K": "T_soil",
            "mass_flow_kg_s": "mdot", "wall_thickness_m": "thickness",
            "steel_conductivity_W_mK": "k_steel", "burial_depth_m": "depth",
            "soil_conductivity_W_mK": "k_soil", "minimum_pressure_Pa": "p_min",
            "maximum_mach": "max_mach",
        }
        for field in mapping:
            _positive(field, getattr(self, field))
        if not isinstance(self.adiabatic, bool) or not isinstance(self.include_acceleration, bool):
            raise DomainError("adiabatic and include_acceleration must be booleans")
        if (isinstance(self.roughness_m, bool) or not isinstance(self.roughness_m, Real)
                or not math.isfinite(self.roughness_m) or self.roughness_m < 0):
            raise DomainError("roughness_m must be finite and nonnegative")
        if self.constant_darcy_factor is not None:
            _positive("constant_darcy_factor", self.constant_darcy_factor)
        return Case(
            **{short: getattr(self, field) for field, short in mapping.items()},
            roughness=self.roughness_m, friction_method=self.friction_correlation,
            heat_method=self.heat_correlation, adiabatic=self.adiabatic,
            acceleration=self.include_acceleration, fixed_f=self.constant_darcy_factor,
        ).validate()

@dataclass
class SimulationResult:
    """Sampled profile in SI and integral diagnostics; see docs/api.md."""
    pipeline: Pipeline
    model: str
    profile: pd.DataFrame
    summary: dict

@dataclass
class InletPressureResult:
    required_pressure_Pa: float
    delivery_residual_Pa: float
    simulation: SimulationResult

def simulate(pipeline=None, model="real_coupled", *, relative_tolerance=2e-8,
             max_step_m=None, audit_points=201):
    """Integrate one steady pipeline; failed trajectories raise DomainError."""
    if pipeline is None:
        pipeline = Pipeline()
    if not isinstance(pipeline, Pipeline):
        raise DomainError("pipeline must be a Pipeline instance")
    case = pipeline._case()
    code = _model(model)
    _positive("relative_tolerance", relative_tolerance)
    if not 1e-12 <= relative_tolerance <= 1e-3:
        raise DomainError("relative_tolerance must lie between 1e-12 and 1e-3")
    if max_step_m is not None:
        _positive("max_step_m", max_step_m)
    if isinstance(audit_points, bool) or not isinstance(audit_points, Integral) or audit_points < 3 or audit_points % 2 != 1:
        raise DomainError("audit_points must be an odd integer >= 3")
    result = solve(case, code, rtol=relative_tolerance, max_step=max_step_m, points=int(audit_points))
    summary = dict(result.summary, model=model)
    return SimulationResult(pipeline, model, result.profile, summary)

def required_inlet_pressure(pipeline, outlet_pressure_Pa, model="real_coupled", *,
                            upper_pressure_Pa=30e6):
    """Shoot for fixed outlet pressure and mass flow; upper bound is numerical."""
    if not isinstance(pipeline, Pipeline):
        raise DomainError("pipeline must be a Pipeline instance")
    case = pipeline._case()
    _positive("outlet_pressure_Pa", outlet_pressure_Pa)
    _positive("upper_pressure_Pa", upper_pressure_Pa)
    if upper_pressure_Pa > 30e6:
        raise DomainError("upper_pressure_Pa exceeds the adopted 30 MPa property envelope")
    code = _model(model)
    pressure, result, error = required_inlet(case, code, outlet_pressure_Pa, upper=upper_pressure_Pa)
    actual = replace(pipeline, inlet_pressure_Pa=pressure)
    wrapped = SimulationResult(actual, model, result.profile, dict(result.summary, model=model))
    return InletPressureResult(float(pressure), float(error), wrapped)

def compressor_power(discharge_pressure_Pa, mass_flow_kg_s, aftercooler_temperature_K,
                     *, suction_pressure_Pa=2e6, suction_temperature_K=298.15,
                     isentropic_efficiency=0.75, motor_efficiency=0.95):
    """Single-stage real-H2 compression energy estimate; no equipment rating."""
    for name, value in (
        ("discharge_pressure_Pa", discharge_pressure_Pa), ("mass_flow_kg_s", mass_flow_kg_s),
        ("aftercooler_temperature_K", aftercooler_temperature_K),
        ("suction_pressure_Pa", suction_pressure_Pa), ("suction_temperature_K", suction_temperature_K),
        ("isentropic_efficiency", isentropic_efficiency), ("motor_efficiency", motor_efficiency)):
        _positive(name, value)
    if suction_pressure_Pa < 1e5 or not 200 <= suction_temperature_K <= 500 or not 200 <= aftercooler_temperature_K <= 500:
        raise DomainError("Compressor inlet/aftercooler requires 200–500 K and suction >= 1e5 Pa")
    try:
        return compressor(discharge_pressure_Pa, mass_flow_kg_s, aftercooler_temperature_K,
                          p_suction=suction_pressure_Pa, T_suction=suction_temperature_K,
                          eta_is=isentropic_efficiency, eta_motor=motor_efficiency)
    except ValueError as exc:
        raise DomainError(f"Compressor calculation failed: {exc}") from exc

