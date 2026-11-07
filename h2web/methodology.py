"""Educational equations checked against the unchanged solver and audited supplement.

This module renders documentation; it is not a second numerical implementation.
"""
from pathlib import Path
import streamlit as st

# LaTeX, physical meaning, source in vendored _core, audited supplement reference.
EQUATIONS = {
    'geometry': (r'D=2r_i,\quad r_o=r_i+t_w,\quad H_b>r_o',
        'The bore defines the flow diameter. Burial depth is measured from the ground surface to the pipe centreline, not to its crown.', 'config.py', 'S3 / Fig. S1'),
    'forward': (r'p(0)=p_{\mathrm{in}},\qquad T(0)=T_{\mathrm{in}}',
        'A forward run prescribes inlet pressure and temperature and predicts the outlet at a specified mass flow.', 'solver.py', 'S4'),
    'inverse': (r'p(L;p_{\mathrm{req}})=p_{\mathrm{del}}',
        'Delivery inversion varies inlet pressure until the computed outlet reaches the target, holding mass flow, inlet temperature and other physical inputs fixed.', 'compression.py', 'S4'),
    'mass': (r'\frac{d(\rho uA)}{dx}=0,\qquad \dot m=\rho uA',
        'The same mass crosses each pipe section. The model has no leaks, injections or branches.', 'equations.py', 'S1'),
    'area': (r'A=\frac{\pi D^2}{4},\qquad G=\frac{\dot m}{A},\qquad u=\frac{G}{\rho}',
        'Constant area and prescribed mass flow fix mass flux. Velocity changes as density changes.', 'equations.py', 'S1'),
    'momentum': (r'\frac{dp}{dx}+G\frac{du}{dx}=-F',
        'Pressure forces balance axial momentum changes and wall friction. Every term has units Pa/m.', 'equations.py', 'S2'),
    'loss': (r'F=\frac{f_DG^2}{2D\rho}=\frac{f_D\rho u^2}{2D}',
        'This is the positive Darcy wall-friction pressure-loss term per length, not compressor electrical power.', 'equations.py', 'S2'),
    'drop': (r'\Delta p=p(0)-p(L)',
        'Reported pressure drop is inlet minus outlet absolute pressure, including acceleration effects when enabled.', 'solver.py', 'S2'),
    'energy': (r'\frac{d}{dx}\left(h+\frac{u^2}{2}\right)=\frac{q_{\mathrm{used}}^{\prime}}{\dot m}',
        'Heat entering the gas changes specific total enthalpy: static enthalpy plus kinetic energy. Both sides have units J/(kg m).', 'equations.py', 'S3'),
    'real': (r'\rho=\frac{p}{ZRT}',
        'Compressibility relates real-gas density to pressure and temperature. HEOS supplies the real-fluid state; this identity is not a separately fitted EOS.', 'properties.py', 'S8'),
    'rho_derivatives': (r'\rho_p=\left(\frac{\partial\rho}{\partial p}\right)_T,\qquad \rho_T=\left(\frac{\partial\rho}{\partial T}\right)_p',
        'Density derivatives describe changes in one thermodynamic variable while holding the other fixed.', 'properties.py', 'S2'),
    'h_derivatives': (r'c_p=\left(\frac{\partial h}{\partial T}\right)_p,\qquad h_p=\left(\frac{\partial h}{\partial p}\right)_T',
        'Heat capacity describes temperature-dependent enthalpy. The pressure derivative retains real-gas pressure–enthalpy effects.', 'properties.py', 'S2'),
    'identity': (r'h_p=\frac{1+T\rho_T/\rho}{\rho}',
        'The retained tests check this thermodynamic identity against library derivatives. The real-gas solver requests the derivative directly from CoolProp.', 'properties.py; test_core_physics.py', 'S6'),
    'ideal': (r'\rho_{\mathrm{id}}=\frac{p}{RT},\qquad Z_{\mathrm{id}}=1',
        'The ideal branch uses ideal-gas density at the local pressure and temperature.', 'properties.py', 'S10'),
    'ideal_h': (r'\begin{gathered}\tau=T_c/T,\\h_{\mathrm{id}}=RT(1+\tau\alpha^0_\tau),\\c_{p,\mathrm{id}}=R(1-\tau^2\alpha^0_{\tau\tau})\end{gathered}',
        'Ideal enthalpy and heat capacity use the ideal Helmholtz contribution from the same hydrogen library. Heat capacity is temperature dependent, not assumed constant.', 'properties.py', 'S10'),
    'ideal_d': (r'\begin{gathered}\rho_{p,\mathrm{id}}=\rho_{\mathrm{id}}/p,\\\rho_{T,\mathrm{id}}=-\rho_{\mathrm{id}}/T,\qquad h_{p,\mathrm{id}}=0\end{gathered}',
        'These are the exact density and enthalpy derivatives used by the ideal thermodynamic branch.', 'properties.py', 'S11'),
    're': (r'\mathrm{Re}=\frac{GD}{\mu}',
        'Reynolds number compares inertia with viscous effects and selects the supported friction regime.', 'equations.py', 'S12'),
    'colebrook': (r'\frac{1}{\sqrt{f_D}}=-2\log_{10}\!\left[\frac{\epsilon}{3.7D}+\frac{2.51}{\mathrm{Re}\sqrt{f_D}}\right]',
        'The default turbulent Darcy factor depends implicitly on Reynolds number and equivalent sand-grain roughness.', 'friction.py', 'S12'),
    'haaland': (r'f_D=\left\{-1.8\log_{10}\!\left[\left(\frac{\epsilon}{3.7D}\right)^{1.11}+\frac{6.9}{\mathrm{Re}}\right]\right\}^{-2}',
        'The selectable Haaland closure explicitly approximates the turbulent Darcy factor using the same roughness and Reynolds number.', 'friction.py', 'S13'),
    'laminar': (r'f_D=64/\mathrm{Re}\qquad(\mathrm{Re}<2300)',
        'The laminar branch uses this Darcy factor. Transitional flow from Reynolds number 2300 to below 4000 is rejected.', 'friction.py', 'S13'),
    'heat': (r'q_{\mathrm{ground}}^{\prime}=\frac{T_\infty-T}{\mathcal R}',
        'Heat is positive into the gas. Gas warmer than its surroundings loses heat, so this quantity is negative.', 'heat_transfer.py', 'S14'),
    'resistance': (r'\begin{aligned}\mathcal R={}&\frac{1}{h_i\pi D}\\&+\frac{\ln(r_o/r_i)}{2\pi k_w}\\&+\frac{\operatorname{acosh}(H_b/r_o)}{2\pi k_s}\end{aligned}',
        'Gas-film convection, cylindrical wall conduction and buried-cylinder/plane soil conduction act in series. Each term has units K m/W.', 'heat_transfer.py', 'S14'),
    'film': (r'\mathrm{Pr}=\frac{c_{p,\mathrm{tr}}\mu}{k_g},\qquad h_i=\frac{\mathrm{Nu}\,k_g}{D}',
        'HEOS transport heat capacity, viscosity and conductivity set Prandtl number. Nusselt number gives the gas-film heat-transfer coefficient.', 'heat_transfer.py', 'S16'),
    'smooth': (r'f_s=(0.79\ln\mathrm{Re}-1.64)^{-2}',
        'Gnielinski uses this separate smooth-film factor. It does not reuse the rough-pipe Darcy factor from the momentum equation.', 'heat_transfer.py', 'S15'),
    'gnielinski': (r'\mathrm{Nu}=\frac{(f_s/8)(\mathrm{Re}-1000)\mathrm{Pr}}{1+12.7\sqrt{f_s/8}\left(\mathrm{Pr}^{2/3}-1\right)}',
        'The default turbulent convection correlation combines Reynolds and Prandtl numbers within its adopted applicability limits.', 'heat_transfer.py', 'S15'),
    'db': (r'\begin{gathered}\mathrm{Nu}=0.023\,\mathrm{Re}^{0.8}\mathrm{Pr}^{n},\\n=\begin{cases}0.4,&T_\infty>T,\\0.3,&T_\infty\leq T.\end{cases}\end{gathered}',
        'Dittus–Boelter uses the heating exponent when the surroundings are warmer. The code uses 0.3 otherwise, including equal temperatures.', 'heat_transfer.py', 'S16'),
    'laminar_heat': (r'\mathrm{Nu}=3.66\qquad(\mathrm{Re}<2300)',
        'This is the adopted fully developed laminar limit, not a general solution for mixed thermal boundary conditions.', 'heat_transfer.py', 'S3'),
    'ode_p': (r'\left(1-u^2\rho_p\right)\frac{dp}{dx}-u^2\rho_T\frac{dT}{dx}=-F',
        'Substituting velocity as mass flux divided by density turns momentum into a pressure–temperature differential equation.', 'equations.py', 'S5'),
    'ode_T': (r'\begin{aligned}&\left(h_p-\frac{u^2\rho_p}{\rho}\right)\frac{dp}{dx}\\&+\left(c_p-\frac{u^2\rho_T}{\rho}\right)\frac{dT}{dx}=\frac{q_{\mathrm{used}}^{\prime}}{\dot m}\end{aligned}',
        'This is the energy row of the implemented two-by-two linear system. Coupled modes solve both rows for the axial derivatives.', 'equations.py', 'S5'),
    'coupled_heat': (r'q_{\mathrm{used}}^{\prime}=q_{\mathrm{ground}}^{\prime}\qquad(\mathrm{M3},\mathrm{M4})',
        'Coupled modes let temperature vary and use modelled environmental heat in total energy.', 'equations.py', 'S3 / S14'),
    'iso': (r'\begin{gathered}T(x)=T_{\mathrm{in}},\qquad dT/dx=0,\\\frac{dp}{dx}=\frac{-F}{1-u^2\rho_p}\end{gathered}',
        'M1 and M2 impose constant gas temperature and integrate the remaining momentum equation.', 'equations.py', 'S17'),
    'iso_heat': (r'q_{\mathrm{used}}^{\prime}=\dot m\left(h_p-\frac{u^2\rho_p}{\rho}\right)\frac{dp}{dx}',
        'Required heat is inferred from energy to maintain constant temperature. It need not equal passive ground heat.', 'equations.py', 'S17'),
    'thermostat': (r'q_{\mathrm{th}}^{\prime}=q_{\mathrm{used}}^{\prime}-q_{\mathrm{ground}}^{\prime}',
        'Thermostat duty is the additional heating or cooling needed to enforce isothermality.', 'equations.py', 'S18'),
    'Q': (r'Q_j=\int_0^L q_j^{\prime}\,dx,\quad j\in\{\mathrm{used},\mathrm{ground},\mathrm{th}\}',
        'Integrating heat per length gives a heat rate in watts, not an energy in joules.', 'solver.py', 'S18'),
    'scaled': (r'y_p=p/p_{\mathrm{in}},\qquad y_T=T/T_{\mathrm{in}}',
        'Dimensionless states prevent the very different pressure and temperature scales from dominating adaptive error control.', 'solver.py', 'S4'),
    'rp': (r'\begin{aligned}r_p={}&p(L)-p(0)\\&+G[u(L)-u(0)]+\int_0^L F\,dx\end{aligned}',
        'Separate quadrature of the integral momentum balance checks numerical accounting. This residual has units Pa.', 'solver.py', 'S19'),
    'H': (r'H=h+u^2/2',
        'Specific total enthalpy includes kinetic energy. It differs from burial depth, written with subscript b.', 'solver.py', 'S20'),
    'rh': (r'r_h=H(L)-H(0)-\frac{1}{\dot m}\int_0^L q_{\mathrm{used}}^{\prime}\,dx',
        'The integral energy residual has units J/kg. A small balance error alone does not establish physical prediction accuracy.', 'solver.py', 'S20'),
    'ep': (r'e_p=\frac{|r_p|}{\max\left(|p(L)-p(0)|,\,1\,\mathrm{Pa}\right)}',
        'Momentum residual is scaled by the actual pressure change with a 1 Pa floor.', 'solver.py', 'S21'),
    'eh': (r'\begin{gathered}S_h=\max\left\{\begin{array}{l}|H(L)-H(0)|,\\|Q_{\mathrm{used}}/\dot m|,\\1\,\mathrm{J/kg}\end{array}\right\},\\e_h=|r_h|/S_h\end{gathered}',
        'The energy scale is the largest of total-enthalpy change, exchanged heat per mass and a 1 J/kg floor. S with subscript h abbreviates the implemented denominator.', 'solver.py', 'S21'),
    'em': (r'e_{\mathrm{mass}}=\max_x\left|\rho u/G-1\right|',
        'This samples algebraic mass consistency because velocity is constructed from mass flux divided by density. It is not an independently integrated continuity check.', 'solver.py', 'S4'),
    'mach': (r'M=u/a',
        'Mach number uses sound speed from the selected thermodynamic branch and forms part of the numerical guards.', 'equations.py; properties.py', 'S7 / S11'),
    'compression': (r'\begin{gathered}h_1=h(p_1,T_1),\quad s_1=s(p_1,T_1),\\h_{2s}=h(p_2,s_1),\\P_{\mathrm{el}}=\frac{\dot m(h_{2s}-h_1)}{\eta_{\mathrm{is}}\eta_m}\end{gathered}',
        'Real-hydrogen isentropic enthalpy rise and the specified isentropic/motor efficiencies give compressor electrical power.', 'compression.py', 'S22'),
    'increment': (r'\Delta P_{\mathrm{el}}=P_{\mathrm{el}}(p_{\mathrm{req}})-P_{\mathrm{el}}(p_{\mathrm{del}})',
        'Transport power is the extra electricity rate over direct compression to delivery pressure with identical suction, flow and efficiency assumptions.', 'h2web/calculations.py', 'S22'),
    'cooler': (r'\begin{gathered}h_2=h_1+\frac{h_{2s}-h_1}{\eta_{\mathrm{is}}},\\Q_{\mathrm{cool}}=\dot m[h_2-h(p_2,T_{\mathrm{in}})]\end{gathered}',
        'Aftercooling returns the gas to pipeline inlet temperature. Positive duty means heat removed; negative duty means heating is required.', 'compression.py', 'S23'),
}

