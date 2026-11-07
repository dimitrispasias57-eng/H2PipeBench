# Method & Limits: scientific and notation audit

Audit date: 7 November 2026. Interface version: 0.1.0rc1-web2.
This revision documents the existing 0.1.0rc1 solver. It does not change its
equations, coefficients, numerical settings, recorded results or benchmark data.
The research manuscripts and notation-audited Word supplement are unchanged.

## Evidence and scope

Each displayed mathematical block was checked against the frozen Python source
below and the project's notation-audited technical supplement. The supplement
was read from its actual Word XML as well as the retained equation audit;
equation numbers below refer to that document, not a new derivation.
No new physical benchmark, validation experiment or research sweep was run.
The regression suite exercises established cases; that is software verification.

There are 45 displayed Streamlit LaTeX blocks, with physical explanations,
and 44 grouped nomenclature rows plus explicit definitions of subscripts,
superscripts and operators. Expanders keep detailed mathematics optional.
The project geometry image remains byte-identical to the original release.

## Scientific findings and clarifications

- Continuity is imposed algebraically through fixed mass flux. The reported
  mass residual is therefore an algebraic check, not an independent PDE solve.
- Momentum retains acceleration by default. Total energy uses static enthalpy
  plus kinetic energy. Disabling acceleration removes the matching terms from
  both differential balances and integral audits; pressure-dependent enthalpy
  remains. No extra friction-heating term is added to total energy.
- M1/M3 use ideal thermodynamic properties with temperature-dependent ideal
  Helmholtz heat capacity. All four modes retain real HEOS viscosity,
  conductivity and transport heat capacity. M2/M4 also use real thermodynamics.
- Gnielinski uses a separate smooth-film friction factor. The momentum Darcy
  factor uses the selected rough-pipe closure. They must not share a symbol.
- Isothermal heat is inferred from the energy equation. Thermostat duty is
  required heat minus environmental heat. Adiabatic environment alone does
  not eliminate the imposed-isothermal thermostat.
- Environmental heat per length is positive into gas. The unchanged geometry's
  outward arrows illustrate warmer gas and therefore negative environmental
  heat. The pipe bore is D=2r_i, wall thickness is r_o-r_i, and H_b is centreline
  burial depth. T_in, T_infinity, p_in, p_del, mass-flow dot and roughness epsilon
  are consistent with the equation and nomenclature definitions.
- DOP853 advances in distance. Audit samples are not finite elements or time
  steps. The solid-conduction finite-element benchmark is separate from gas
  flow and is not a transient soil solver coupled to this web calculation.
- Conservation residuals and tolerance refinement concern numerical solution
  consistency. Independent algorithms sharing HEOS/closures and constrained
  pandapipes comparisons do not establish experimental accuracy. Unresolved
  laboratory-loop discrepancies and lack of full-scale validation are retained.
- Compressor electricity is a power rate. Incremental transport power uses a
  common suction-to-delivery baseline. Equipment maps, staging optimization,
  cooler electricity and structural/material suitability are outside scope.

## Dimensional review

| Relation | Dimensional check |
|---|---|
| Continuity | rho u A and mass flow: kg/s; its axial derivative: kg/(s m) |
| Momentum | dp/dx, G du/dx and F: Pa/m |
| Darcy loss | f_D G^2/(2 D rho): kg/(m^2 s^2) = Pa/m |
| Total energy | d(h+u^2/2)/dx and q'/mass flow: J/(kg m) |
| ODE momentum coefficients | 1-u^2 rho_p is dimensionless; u^2 rho_T has Pa/K |
| ODE energy coefficients | h_p-u^2 rho_p/rho: J/(kg Pa); c_p-u^2 rho_T/rho: J/(kg K) |
| Real density identity | p/(Z R T): kg/m^3 |
| Thermodynamic h_p identity | (1+T rho_T/rho)/rho: m^3/kg = J/(kg Pa) |
| Ideal Helmholtz properties | h: J/kg; c_p: J/(kg K); tau and alpha derivatives: dimensionless |
| Reynolds, Prandtl, Nusselt | Dimensionless with transport c_p in Prandtl |
| Film coefficient | Nu k_g/D: W/(m^2 K) |
| Thermal resistance | Every series term: K m/W, so (T_infinity-T)/R: W/m |
| Integrated heat | Integral of W/m over length: W |
| Momentum/energy audits | Pa and J/kg; normalized residuals dimensionless, with unit-bearing floors |
| Compressor and cooler | Mass flow times enthalpy rise/difference: W; efficiencies dimensionless |
| Logarithm arguments | Relative roughness, Re, radius ratios and depth/radius: dimensionless |

