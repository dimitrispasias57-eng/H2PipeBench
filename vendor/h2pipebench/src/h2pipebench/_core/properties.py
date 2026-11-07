"""Normal-hydrogen HEOS and its thermodynamically consistent ideal limit."""
from dataclasses import dataclass
import math
import CoolProp.CoolProp as CP


class DomainError(ValueError):
    """Input or trajectory lies outside the declared model domain."""


@dataclass(frozen=True)
class Properties:
    rho: float
    h: float
    cp: float
    rho_p: float
    rho_T: float
    h_p: float
    mu: float
    k: float
    cp_transport: float
    a: float
    Z: float


class Hydrogen:
    """One mutable CoolProp state per solver; do not share across threads."""
    def __init__(self, ideal=False):
        self.ideal = ideal
        self.state = CP.AbstractState('HEOS', 'Hydrogen')
        self.R = self.state.gas_constant()/self.state.molar_mass()

    def at(self, p, T):
        if not (math.isfinite(p) and math.isfinite(T) and
                5e4 <= p <= 30e6 and 200 <= T <= 500):
            raise DomainError(f'Property envelope violated: p={p:g} Pa, T={T:g} K')
        s=self.state
        s.update(CP.PT_INPUTS, p, T)
        mu,k,cpt=s.viscosity(),s.conductivity(),s.cpmass()
        if self.ideal:
            tau=s.tau()
            cp=self.R*(1-tau*tau*s.d2alpha0_dTau2())
            h=self.R*T*(1+tau*s.dalpha0_dTau())
            rho=p/(self.R*T)
            return Properties(rho,h,cp,rho/p,-rho/T,0.,mu,k,cpt,
                              math.sqrt(cp/(cp-self.R)*self.R*T),1.)
        return Properties(s.rhomass(),s.hmass(),cpt,
                          s.first_partial_deriv(CP.iDmass,CP.iP,CP.iT),
                          s.first_partial_deriv(CP.iDmass,CP.iT,CP.iP),
                          s.first_partial_deriv(CP.iHmass,CP.iP,CP.iT),
                          mu,k,cpt,s.speed_sound(),s.compressibility_factor())