NOMENCLATURE = {
    'Geometry and flow': [
        (r'x,\ L','Axial distance; total pipe length',r'\mathrm m'),
        (r'D,\ r_i,\ r_o,\ t_w','Bore diameter; inner/outer radii; wall thickness',r'\mathrm m'),
        (r'H_b','Ground surface to pipe centreline burial depth',r'\mathrm m'),
        (r'A','Bore cross-sectional area',r'\mathrm{m^2}'),
        (r'\dot m','Hydrogen mass flow rate',r'\mathrm{kg\,s^{-1}}'),
        (r'G','Mass flux',r'\mathrm{kg\,m^{-2}\,s^{-1}}'),
        (r'u,\ a','Mean axial velocity; sound speed',r'\mathrm{m\,s^{-1}}'),
        (r'p,\ \Delta p','Absolute pressure; inlet-minus-outlet pressure drop',r'\mathrm{Pa}'),
        (r'p_{\mathrm{in}},p_{\mathrm{req}},p_{\mathrm{del}}','Prescribed inlet; required inlet; target delivery pressure',r'\mathrm{Pa}'),
        (r'T,T_{\mathrm{in}},T_\infty','Gas; inlet; prescribed surrounding-soil temperature',r'\mathrm K'),
        (r'\epsilon','Equivalent sand-grain internal roughness',r'\mathrm m'),
        (r'f_D,\ f_s','Darcy wall-friction factor; separate smooth-film factor',r'1'),
        (r'F','Positive wall-friction pressure loss per length',r'\mathrm{Pa\,m^{-1}}'),
        (r'\mathrm{Re},\mathrm{Pr},\mathrm{Nu},M','Reynolds, Prandtl, Nusselt and Mach numbers',r'1'),
    ],
    'Properties and heat transfer': [
        (r'\rho','Gas density',r'\mathrm{kg\,m^{-3}}'),
        (r'h,\ H','Specific static and total enthalpy',r'\mathrm{J\,kg^{-1}}'),
        (r'c_p,\ c_{p,\mathrm{tr}}','Thermodynamic heat capacity; HEOS heat capacity for transport',r'\mathrm{J\,kg^{-1}\,K^{-1}}'),
        (r'R','Specific gas constant: library gas constant divided by molar mass',r'\mathrm{J\,kg^{-1}\,K^{-1}}'),
        (r'Z','Compressibility factor',r'1'),
        (r'\mu','Dynamic viscosity',r'\mathrm{Pa\,s}'),
        (r'k_g,\ k_w,\ k_s','Gas, steel-wall and soil thermal conductivities',r'\mathrm{W\,m^{-1}\,K^{-1}}'),
        (r'h_i','Internal film coefficient; not specific enthalpy',r'\mathrm{W\,m^{-2}\,K^{-1}}'),
        (r'\mathcal R','Total thermal resistance on a per-length basis',r'\mathrm{K\,m\,W^{-1}}'),
        (r'q_{\mathrm{ground}}^{\prime},q_{\mathrm{used}}^{\prime},q_{\mathrm{th}}^{\prime}','Environmental, energy-balance and thermostat heat rates per length; positive into gas',r'\mathrm{W\,m^{-1}}'),
        (r'Q_j','Integrated heat rate; j identifies used, ground or th',r'\mathrm W'),
        (r'\rho_p','Density derivative with pressure at fixed temperature',r'\mathrm{kg\,m^{-3}\,Pa^{-1}}'),
        (r'\rho_T','Density derivative with temperature at fixed pressure',r'\mathrm{kg\,m^{-3}\,K^{-1}}'),
        (r'h_p','Enthalpy derivative with pressure at fixed temperature',r'\mathrm{J\,kg^{-1}\,Pa^{-1}}'),
        (r'\tau','Inverse reduced temperature',r'1'),
        (r'T_c','Hydrogen critical/reference temperature',r'\mathrm K'),
        (r'\alpha^0','Dimensionless ideal Helmholtz contribution',r'1'),
        (r'\alpha^0_\tau,\alpha^0_{\tau\tau}','First/second partial derivatives with inverse reduced temperature',r'1'),
        (r'n','Dittus–Boelter exponent: 0.4 for heating, 0.3 otherwise',r'1'),
    ],
    'Diagnostics and compression': [
        (r'y_p,\ y_T','Pressure and temperature normalized by inlet values',r'1'),
        (r'r_p','Signed integral momentum residual',r'\mathrm{Pa}'),
        (r'r_h,\ S_h','Signed specific-energy residual; its normalization scale',r'\mathrm{J\,kg^{-1}}'),
        (r'e_p,e_h,e_{\mathrm{mass}}','Absolute normalized momentum, energy and mass-consistency residuals',r'1'),
        (r'p_1,\ p_2','Compressor suction and discharge pressures',r'\mathrm{Pa}'),
        (r'T_1','Compressor suction temperature',r'\mathrm K'),
        (r's,\ s_1','Specific entropy; entropy at suction',r'\mathrm{J\,kg^{-1}\,K^{-1}}'),
        (r'h_1,h_{2s},h_2','Suction, isentropic discharge and actual discharge enthalpies',r'\mathrm{J\,kg^{-1}}'),
        (r'\eta_{\mathrm{is}},\eta_m','Isentropic and motor efficiencies',r'1'),
        (r'P_{\mathrm{el}},\Delta P_{\mathrm{el}}','Total and incremental electrical powers',r'\mathrm W'),
        (r'Q_{\mathrm{cool}}','Aftercooler heat rate, positive when removed',r'\mathrm W'),
    ],
}

