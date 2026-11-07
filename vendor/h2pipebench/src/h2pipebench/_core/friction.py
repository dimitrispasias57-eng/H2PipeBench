"""Darcy friction factors; no Fanning factors enter the ODE."""
import math
from .properties import DomainError


def darcy_factor(Re, relative_roughness, method='colebrook'):
    if not (math.isfinite(Re) and Re>0 and 0<=relative_roughness<=0.05):
        raise DomainError('Invalid Reynolds number or relative roughness')
    if Re<2300:
        return 64/Re
    if Re<4000:
        raise DomainError('Transitional flow 2300<=Re<4000 is unsupported')
    r=relative_roughness
    y=-1.8*math.log10((r/3.7)**1.11+6.9/Re)
    if method=='haaland':
        return 1/y**2
    if method!='colebrook':
        raise ValueError(f'Unknown friction method: {method}')
    for _ in range(25):
        term=r/3.7+2.51*y/Re
        step=(y+2*math.log10(term))/(1+2/math.log(10)*2.51/Re/term)
        y-=step
        if abs(step)<1e-12:
            return 1/y**2
    raise RuntimeError('Colebrook solve did not converge')


def fanning_from_darcy(f):
    return f/4
