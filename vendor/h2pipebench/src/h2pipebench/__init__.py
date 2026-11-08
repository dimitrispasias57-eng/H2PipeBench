"""Public SI API for H2PipeBench; see docs/api.md."""
from .api import (
    Pipeline, SimulationResult, InletPressureResult, simulate,
    required_inlet_pressure, compressor_power, DomainError,
)
__version__ = "0.1.0"
__all__ = [
    "Pipeline", "SimulationResult", "InletPressureResult", "simulate",
    "required_inlet_pressure", "compressor_power", "DomainError", "__version__",
]