def _eq(*keys):
    for key in keys:
        latex, meaning, _, _ = EQUATIONS[key]
        st.latex(latex)
        st.markdown(meaning)

def show_methodology():
    st.subheader('Scientific methodology and limitations')
    st.write('Follow the physical model, conservation laws and numerical checks below. Equations describe the released solver. All symbols are defined in the expandable nomenclature. Pressures are absolute; calculations use SI units.')
    st.caption('A prime on heat rate means per unit pipe length, not differentiation. Open only the sections you need. Wide mathematics and tables scroll within their containers on small screens.')

    with st.expander('Physical model — assumptions and M1–M4',expanded=True):
        st.write('The model follows cross-section-averaged hydrogen pressure and temperature along one horizontal pipe of constant bore. Flow is steady, single phase and pure normal hydrogen, with a prescribed positive mass flow. Wall friction and environmental heat exchange are included.')
        st.markdown('''| Model | Thermodynamics | Temperature treatment |
|---|---|---|
| **M1** | Ideal density and ideal Helmholtz enthalpy | Imposed inlet temperature throughout; required heat inferred |
| **M2** | Real-gas HEOS properties | Imposed inlet temperature throughout; required heat inferred |
| **M3** | Ideal density and ideal Helmholtz enthalpy | Temperature solved with pressure and environmental heat |
| **M4** | Real-gas HEOS properties | Temperature solved with pressure and environmental heat |''')
        st.write('All four use HEOS viscosity, gas conductivity and transport heat capacity at the local state. M1/M3 change thermodynamics but do not represent a fully dilute-gas transport model. Acceleration and kinetic energy are enabled together by default and omitted together when switched off. M4 is the most complete of these four formulations, not experimentally validated truth.')
        st.write('The interface includes no elevation change, gas transients, species mixing, phase change, leaks, network, local fitting losses or resolved 3D turbulence. Wall/soil heat transfer is a steady resistance approximation, with no axial solid conduction or soil heat storage. Compressor work is calculated separately from the pipeline balance.')

    with st.expander('Geometry and boundary conditions'):
        st.image(str(Path(__file__).resolve().parents[1]/'assets/geometry.png'),width='stretch')
        st.caption('Original notation-audited geometry, unchanged and not to scale. Outward heat arrows illustrate warmer gas: environmental heat into gas is negative. Heat reverses when the surroundings are warmer. Use fullscreen to inspect small labels.')
        _eq('geometry','forward','inverse')
        st.write('A forward run does not additionally prescribe outlet pressure. Isothermal models impose inlet temperature along the whole pipe; coupled models use inlet temperature as the thermal boundary. No axial temperature-gradient boundary is imposed. Soil temperature and wall/soil conductivities are prescribed constants, with homogeneous soil.')
        st.markdown('''| Representative input | Retained 50 km example (SI) |
|---|---|
| Length; bore; wall thickness | 50,000 m; 0.500 m; 0.012 m |
| Centreline burial; roughness | 1.5 m; 0.000020 m |
| Inlet pressure; mass flow | 8,000,000 Pa; 6 kg/s |
| Inlet; soil temperature | 313.15 K; 283.15 K |
| Steel; soil conductivity | 45; 1.5 W/(m K) |
| Delivery target (inverse only) | 7,000,000 Pa |''')
        st.write('The finite-element solid-conduction benchmark shown under the diagram is a separate verification component. It is not coupled to the gas ODE and supplies no transient soil field or time step to this web simulation.')

    with st.expander('Conservation — mass, momentum and total energy'):
        _eq('mass','area','momentum','loss','drop','energy')
        st.write('Enthalpy already includes pressure work. Wall friction dissipates mechanical energy internally; adding an extra Darcy heating source to total energy would double-count it. Disabling acceleration removes the velocity-derivative momentum term and kinetic energy together.')

    with st.expander('Hydrogen properties — real and ideal thermodynamics'):
        st.markdown('Real modes call CoolProp **HEOS::Hydrogen** for normal-hydrogen density, enthalpy, heat capacity, derivatives and sound speed. The real EOS is delegated to this library, not reimplemented in the interface. See the [official hydrogen property documentation](https://coolprop.org/fluid_properties/fluids/Hydrogen.html).')
        _eq('real','rho_derivatives','h_derivatives','identity','ideal','ideal_h','ideal_d')
        st.markdown(r'Superscript $0$ identifies the ideal Helmholtz part, not a power. The $\tau$ subscripts denote partial derivatives with the other reduced coordinate fixed. Transport heat capacity $c_{p,\mathrm{tr}}$ always comes from HEOS and is used in Prandtl number; the selected branch’s $c_p$ is used in gas energy.')

    with st.expander('Darcy friction — implemented closures'):
        _eq('re','colebrook','haaland','laminar')
        st.write('Colebrook uses Newton iteration in the reciprocal square root of the Darcy factor, starting from Haaland, with at most 25 iterations and step threshold 10⁻¹². Darcy is four times Fanning; a Fanning factor is never inserted into the production momentum equation. Relative roughness must be between 0 and 0.05.')

    with st.expander('Heat exchange — gas film, steel wall and soil'):
        _eq('heat','resistance','film','smooth','gnielinski','db','laminar_heat')
        st.write('Wall resistance and the smooth-film factor use natural logarithms; friction equations explicitly use base-10 logarithms. The soil term uses inverse hyperbolic cosine. Research-only resistance and Nusselt multipliers remain unity in the public API. Radiation, weather, moisture migration and time-dependent soil storage are absent.')

    with st.expander('Gas ODE — coupled and isothermal modes'):
        _eq('ode_p','ode_T','coupled_heat','iso','iso_heat','thermostat','Q')
        st.markdown(r'These differential equations retain acceleration. Switching it off sets every $u^2$ contribution in these rows to zero but retains $h_p$. “Adiabatic environment” sets $q_{\mathrm{ground}}^{\prime}=0$ and bypasses the film correlation. A coupled adiabatic run conserves total enthalpy; an imposed-isothermal run may still require a thermostat.')
        st.write('Cooling can increase density while pressure falls, so velocity need not always increase downstream. Real-gas pressure–enthalpy effects can oppose environmental cooling. These effects depend on state and boundary conditions; a small outlet-temperature difference alone does not establish a small pressure-drop difference.')

    with st.expander('Numerical method, tolerances and conservation checks'):
        _eq('scaled')
        st.markdown(r'SciPy **DOP853** integrates in axial distance with adaptive eighth-order Runge–Kutta stepping and dense output. Defaults are relative tolerance $2\times10^{-8}$ and absolute tolerance $2\times10^{-11}$ on normalized states, with maximum axial step $L/40$. These are local error controls, not guaranteed global error bounds in Pa or K.')
        st.write('Forward and comparison results use 801 uniformly spaced audit samples of the adaptive solution. These are output/quadrature points, not a gas mesh. There is no physical gas time step. The delivery inverse uses 51 audit points in trial forwards and 201 for the final audit. The separate solid benchmark uses a finite-element spatial mesh and backward-Euler time steps, not this gas integration.')
        st.write('The inverse search requires two successful forward solutions that bracket the target and checks increasing outlet pressure as inlet pressure increases. Brent’s method then uses absolute tolerance 0.02 Pa and relative tolerance 2×10⁻¹⁰, with an upper search pressure of 30 MPa. Failed trials receive no artificial outlets. Failure to find a bracket is not a theorem of global physical infeasibility.')
        _eq('rp','H','rh','ep','eh','em')
        st.markdown(r'Simpson quadrature evaluates the integral terms on the audit grid, so diagnostics depend on quadrature resolution. Disabling acceleration removes $G[u(L)-u(0)]$ from the momentum audit and uses $H=h$ in energy. Residuals are reported rather than applied as universal acceptance bounds to every user case.')
        st.markdown(r'Retained baseline tests refine all four modes to relative tolerance $2\times10^{-10}$ and maximum step $L/100$, retaining 801 audit points. They require outlet changes below 0.1 Pa and $10^{-5}$ K, mass consistency below $10^{-14}$, relative momentum residual below $10^{-7}$ and relative energy residual below $10^{-6}$. These are criteria for specified tests, not universal accuracy guarantees.')

    with st.expander('Optional compression — electrical power and aftercooling'):
        _eq('compression','increment','cooler')
        st.markdown(r'Compressor discharge pressure $p_2$ equals required pipeline inlet pressure $p_{\mathrm{req}}$ in delivery mode. The reference example uses 2 MPa/298.15 K suction, isentropic efficiency 0.75 and motor efficiency 0.95, with aftercooling to pipeline inlet temperature. Compression always uses real HEOS hydrogen, including when the pipeline uses an ideal mode.')
        st.write('These are power rates in W (displayed as kW/MW), not energy in kWh/MWh or equipment ratings. The single-stage thermodynamic calculation has no compressor map, optimized staging, equipment selection or cooler electricity. It does not directly convert pipeline friction into electrical power.')
        st.write('The compressor requires discharge pressure at least equal to suction and no greater than 30 MPa, positive flow and efficiencies in (0, 1]. The public interface accepts suction and aftercooler temperatures within 200–500 K. Computed discharge temperatures above 1000 K are rejected. These are adopted calculation limits, not equipment ratings.')

    with st.expander('Admissibility and public-service limits'):
        _eq('mach')
        st.write('Successful pipeline states stay at 200–500 K, above the configured minimum pressure (0.1 MPa by default), and at or below 30 MPa. The property routine allows a 0.05 MPa internal trial-state buffer, which does not lower the successful-trajectory limit. Mach remains below 0.8. These are adopted software restrictions, not calibrated safety ranges.')
        st.markdown(r'The determinant of the coupled coefficient matrix, divided by thermodynamic heat capacity $c_p$, must exceed 0.02. Isothermal calls also guard $1-u^2\rho_p$ locally above 0.02, with a terminal event at 0.05. Pressure/Mach events terminate integration. Failed, event-terminated or incomplete trajectories are rejected; a trial-stage closure failure can occur before event localization.')
        st.markdown('''| Heat-transfer branch | Implemented range |
|---|---|
| Laminar | Re < 2300; Nu = 3.66 |
| Transition | 2300 ≤ Re < 4000 rejected |
| Gnielinski | 4000 ≤ Re ≤ 5×10⁶; 0.5 ≤ Pr ≤ 2000 |
| Dittus–Boelter | 10⁴ ≤ Re ≤ 5×10⁶; 0.6 ≤ Pr ≤ 160 |''')
        st.write('Thermal-correlation checks are bypassed only when environmental heat is disabled; friction checks remain active. The interface also bounds inputs, spaces requests, admits one job per server process and uses 35/75/90-second forward/comparison/inverse time limits. A busy or timed-out service is not a physical infeasibility conclusion.')

    with st.expander('Numerical verification versus experimental validation'):
        st.markdown('''| Existing check | What it establishes |
|---|---|
| Ideal-isothermal analytical pressure limit | Numerical agreement under specified limiting assumptions |
| Separately formulated conservative midpoint solver | Algorithm agreement with shared HEOS and closures |
| Matched pandapipes hydraulics | Agreement in a constrained ideal hydraulic case; not an accuracy ranking |
| Property identities and compressor work integration | Thermodynamic/internal consistency |
| Tolerance refinement and integral balances | Numerical sensitivity and accounting in tested cases |
| Separate solid-conduction FEM benchmarks | Spatial/time discretisation checks for that component only |''')
        st.write('Numerical verification asks whether the stated mathematical model is implemented and solved consistently. Experimental validation asks whether predictions agree sufficiently with independent measurements for a specified use and uncertainty. Agreement between calculations sharing constitutive assumptions is not experimental evidence.')
        st.write('Full-scale experimental hydrogen-pipeline accuracy has not been established. Laboratory-loop discrepancies remain partly unresolved, with incomplete thermal boundaries and metrology. Their attribution is unresolved; those audits did not demonstrate a production-equation defect. Small residuals, a working website or agreement with another code do not remove these limitations.')
        st.markdown('See the [scientific provenance](https://github.com/dimitrispasias57-eng/H2PipeBench/blob/main/docs/SCIENCE.md) and [methodology audit](https://github.com/dimitrispasias57-eng/H2PipeBench/blob/main/docs/METHODOLOGY_AUDIT.md). The notation-audited technical supplement remains the detailed project derivation and is unchanged by this revision.')

    with st.expander('Nomenclature — Symbols and Units'):
        st.write('A unit of 1 means dimensionless. These definitions cover the geometry, equations and discussion.')
        for group, rows in NOMENCLATURE.items():
            st.markdown('**'+group+'**')
            st.markdown('| Symbol | Meaning | SI unit |\n|---|---|---|\n'+'\n'.join(
                f'| ${symbol}$ | {meaning} | ${unit}$ |' for symbol,meaning,unit in rows))
        st.markdown(r'''**Subscripts, superscripts and operators**

- $\mathrm{in}$: inlet; $\mathrm{del}$: delivery target; $\mathrm{req}$: required inlet.
- $i,o$: inner/outer radii; $b$: centreline burial; $w,s,g$: wall, soil and gas conductivities. In $f_s$, the $s$ means smooth-film factor, not soil.
- $\infty$: prescribed surroundings; $\mathrm{ground}$: environmental heat; $\mathrm{used}$: energy-balance heat; $\mathrm{th}$: thermostat. $j$ selects these heat terms.
- $\mathrm{id}$: ideal thermodynamics; $\mathrm{tr}$: transport heat capacity; $c$ in $T_c$: critical/reference temperature. $D$ in $f_D$ denotes the Darcy convention.
- $p,T$ on property derivatives identify the differentiated variable; subscripts outside derivative brackets identify what is held fixed.
- Superscript $0$ on $\alpha^0$ denotes the ideal contribution, not a power. Subscripts $\tau,\tau\tau$ denote first and second partial derivatives. Ideal subscripts apply to density, enthalpy, heat capacity and their derivatives with the same units as their unlabelled counterparts.
- $1,2,2s$: compressor suction, actual discharge and isentropic discharge; $\mathrm{is}$: isentropic; $m$ in $\eta_m$: motor; $\mathrm{el}$: electrical; $\mathrm{cool}$: aftercooler. The symbol $s$ alone means specific entropy.
- The dot on $\dot m$ denotes a rate; the prime on $q^\prime$ denotes heat per length. Powers such as $u^2$ are ordinary powers. $\Delta$ denotes the stated difference; $d/dx$ denotes an axial derivative and $\partial$ a partial derivative.
- $\pi$ is the circle constant. $\ln$ is natural logarithm; $\log_{10}$ is base-10 logarithm; $\operatorname{acosh}$ is inverse hyperbolic cosine. Absolute-value bars, integration and maximum operators have their usual meanings; $\max_x$ in mass consistency is evaluated on audit samples.
- Residual subscripts $p,h,\mathrm{mass}$ identify momentum/pressure, specific total-energy and mass consistency. $S_h$ is an energy scale; $y_p,y_T$ are normalized states, not derivatives. $H$ is specific total enthalpy, whereas $H_b$ is burial depth. $h_i$ is a film coefficient, whereas $h$ is specific enthalpy.''')

    st.warning('Research and educational use only. H2PipeBench predictions are not certified for industrial pipeline design, safety assessments, equipment selection or regulatory compliance. No structural, embrittlement, material-compatibility or equipment-rating conclusion is supported.')
