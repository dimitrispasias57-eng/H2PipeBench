"""Adaptive DOP853 solve, admissibility events, independently integrated audits."""
from dataclasses import dataclass
import numpy as np
import pandas as pd
from scipy.integrate import solve_ivp, simpson
from .config import MODELS
from .properties import Hydrogen, DomainError
from .equations import local


@dataclass
class Result:
    case: object
    model: str
    profile: pd.DataFrame
    summary: dict


def solve(case,model='M4',*,rtol=2e-8,max_step=None,points=201,gas_factory=None):
    case.validate()
    if model not in MODELS:
        raise ValueError(f'Unknown model {model}')
    if points<3 or points%2!=1:
        raise ValueError('Use an odd number of >=3 audit points')
    gas=(gas_factory or Hydrogen)(ideal=model in ('M1','M3'))
    # Integrate normalized p and T to avoid mismatched ODE scales.
    scale=np.array([case.p_in,case.T_in])
    def rhs(x,y):
        return local(case,model,gas,*(y*scale))[0]/scale
    def pressure_event(x,y): return y[0]*scale[0]-case.p_min
    def critical_event(x,y):
        _,d=local(case,model,gas,*(y*scale))
        return min(case.max_mach-d['Mach'],d['isothermal_margin']-0.05 if model in ('M1','M2') else 1.)
    for e in (pressure_event,critical_event):
        e.terminal=True; e.direction=-1
    _,initial=local(case,model,gas,case.p_in,case.T_in)
    if initial['Mach']>=case.max_mach:
        raise DomainError('Inlet exceeds conservative Mach limit')
    sol=solve_ivp(rhs,(0,case.L),[1.,1.],method='DOP853',rtol=rtol,
        atol=rtol*1e-3,max_step=max_step or case.L/40,
        events=[pressure_event,critical_event],dense_output=True)
    if not sol.success or sol.status!=0 or sol.t[-1]<case.L*(1-1e-12):
        event='minimum_pressure' if len(sol.t_events[0]) else 'Mach_or_isothermal_margin' if len(sol.t_events[1]) else 'integrator_failure'
        pe,Te=sol.y[:,-1]*scale
        raise DomainError(f'Incomplete trajectory at x={sol.t[-1]:g} m: {event}; p={pe:g} Pa, T={Te:g} K; {sol.message}')
    x=np.linspace(0,case.L,points); p,T=sol.sol(x)*scale[:,None]
    records=[]
    for xi,pi,Ti in zip(x,p,T):
        _,d=local(case,model,gas,pi,Ti)
        records.append(dict(x_m=xi,p_Pa=pi,T_K=Ti,**d))
    df=pd.DataFrame(records)
    G=case.mdot/(np.pi*case.D**2/4)
    momentum=p[-1]-p[0]+(G*(df.u_m_s.iloc[-1]-df.u_m_s.iloc[0]) if case.acceleration else 0.)+simpson(df.friction_Pa_m,x=x)
    H=df.h_J_kg+(df.u_m_s**2/2 if case.acceleration else 0.)
    heat_specific=simpson(df.q_used_W_m,x=x)/case.mdot
    energy=H.iloc[-1]-H.iloc[0]-heat_specific
    summary=dict(name=case.name,model=model,status='valid',p_out_Pa=p[-1],T_out_K=T[-1],
        dp_Pa=p[0]-p[-1],Q_ground_W=simpson(df.q_ground_W_m,x=x),
        Q_required_W=simpson(df.q_used_W_m,x=x),
        Q_thermostat_W=simpson(df.thermostat_W_m,x=x),
        momentum_residual_Pa=momentum,energy_residual_J_kg=energy,
        momentum_relative=abs(momentum)/max(abs(p[-1]-p[0]),1.),
        energy_relative=abs(energy)/max(abs(heat_specific),abs(H.iloc[-1]-H.iloc[0]),1.),
        mass_relative=float(np.max(abs(df.rho_kg_m3*df.u_m_s/G-1))),
        Re_min=df.Re.min(),Re_max=df.Re.max(),Mach_max=df.Mach.max(),
        T_min_K=T.min(),T_max_K=T.max(),film_fraction_max=df.film_fraction.max(),
        nfev=sol.nfev,accepted_steps=len(sol.t)-1,rtol=rtol,max_step_m=max_step or case.L/40,
        audit_points=points)
    return Result(case,model,df,summary)
