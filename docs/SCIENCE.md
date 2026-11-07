# Scientific scope and numerical provenance

The interface uses the notation-audited H2PipeBench manuscript and supplement
as scientific references without redistributing or editing those manuscripts.
Equations in the app are transcribed from that existing evidence and checked
against the package. No new governing equations or empirical coefficients were
introduced.

For area A, mass flux G = mass_flow/A and velocity u = G/rho:

```text
d(rho*u*A)/dx = 0
dp/dx + G*du/dx = -f_D*G^2/(2*D*rho)
d(h + u^2/2)/dx = q_used_per_length/mass_flow
```

Real modes use HEOS hydrogen properties. Ideal modes use ideal Helmholtz
thermodynamics while retaining HEOS viscosity, conductivity and transport heat
capacity. Heat transfer adds gas-film, cylindrical-wall and buried-cylinder
soil resistance per pipe length. Isothermal operation is a thermal constraint;
its implied thermostat duty is reported, not omitted.

DOP853 uses relative tolerance 2e-8, normalized absolute tolerance 2e-11,
maximum step L/40 and dense output. Forward runs use 801 audit samples to match
the archived examples. The inverse API uses its unchanged 201-point final
audit and Brent search. Simpson-integrated residuals are numerical diagnostics,
not measured uncertainty. The mass diagnostic is algebraic consistency.

Pipeline outputs are pressure (Pa absolute), temperature (K), density (kg/m^3),
velocity (m/s), enthalpy (J/kg), heat capacity (J/(kg K)), Darcy factor,
Reynolds/Mach/Prandtl/Nusselt numbers and compressibility (dimensionless), local
heat (W/m), local pressure-loss rate (Pa/m), thermal resistance (K m/W), film
fraction and critical-state margins (dimensionless). Integrated heat is W.
Charts and metrics convert only units; exports identify all source units.

The single-stage compressor uses isentropic enthalpy rise divided by
isentropic and motor efficiencies. Incremental transport electrical power is
the total required-pressure value minus a common suction-to-delivery baseline.
Aftercooler heat is positive when removed; negative values mean required heat
input. Aftercooler electricity, staging, equipment maps and ratings are absent.

The app demonstrates an existing package. It provides no novel experimental
evidence, no full-scale accuracy bound, and no industrial design approval.
The numerical comparison to pandapipes in the project matches a constrained
ideal hydraulic limit and is not a ranking of physical accuracy. Laboratory
loop discrepancies and incomplete experimental boundaries remain unresolved.

## Primary references

- Leachman et al., hydrogen EOS: https://doi.org/10.1063/1.3160306
- Bell et al., CoolProp: https://doi.org/10.1021/ie4033999
- Hydrogen model documentation: https://coolprop.org/fluid_properties/fluids/Hydrogen.html
- Lohmeier et al., pandapipes: https://doi.org/10.3390/su12239899
- Yang et al., laboratory comparison source: https://doi.org/10.3969/j.issn.1006-5539.2025.05.011

The citations identify sources already used in the research. No third-party
article or measured dataset is bundled. The project geometry is original
Python/vector artwork, not generative raster art or a reproduced journal figure.
