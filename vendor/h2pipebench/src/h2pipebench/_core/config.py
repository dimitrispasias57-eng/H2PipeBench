"""Validated configuration. No implicit conversion from bar, gauge pressure or C."""
from dataclasses import dataclass, asdict
import math
from .properties import DomainError

MODELS=('M1','M2','M3','M4')


@dataclass(frozen=True)
class Case:
    name: str='baseline'
    L: float=50000.
    D: float=0.5
    p_in: float=8e6
    T_in: float=313.15
    T_soil: float=283.15
    mdot: float=6.
    roughness: float=2e-5
    thickness: float=0.012
    k_steel: float=45.
    depth: float=1.5
    k_soil: float=1.5
    resistance_multiplier: float=1.
    nu_multiplier: float=1.
    friction_method: str='colebrook'
    heat_method: str='gnielinski'
    adiabatic: bool=False
    fixed_f: float | None=None
    acceleration: bool=True
    p_min: float=1e5
    max_mach: float=0.8

    def validate(self):
        for k in ('L','D','p_in','T_in','T_soil','mdot','thickness','k_steel',
                  'depth','k_soil','resistance_multiplier','nu_multiplier','p_min'):
            v=getattr(self,k)
            if not (math.isfinite(v) and v>0):
                raise DomainError(f'{k} must be finite and positive in SI units')
        if not (self.p_min<self.p_in<=30e6 and 200<=self.T_in<=500 and 200<=self.T_soil<=500):
            raise DomainError('Use absolute Pa and K within the documented envelope')
        if self.p_min<1e5 or not 0<self.max_mach<=0.8:
            raise DomainError('Invalid pressure or conservative Mach guard')
        if self.depth<=self.D/2+self.thickness or not 0<=self.roughness/self.D<=0.05:
            raise DomainError('Invalid burial geometry or roughness')
        if self.fixed_f is not None and not (0<self.fixed_f<1):
            raise DomainError('Invalid constant verification friction factor')
        if self.friction_method not in ('colebrook','haaland') or self.heat_method not in ('gnielinski','dittus_boelter'):
            raise DomainError('Unknown correlation')
        return self

    def dict(self):
        return asdict(self)

