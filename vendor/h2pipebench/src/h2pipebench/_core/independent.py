"""Independent implicit-midpoint finite-volume conservation audit.

No reuse of local(), property derivatives, production friction or heat routines.
Shared constitutive references: CoolProp HEOS, Colebrook, Gnielinski and buried
cylinder resistance. Agreement is numerical verification, not physical validation.
"""
import math
import numpy as np
import pandas as pd
import CoolProp.CoolProp as CP
from scipy.optimize import root,brentq

def finite_volume(c,model,segments=400):
    state=CP.AbstractState('HEOS','Hydrogen')
    Rgas=state.gas_constant()/state.molar_mass()
    G=4*c.mdot/(math.pi*c.D**2);dx=c.L/segments
    iso=model in ('M1','M2');ideal=model in ('M1','M3')
    def values(p,T):
        state.update(CP.PT_INPUTS,p,T)
        rho=p/(Rgas*T) if ideal else state.rhomass()
        h=Rgas*T*(1+state.tau()*state.dalpha0_dTau()) if ideal else state.hmass()
        u=G/rho;Re=G*c.D/state.viscosity()
        if c.fixed_f is not None:f=c.fixed_f
        elif Re<2300:f=64/Re
        elif c.friction_method=='haaland':f=(-1.8*math.log10((c.roughness/c.D/3.7)**1.11+6.9/Re))**-2
        else:f=brentq(lambda f:1/math.sqrt(f)+2*math.log10(c.roughness/c.D/3.7+2.51/(Re*math.sqrt(f))),.002,.2,xtol=1e-14)
        friction=f*G**2/(2*c.D*rho)
        if c.adiabatic:q=0.;res=math.inf
        else:
            Pr=state.cpmass()*state.viscosity()/state.conductivity()
            fs=(.79*math.log(Re)-1.64)**-2
            nu=3.66 if Re<2300 else (fs/8)*(Re-1000)*Pr/(1+12.7*math.sqrt(fs/8)*(Pr**(2/3)-1))
            if c.heat_method=='dittus_boelter':nu=.023*Re**.8*Pr**(.4 if c.T_soil>T else .3)
            hi=nu*c.nu_multiplier*state.conductivity()/c.D
            res=1/(hi*math.pi*c.D)+math.log((c.D/2+c.thickness)/(c.D/2))/(2*math.pi*c.k_steel)+c.resistance_multiplier*math.acosh(c.depth/(c.D/2+c.thickness))/(2*math.pi*c.k_soil)
            q=(c.T_soil-T)/res
        J=p+(G*u if c.acceleration else 0)
        E=h+(u*u/2 if c.acceleration else 0)
        return J,E,friction,q,rho,h,res
    y=np.array([c.p_in,c.T_in]);rows=[];mom=0.;energy=0.
    v0=values(*y);rows.append(dict(x_m=0,p_Pa=y[0],T_K=y[1]))
    scale=np.array([c.p_in,300.]);escale=4e6
    for k in range(segments):
        old=y.copy();v=values(*old)
        def residual(z):
            now=z*scale
            if iso:now[1]=c.T_in
            vn=values(*now);mid=values(*((old+now)/2))
            return [(vn[0]-v[0]+dx*mid[2])/c.p_in,
                    (z[1]-c.T_in/scale[1]) if iso else (vn[1]-v[1]-dx*mid[3]/c.mdot)/escale]
        sol=root(residual,old/scale,tol=2e-11)
        if np.max(np.abs(residual(sol.x)))>2e-10:raise RuntimeError('FV nonlinear residual too large')
        y=sol.x*scale;vn=values(*y);mid=values(*((old+y)/2))
        mom+=vn[0]-v[0]+dx*mid[2]
        energy+=vn[1]-v[1]-(vn[1]-v[1] if iso else dx*mid[3]/c.mdot)
        rows.append(dict(x_m=(k+1)*dx,p_Pa=y[0],T_K=y[1]))
    return dict(p_out_Pa=y[0],T_out_K=y[1],dp_Pa=c.p_in-y[0],
                discrete_momentum_residual_Pa=mom,discrete_energy_residual_J_kg=energy,
                iso_energy_enforced=not iso),pd.DataFrame(rows)
