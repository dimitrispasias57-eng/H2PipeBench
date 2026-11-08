# Executed verification and deployment checks

Date: 7 November 2026. Environment: a new Windows x86-64 virtual environment,
CPython 3.12.14. Installation used this distribution's requirements-dev.txt.
The Python process and dependencies were separate from the research environment.

The initial complete test run passed **87 tests**. `pip check` reported no
broken requirements. The scientific source hash check includes every one of
the 14 packaged Python files. Additional release sealing repeats the suite
after any app changes; the owner review record identifies the final run.

| Check | Executed evidence |
|---|---|
| Retained solver regression tests | Analytical isothermal limit, thermodynamic derivatives, conservation, convergence, compressor/inverse checks, invalid domains and separate solid-conduction verification |
| Forward example A | Every numeric profile column compared with the retained 801-point CSV; relative tolerance 2e-9, absolute 1e-7 for this regression comparison |
| Comparison example B | Four formulations compared with retained 100 km, 300 mm, 3 kg/s, 12 MPa, 333.15 K output |
| Inverse/compressor example A | Required inlet, total and incremental power agree with retained values; delivery residual below 0.1 Pa |
| Interface conversions | All geometry, operating, thermal and option fields reach the public API in their stated units |
| Alternatives and invalid cases | Haaland, Dittus–Boelter, acceleration omission and adiabatic switches executed; invalid geometry, nonfinite values and unsupported trajectories rejected |
| Downloads | CSV/JSON values and chart arrays checked against the result snapshot; PNG signature and SVG generated; HTML includes assumptions and units |
| Execution safeguards | Busy admission, request spacing, worker-start failure and real subprocess timeout exercised |
| Streamlit AppTest | Actual forward, comparison and compressor calculations; temperature conversion, figure generation, invalidation and information pages |
| Browser | Actual local server, forward/comparison/compressor forms, invalid geometry and CSV download event observed; desktop and mobile layouts visually inspected |

Reference example A uses 50 km, 500 mm bore, 6 kg/s, 8 MPa inlet, 313.15 K
inlet and 283.15 K soil. For M4:

- Outlet pressure: 7.912069162500649 MPa.
- Outlet temperature: 286.4202708684077 K.
- Pressure drop: 87.93083749935124 kPa.
- Required inlet for a 7 MPa delivery target: 7.098694836959345 MPa.
- Total compressor electrical power: 16.147617980053604 MW.
- Incremental transport electrical power: 214.48947956208698 kW.

The pressure figures represent absolute pressure. These are regression
references, not measured accuracy claims. Browser metrics intentionally round
for readability; exports retain the returned values. The energy residual is
a numerical integral balance, not a validation confidence interval.

Responsive checks include a 1440-pixel desktop, a 768-pixel tablet and a
390-pixel mobile viewport. The tablet geometry and equation renderer were
inspected, with no reported mathematical rendering errors.
The mobile page has no document-level horizontal overflow; large numerical
tables scroll within their container. Four-model legends remain legible.
These are browser viewport checks, not tests on physical phones or all browsers.

## Reproduce

From the repository root, install requirements-dev.txt in Python 3.12, then run:

```console
python -m pip check
python -m pytest -q
python -m streamlit run app.py
```

## Public deployment checks: 7 November 2026

