"""Delivery shooting and real-gas isentropic compressor with aftercooler."""
from dataclasses import replace
import CoolProp.CoolProp as CP
from scipy.optimize import brentq
from .properties import DomainError
from .solver import solve


def required_inlet(case, model, target, *, upper=30e6,gas_factory=None):
    if not case.p_min<target<upper:
        raise DomainError('Outlet target outside inverse-search range')
    cache={}
    def forward(p):
        if p not in cache:
            cache[p]=solve(replace(case,p_in=p),model,points=51,gas_factory=gas_factory)
        return cache[p].summary['p_out_Pa']-target
    # Find a feasible bracket. Failed low-pressure trials are not treated as roots.
    low=None; fl=None; high=None; last_failed=None
    p=target*(1+1e-6)
    previous=None
    while p<=upper:
        try:
            f=forward(p)
        except DomainError:
            if previous is not None:
                raise DomainError('Non-monotone feasible domain during inverse search')
            last_failed=p
            p=min(p*1.15,upper) if p<upper else upper+1
            continue
        if previous is not None and f<=previous:
            raise DomainError('Outlet not monotonic in inlet in inverse bracket')
        previous=f
        if f<0:
            low,fl=p,f
        else:
            high=p
            break
        p=min(p*1.15,upper) if p<upper else upper+1
    if high is not None and low is None and last_failed is not None:
        # Resolve a narrow feasible interval without assigning a fabricated outlet
        # pressure to failed trials. Only successful forwards may bracket a root.
        a,b=last_failed,high
        for _ in range(45):
            m=(a+b)/2
            try:
                fm=forward(m)
            except DomainError:
                a=m
                continue
            if fm<0:
                low=m
                break
            b=m; high=m
    if high is None or low is None:
        raise DomainError('No two feasible states bracket the delivery root')
    root=brentq(forward,low,high,xtol=0.02,rtol=2e-10)
    result=solve(replace(case,p_in=root),model,points=201,gas_factory=gas_factory)
    return root,result,result.summary['p_out_Pa']-target


def compressor(p_discharge,mdot,T_pipeline,*,p_suction=2e6,T_suction=298.15,eta_is=0.75,eta_motor=0.95):
    if not (p_suction<=p_discharge<=30e6 and mdot>0 and 0<eta_is<=1 and 0<eta_motor<=1):
        raise DomainError('Invalid compressor pressure ratio or efficiency')
    fluid='HEOS::Hydrogen'
    h1=CP.PropsSI('Hmass','P',p_suction,'T',T_suction,fluid)
    s1=CP.PropsSI('Smass','P',p_suction,'T',T_suction,fluid)
    h2s=CP.PropsSI('Hmass','P',p_discharge,'Smass',s1,fluid)
    w_is=h2s-h1
    h2=h1+w_is/eta_is
    T2=CP.PropsSI('T','P',p_discharge,'Hmass',h2,fluid)
    if T2>1000:
        raise DomainError('Compressor discharge exceeds adopted EOS temperature limit')
    hc=CP.PropsSI('Hmass','P',p_discharge,'T',T_pipeline,fluid)
    return dict(p_suction_Pa=p_suction,T_suction_K=T_suction,p_discharge_Pa=p_discharge,
        eta_is=eta_is,eta_motor=eta_motor,w_is_J_kg=w_is,
        shaft_power_W=mdot*w_is/eta_is,electric_power_W=mdot*w_is/eta_is/eta_motor,
        discharge_T_K=T2,aftercooler_heat_removed_W=mdot*(h2-hc),
        aftercooler_T_K=T_pipeline)
