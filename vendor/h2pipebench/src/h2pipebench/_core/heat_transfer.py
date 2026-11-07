"""Developed internal convection and buried cylinder/plane soil conduction."""
import math
from .properties import DomainError


def nusselt(Re, Pr, method='gnielinski', heating=False):
    if Re<=0 or Pr<=0:
        raise DomainError('Nonpositive Re or Pr')
    if Re<2300:
        return 3.66
    if Re<4000:
        raise DomainError('Transitional heat transfer unsupported')
    if method=='gnielinski':
        if not (Re<=5e6 and 0.5<=Pr<=2000):
            raise DomainError(f'Gnielinski outside domain: Re={Re:g}, Pr={Pr:g}')
        f=(0.79*math.log(Re)-1.64)**-2
        return (f/8)*(Re-1000)*Pr/(1+12.7*math.sqrt(f/8)*(Pr**(2/3)-1))
    if method=='dittus_boelter':
        if not (1e4<=Re<=5e6 and 0.6<=Pr<=160):
            raise DomainError('Dittus-Boelter outside adopted domain')
        return 0.023*Re**0.8*Pr**(0.4 if heating else 0.3)
    raise ValueError(f'Unknown heat transfer method: {method}')


def heat_exchange(case, prop, T, Re):
    if case.adiabatic:
        return 0., math.inf, 0., 0.
    Pr=prop.cp_transport*prop.mu/prop.k
    Nu=nusselt(Re,Pr,case.heat_method,case.T_soil>T)*case.nu_multiplier
    hi=Nu*prop.k/case.D
    ri=case.D/2; ro=ri+case.thickness
    film=1/(hi*math.pi*case.D)
    wall=math.log(ro/ri)/(2*math.pi*case.k_steel)
    soil=case.resistance_multiplier*math.acosh(case.depth/ro)/(2*math.pi*case.k_soil)
    resistance=film+wall+soil
    return (case.T_soil-T)/resistance, resistance, Nu, film/resistance