S_h is only a notation alias for the solver's energy-residual denominator,
not a new model coefficient. A prime denotes heat rate per length, not a
derivative. R (specific gas constant) and calligraphic R (thermal resistance),
h (enthalpy) and h_i (film coefficient), and H (total enthalpy) and H_b (depth)
are distinguished explicitly. Every mathematical argument and sign follows
the source; explanatory identities are labelled as identities or checks.

## Equation-to-source map

| Web equation key | Unmodified implementation / existing test | Audited supplement |
|---|---|---|
| `geometry` | [config.py](../vendor/h2pipebench/src/h2pipebench/_core/config.py) | Fig. S1; Section S3 (geometry and resistance) |
| `forward` | [solver.py](../vendor/h2pipebench/src/h2pipebench/_core/solver.py) | Section S4 (boundary conditions and numerical method) |
| `inverse` | [compression.py](../vendor/h2pipebench/src/h2pipebench/_core/compression.py) | Section S4 (delivery boundary and inversion) |
| `mass` | [equations.py](../vendor/h2pipebench/src/h2pipebench/_core/equations.py) | Eq. S1 |
| `area` | [equations.py](../vendor/h2pipebench/src/h2pipebench/_core/equations.py) | Eq. S1 |
| `momentum` | [equations.py](../vendor/h2pipebench/src/h2pipebench/_core/equations.py) | Eq. S2 |
| `loss` | [equations.py](../vendor/h2pipebench/src/h2pipebench/_core/equations.py) | Eq. S2 |
| `drop` | [solver.py](../vendor/h2pipebench/src/h2pipebench/_core/solver.py) | Eq. S2 |
| `energy` | [equations.py](../vendor/h2pipebench/src/h2pipebench/_core/equations.py) | Eq. S3 |
| `real` | [properties.py](../vendor/h2pipebench/src/h2pipebench/_core/properties.py) | Eq. S8 |
| `rho_derivatives` | [properties.py](../vendor/h2pipebench/src/h2pipebench/_core/properties.py) | Section S2, definitions following Eq. S5 |
| `h_derivatives` | [properties.py](../vendor/h2pipebench/src/h2pipebench/_core/properties.py) | Section S2, definitions following Eq. S5 |
| `identity` | [properties.py](../vendor/h2pipebench/src/h2pipebench/_core/properties.py); [test_core_physics.py](../tests/solver/test_core_physics.py) | Eq. S6 |
| `ideal` | [properties.py](../vendor/h2pipebench/src/h2pipebench/_core/properties.py) | Eq. S10 |
| `ideal_h` | [properties.py](../vendor/h2pipebench/src/h2pipebench/_core/properties.py) | Eq. S10 |
| `ideal_d` | [properties.py](../vendor/h2pipebench/src/h2pipebench/_core/properties.py) | Eq. S11 |
| `re` | [equations.py](../vendor/h2pipebench/src/h2pipebench/_core/equations.py) | Eq. S12 |
| `colebrook` | [friction.py](../vendor/h2pipebench/src/h2pipebench/_core/friction.py) | Eq. S12 |
| `haaland` | [friction.py](../vendor/h2pipebench/src/h2pipebench/_core/friction.py) | Eq. S13 |
| `laminar` | [friction.py](../vendor/h2pipebench/src/h2pipebench/_core/friction.py) | Eq. S13 |
| `heat` | [heat_transfer.py](../vendor/h2pipebench/src/h2pipebench/_core/heat_transfer.py) | Eq. S14 |
| `resistance` | [heat_transfer.py](../vendor/h2pipebench/src/h2pipebench/_core/heat_transfer.py) | Eq. S14 |
| `film` | [heat_transfer.py](../vendor/h2pipebench/src/h2pipebench/_core/heat_transfer.py) | Eq. S16 |
| `smooth` | [heat_transfer.py](../vendor/h2pipebench/src/h2pipebench/_core/heat_transfer.py) | Eq. S15 |
| `gnielinski` | [heat_transfer.py](../vendor/h2pipebench/src/h2pipebench/_core/heat_transfer.py) | Eq. S15 |
| `db` | [heat_transfer.py](../vendor/h2pipebench/src/h2pipebench/_core/heat_transfer.py) | Eq. S16 |
| `laminar_heat` | [heat_transfer.py](../vendor/h2pipebench/src/h2pipebench/_core/heat_transfer.py) | Section S3, laminar closure |
| `ode_p` | [equations.py](../vendor/h2pipebench/src/h2pipebench/_core/equations.py) | Eq. S5 |
| `ode_T` | [equations.py](../vendor/h2pipebench/src/h2pipebench/_core/equations.py) | Eq. S5 |
| `coupled_heat` | [equations.py](../vendor/h2pipebench/src/h2pipebench/_core/equations.py) | Eqs. S3 and S14 |
| `iso` | [equations.py](../vendor/h2pipebench/src/h2pipebench/_core/equations.py) | Eq. S17 |
| `iso_heat` | [equations.py](../vendor/h2pipebench/src/h2pipebench/_core/equations.py) | Eq. S17 |
| `thermostat` | [equations.py](../vendor/h2pipebench/src/h2pipebench/_core/equations.py) | Eq. S18 |
| `Q` | [solver.py](../vendor/h2pipebench/src/h2pipebench/_core/solver.py) | Eq. S18 |
| `scaled` | [solver.py](../vendor/h2pipebench/src/h2pipebench/_core/solver.py) | Section S4, normalized states |
| `rp` | [solver.py](../vendor/h2pipebench/src/h2pipebench/_core/solver.py) | Eq. S19 |
| `H` | [solver.py](../vendor/h2pipebench/src/h2pipebench/_core/solver.py) | Eq. S20 |
| `rh` | [solver.py](../vendor/h2pipebench/src/h2pipebench/_core/solver.py) | Eq. S20 |
| `ep` | [solver.py](../vendor/h2pipebench/src/h2pipebench/_core/solver.py) | Eq. S21 |
| `eh` | [solver.py](../vendor/h2pipebench/src/h2pipebench/_core/solver.py) | Eq. S21 |
| `em` | [solver.py](../vendor/h2pipebench/src/h2pipebench/_core/solver.py) | Section S4, algebraic mass diagnostic |
| `mach` | [equations.py](../vendor/h2pipebench/src/h2pipebench/_core/equations.py); [properties.py](../vendor/h2pipebench/src/h2pipebench/_core/properties.py) | Eqs. S7 and S11 |
| `compression` | [compression.py](../vendor/h2pipebench/src/h2pipebench/_core/compression.py) | Eq. S22 |
| `increment` | [h2web/calculations.py](../h2web/calculations.py) | Eq. S22 |
| `cooler` | [compression.py](../vendor/h2pipebench/src/h2pipebench/_core/compression.py) | Eq. S23 |

## Rendering and regression checks

The UI uses `st.latex`, with Streamlit's KaTeX renderer. Mathematical labels
inside nomenclature tables use inline LaTeX. The retained geometry is shown
with a caption explaining its signs and its separate solid benchmark.
See [executed testing evidence](TESTING.md) for the completed interface tests,
viewport checks and deployment verification. These are browser viewport tests,
not physical-device certification or universal cross-browser coverage.

Official renderer reference: [Streamlit st.latex](https://docs.streamlit.io/develop/api-reference/text/st.latex).
Property-library reference: [CoolProp hydrogen](https://coolprop.org/fluid_properties/fluids/Hydrogen.html).
