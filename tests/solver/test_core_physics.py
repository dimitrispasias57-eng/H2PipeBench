from dataclasses import replace
import math
import numpy as np
import pytest
from scipy.optimize import brentq
from h2pipebench._core.config import Case,MODELS
from h2pipebench._core.properties import Hydrogen,DomainError
from h2pipebench._core.friction import darcy_factor,fanning_from_darcy
from h2pipebench._core.heat_transfer import nusselt
from h2pipebench._core.equations import local
from h2pipebench._core.solver import solve
from h2pipebench._core.compression import required_inlet,compressor


@pytest.mark.parametrize('ideal',[False,True])
@pytest.mark.parametrize('p,T',[(4e6,283.15),(8e6,298.15),(12e6,313.15)])
def test_properties_derivatives(ideal,p,T):
    g=Hydrogen(ideal); s=g.at(p,T)
    dp=p*1e-5; dt=T*1e-5
    sp,sm=g.at(p+dp,T),g.at(p-dp,T)
    st,sb=g.at(p,T+dt),g.at(p,T-dt)
    assert s.rho_p==pytest.approx((sp.rho-sm.rho)/(2*dp),rel=2e-7)
    assert s.rho_T==pytest.approx((st.rho-sb.rho)/(2*dt),rel=2e-7)
    assert s.h_p==pytest.approx((sp.h-sm.h)/(2*dp),rel=2e-6,abs=1e-9)
    assert s.cp==pytest.approx((st.h-sb.h)/(2*dt),rel=2e-7)
    assert s.h_p==pytest.approx((1+T*s.rho_T/s.rho)/s.rho,abs=1e-12)
    assert 10000<s.cp<17000 and 7e-6<s.mu<12e-6 and 0.15<s.k<0.25


def test_friction_convention_and_colebrook():
    Re=2e6; r=1e-4; f=darcy_factor(Re,r)
    assert abs(1/math.sqrt(f)+2*math.log10(r/3.7+2.51/(Re*math.sqrt(f))))<1e-11
    assert fanning_from_darcy(f)==f/4
    rho,u,D=6.,10.,.5
    tau=f*rho*u*u/8
    assert 4*tau/D==pytest.approx(f*rho*u*u/(2*D))
    assert darcy_factor(1000,0)==.064
    assert abs(darcy_factor(Re,r,'haaland')/f-1)<0.02


@pytest.mark.parametrize('acceleration',[False,True])
def test_exact_isothermal(acceleration):
    c=Case(L=1e5,mdot=6,fixed_f=.013,acceleration=acceleration)
    r=solve(c,'M1'); G=c.mdot/(np.pi*c.D**2/4); C=G**2*Hydrogen().R*c.T_in
    def residual(p):
        return c.p_in**2-p**2-(2*C*np.log(c.p_in/p) if acceleration else 0)-c.fixed_f*C*c.L/c.D
    p=brentq(residual,.7*c.p_in,c.p_in)
    assert r.summary['p_out_Pa']==pytest.approx(p,rel=2e-9)


@pytest.mark.parametrize('model',MODELS)
def test_conservation_and_convergence(model):
    c=Case()
    a=solve(c,model,points=801)
    b=solve(c,model,rtol=2e-10,max_step=c.L/100,points=801)
    assert a.summary['mass_relative']<1e-14
    assert a.summary['momentum_relative']<1e-7
    assert a.summary['energy_relative']<1e-6
    assert abs(a.summary['p_out_Pa']-b.summary['p_out_Pa'])<0.1
    assert abs(a.summary['T_out_K']-b.summary['T_out_K'])<1e-5
    assert np.all(np.diff(a.profile.p_Pa)<0)


@pytest.mark.parametrize('model',['M3','M4'])
def test_adiabatic_and_characteristic_determinant(model):
    c=Case(adiabatic=True,mdot=6)
    r=solve(c,model)
    H=r.profile.h_J_kg+r.profile.u_m_s**2/2
    assert np.ptp(H)<1e-4
    np.testing.assert_allclose(r.profile.det_normalized,1-r.profile.Mach**2,rtol=2e-12)
    if model=='M4': assert r.summary['T_out_K']>c.T_in  # normal H2 warms in this regime
    else: assert r.summary['T_out_K']<c.T_in


def test_isothermal_heat_constraint():
    r=solve(Case(),'M2')
    assert np.all(r.profile.T_K==Case().T_in)
    assert abs(r.summary['Q_thermostat_W'])>1000
    assert r.summary['energy_relative']<1e-7


@pytest.mark.parametrize('changes',[{'p_in':80.},{'T_in':25.},{'mdot':-1.},{'depth':.1},{'roughness':-.001},{'mdot':5000.}])
def test_invalid_inputs(changes):
    with pytest.raises(DomainError): solve(replace(Case(),**changes))


def test_excessive_length_and_correlation_domain():
    with pytest.raises(DomainError): solve(Case(L=2e8,mdot=10))
    with pytest.raises(DomainError): nusselt(6e6,.7)
    with pytest.raises(DomainError): darcy_factor(3000,0)
    assert nusselt(1000,.7)==3.66


@pytest.mark.parametrize('model',MODELS)
def test_inverse_roundtrip(model):
    c=Case(L=1e4)
    target=solve(c,model).summary['p_out_Pa']
    p,_,err=required_inlet(c,model,target)
    assert p==pytest.approx(c.p_in,abs=.1)
    assert abs(err)<.1


def test_compressor_entropy_and_efficiency():
    import CoolProp.CoolProp as CP
    a=compressor(8e6,6,313.15)
    b=compressor(8e6,6,313.15,eta_is=1,eta_motor=1)
    assert a['electric_power_W']==pytest.approx(b['electric_power_W']/(.75*.95))
    s1=CP.PropsSI('Smass','P',2e6,'T',298.15,'Hydrogen')
    s2=CP.PropsSI('Smass','P',8e6,'T',b['discharge_T_K'],'Hydrogen')
    assert s2==pytest.approx(s1,rel=1e-10)
    assert a['aftercooler_heat_removed_W']>0
    assert compressor(2e6,6,298.15)['electric_power_W']==pytest.approx(0,abs=1e-6)


def test_inverse_from_infeasible_low_pressure():
    c=Case(D=.2,L=1e5,p_in=12e6,mdot=2.8,thickness=.008)
    with pytest.raises(DomainError): solve(replace(c,p_in=4e6),'M4')
    p,result,err=required_inlet(c,'M4',4e6)
    assert 4e6<p<20e6
    assert abs(err)<.1
    assert result.summary['Mach_max']<c.max_mach


def test_real_adiabatic_entropy_production():
    import CoolProp.CoolProp as CP
    c=Case(adiabatic=True)
    r=solve(c,'M4')
    sin=CP.PropsSI('Smass','P',c.p_in,'T',c.T_in,'Hydrogen')
    sout=CP.PropsSI('Smass','P',r.summary['p_out_Pa'],'T',r.summary['T_out_K'],'Hydrogen')
    assert sout>sin
