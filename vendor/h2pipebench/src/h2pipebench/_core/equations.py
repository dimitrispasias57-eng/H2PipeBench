"""Coupled p,T derivatives; see docs/model_derivation.md."""
import numpy as np
from .properties import DomainError
from .friction import darcy_factor
from .heat_transfer import heat_exchange


def local(case, model, gas, p, T):
    s=gas.at(p,T)
    G=case.mdot/(np.pi*case.D**2/4)
    u=G/s.rho; Re=G*case.D/s.mu
    f=case.fixed_f if case.fixed_f is not None else darcy_factor(Re,case.roughness/case.D,case.friction_method)
    q,R,Nu,film_fraction=heat_exchange(case,s,T,Re)
    v2=u*u if case.acceleration else 0.
    a11=1-v2*s.rho_p; a12=-v2*s.rho_T
    a21=s.h_p-v2*s.rho_p/s.rho; a22=s.cp-v2*s.rho_T/s.rho
    det=(a11*a22-a12*a21)/s.cp
    mach=u/s.a
    if det<=0.02 or a11<=0.02 and model in ('M1','M2'):
        raise DomainError('Critical/choking matrix approached')
    friction=f*G*G/(2*case.D*s.rho)
    if model in ('M1','M2'):
        dp=-friction/a11; dT=0.
        q_used=case.mdot*a21*dp
    else:
        dp,dT=np.linalg.solve([[a11,a12],[a21,a22]],[-friction,q/case.mdot])
        q_used=q
    return np.array([dp,dT]), dict(rho_kg_m3=s.rho,h_J_kg=s.h,cp_J_kgK=s.cp,
        u_m_s=u,Re=Re,f_D=f,Z=s.Z,Mach=mach,det_normalized=det,
        isothermal_margin=a11,q_ground_W_m=q,q_used_W_m=q_used,
        thermostat_W_m=q_used-q,R_Km_W=R,Nu=Nu,film_fraction=film_fraction,
        friction_Pa_m=friction,Pr=s.cp_transport*s.mu/s.k)