Source commit `c7db556f183111d836876b30e30715a975caeeda` passed the complete
87-test suite on both GitHub-hosted Ubuntu (Python 3.12.16, 26.84 s) and Windows
(Python 3.12.10, 16.44 s), including installation and `pip check`.
[Executed CI logs](https://github.com/dimitrispasias57-eng/H2PipeBench/actions/runs/42388470631).

The deployed app is https://h2pipebench.streamlit.app/. Community Cloud was
configured for Python 3.12, main branch, app.py and no secrets. The real default
calculation returned the exact reference outlet pressure and temperature above.
A fresh HTTP/WebSocket client, supplied with no account credentials or browser
cookies, executed the default calculation and retrieved CSV, JSON, HTML, PNG
and SVG exports. Its 801-point CSV matched every one of the 21 numeric reference
columns with rtol=2e-9, atol=1e-7. PNG and SVG payload formats were checked.
The fresh-client test is distinct from the signed-in browser UI inspection.

The deployed browser UI completed M1–M4 comparison and the 7 MPa delivery
calculation (7.098695 MPa required inlet, 16.147618 MW total power,
214.489 kW incremental power). An invalid 0.02 m burial depth produced the
explicit outside-radius error and removed stale results. Layouts were visually
inspected at 1440×1100, 768×1024 and 390×844. These are viewport checks,
not tests on physical phones. The sharing dialog showed public access enabled.

The browser automation did not report a cloud PNG download event within its
timeout; direct unauthenticated retrieval of the generated PNG and SVG succeeded,
and the PNG was visually inspected. This separates browser-event instrumentation
from actual export availability. No signed-out browser profile was created;
anonymous execution was tested using the independent fresh protocol client above.

The live service rejected an overlapping calculation with its intended busy
message. This verifies admission behaviour for that test, not load capacity.
Full-scale experimental accuracy remains unestablished independently of these
installation, browser and regression checks.

## Methodology interface revision: 0.1.0rc1-web2

The local Windows suite passed **87 tests in 15.69 s** after the methodology
and model-selector revisions. The updated AppTest checks the explicit
"All four models (M1–M4)" comparison selector, runs all four formulations,
confirms single-model selection still works, and checks that all 45 equation
records are displayed exactly once without escaped control characters.
Scientific regression tests and stored reference data are unchanged.

Browser inspection at 1440×1100, 768×1024 and 390×844 found all **45 display
equations and 203 total mathematical elements** rendered, with zero KaTeX
errors. All 12 method expanders were opened for this check. Document and main
container horizontal overflow were zero at each size. The two widest display
equations and some nomenclature tables scroll internally on mobile, rather
than being scaled to illegible text or extending the page. The equations,
subscripts, Greek symbols, signs, brackets, primes and all nomenclature rows
were visually reviewed on desktop, with geometry/ODE views checked on tablet
and heat-transfer/nomenclature views checked on mobile. Small diagram labels
can be inspected using the existing fullscreen control; the geometry asset
has not been changed.

These are emulated browser viewport checks, not tests on physical devices or
all browser engines. UI documentation is not experimental validation. See the
[source mapping and dimensional audit](METHODOLOGY_AUDIT.md).
GitHub Actions records Linux and Windows results for each published commit;
the local visual check alone does not establish public deployment success.

## Decimal pipeline length: 0.1.0rc1-web3

On 8 November 2026, the Windows suite passed **90 tests in 23.41 s**.
The three added AppTest cases submit 12.5 km separately through Simulator,
Model comparison and Compression. They check the shared 1 km spinner step,
decimal acceptance, 50 km initial default and unchanged 0.01–200 km limits.
These are the existing interface bounds, not a newly validated physical range.

Each returned model records length_m = 12,500 and ends at x_m = 12,500.
Every numeric CSV profile column matches the completed result snapshot,
including final pressure and temperature. Simulator and comparison M4 outputs
also match a direct public solver API call with length_m = 12,500. Compression
reaches the unchanged 7 MPa delivery target to within 0.1 Pa for this test case.

The control sets physical length; it does not set an integration step.
The unchanged maximum-step rule remains L/40 (312.5 m for this 12.5 km case),
and the relative tolerance remains 2e-8. No integration setting, scientific
equation, historical output, benchmark or manuscript was modified.
The CSV is generated through the existing export function without rounding
the physical length to the spinner increment.

## First tagged release: 0.1.0

The 0.1.0 release retains the 90 scientific, API and web tests above and adds
two release-integrity checks: installed package/web/metadata agreement, and
exact inheritance of the scientific source apart from its version string.
The release notes record the final commit's executed Windows/Ubuntu results
and fresh public-app smoke check. Release status does not change any physical
validation claim. Older sections and dependency inventories retain their
original dates and version labels as historical evidence.
