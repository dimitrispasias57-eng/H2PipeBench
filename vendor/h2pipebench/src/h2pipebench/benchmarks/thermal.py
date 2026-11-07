"""Analytical Bessel eigenmode benchmark of the inherited P1 thermal FEM."""
from numbers import Integral
import numpy as np
import pandas as pd
from scipy.special import j0, y0
from scipy.optimize import brentq
from scipy.sparse import diags
from scipy.sparse.linalg import splu
from ..api import _positive, DomainError
from ._thermal import mesh_model

def annulus_decay(*, angular_cells=64, radial_cells=48, time_step_s=100.0,
                  duration_s=100_000.0):
    """Decay of a 1 K eigenmode, ri=.125 m, ro=1 m, alpha=1e-6 m²/s.

    Both annulus surfaces have zero temperature perturbation. Homogeneous solid,
    no flowing gas, no inference of field soil accuracy. Returns (summary, nodes).
    """
    for name, value, lower in (("angular_cells", angular_cells, 16), ("radial_cells", radial_cells, 16)):
        if isinstance(value, bool) or not isinstance(value, Integral) or value < lower:
            raise DomainError(f"{name} must be an integer >= {lower}")
    _positive("time_step_s", time_step_s)
    _positive("duration_s", duration_s)
    ri, ro, diffusivity = 0.125, 1.0, 1e-6
    equation = lambda lam: j0(lam*ro)*y0(lam*ri) - y0(lam*ro)*j0(lam*ri)
    eigenvalue = brentq(equation, 2.0, 5.0)
    model = mesh_model(conductivity=(1., 1.), capacity=(1e6, 1e6), film=0.,
                       angular=int(angular_cells), soil_cells=int(radial_cells),
                       layer_cells=3, annulus_outer=ro, inner_dirichlet=True)
    radius = np.linalg.norm(model.xy[model.free], axis=1)
    initial = j0(eigenvalue*radius)*y0(eigenvalue*ri)-y0(eigenvalue*radius)*j0(eigenvalue*ri)
    initial /= max(abs(initial))
    state = initial.copy()
    elapsed = 0.0
    factorizations = {}
    boundary_energy = 0.
    loss_weights = np.asarray(model.K.sum(axis=0)).ravel()
    steps = 0
    while elapsed < duration_s - 1e-8:
        dt = min(time_step_s, duration_s-elapsed)
        if dt not in factorizations:
            factorizations[dt] = splu((model.K + diags(model.C/dt)).tocsc()).solve
        new = factorizations[dt](model.C/dt*state)
        boundary_energy += dt * (loss_weights @ new)
        state = new
        elapsed += dt
        steps += 1
    exact = initial * np.exp(-diffusivity*eigenvalue**2*duration_s)
    error = state-exact
    residual = float(model.C@(state-initial) + boundary_energy)
    summary = dict(angular_cells=int(angular_cells), radial_cells=int(radial_cells),
                   time_step_s=time_step_s, duration_s=duration_s, steps=steps,
                   eigenvalue_m_inv=eigenvalue, max_error_K=float(max(abs(error))),
                   weighted_L2_error_K=float(np.sqrt(np.sum(model.C*error**2)/model.C.sum())),
                   energy_residual_J_m=residual,
                   energy_relative=abs(residual)/max(abs(boundary_energy),1.))
    nodes = pd.DataFrame(dict(radius_m=radius, numerical_K=state, exact_K=exact, error_K=error))
    return summary, nodes

