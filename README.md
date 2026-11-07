# H2PipeBench — Hydrogen Pipeline Simulator

**[Open the public simulator](https://h2pipebench.streamlit.app/)** — free browser
access, with no visitor login or Python installation required.

A Streamlit interface to H2PipeBench 0.1.0rc1 for steady, one-dimensional,
horizontal pure-hydrogen pipeline calculations. It calls the actual package;
there is no replacement hydraulic solver in the UI. Project code and geometry
are distributed under the [MIT licence](LICENSE). Dependencies retain their
upstream terms. Source: [dimitrispasias57-eng/H2PipeBench](https://github.com/dimitrispasias57-eng/H2PipeBench).

The [initial public CI run](https://github.com/dimitrispasias57-eng/H2PipeBench/actions/runs/42388470631)
passed all **87 tests on both Ubuntu and Windows**. The live default result and
its 801-point exported profile were checked against retained references.
See [testing evidence and limits](docs/TESTING.md).

## Run locally

Use Python **3.12**. From this repository root:

```console
python -m venv .venv
```

Activate `.venv` using your operating system's normal activation command, then:

```console
python -m pip install -r requirements-dev.txt
python -m pip check
python -m pytest
python -m streamlit run app.py
```

For deployment, install `requirements.txt` only. The local package path in that
file installs `vendor/h2pipebench`; no private research directory is needed.
The included constraints pin tested transitive versions; Linux execution is
still pending and must pass the supplied CI and cloud checks.
Run all commands from this repository root. `.python-version` records the
development interpreter; explicitly select Python 3.12 in Community Cloud's
Advanced settings. No secret or environment credential is needed by the app.

## What the app does

- Simulate ideal/real gas with imposed-isothermal or coupled energy models.
- Compare all four with identical geometry and inlet conditions.
- Solve for inlet pressure at a prescribed delivery pressure and mass flow;
  calculate total and incremental compression electrical **power**.
- Inspect pressure, temperature, density, velocity, Reynolds and heat profiles.
- Download the exact displayed run as SI CSV, JSON, a standalone HTML report,
  and PNG/SVG figures. Figure preparation uses the returned data, not a new solve.
- Review equations, definitions, numerical methods and experimental limitations.

The initial configuration is retained Example A: 50 km, 500 mm inner diameter,
6 kg/s, 8 MPa absolute, 313.15 K inlet and 283.15 K soil. Results appear only
after an explicit run. The 100 km reference in the tests uses 300 mm and
3 kg/s; it is a different case. Changing form fields does not change the last
completed result. Failed requests clear the previous result; failed models
in a comparison are identified and omitted, never replaced.

## Scope and limits

**Research and educational use only.** Predictions are not certified for
industrial pipeline design, safety, equipment selection or regulatory
compliance. Numerical verification is distinct from experimental validation.
Full-scale experimental accuracy is unestablished; some laboratory comparisons
remain unresolved. The web app adds no new scientific validation.

Public-service input limits are in `h2web/inputs.py`. They do not establish
physical realism or experimentally supported ranges. The solver enforces its
own trajectory, property and correlation checks. No transient gas, mixture,
network or three-dimensional CFD feature is exposed. The diagram's separate
solid benchmark is explanatory and is not coupled into these calculations.

## Architecture and privacy

`app.py` provides forms and presentation. `h2web/inputs.py` makes explicit SI
conversions; `calculations.py` calls the package API. `service.py` admits at most
one numerical worker at a time per server process, with fixed time limits.
`worker.py` exchanges a bounded JSON request through pipes, without shell
commands or persistent user files. `exports.py` creates all charts/downloads
from the same result snapshot. CoolProp states are isolated per solve.

Only the active session's latest calculation is held in memory. There is no
result database, shared result cache, upload endpoint, account system or
application analytics. “Clear session results” discards stored results and
figure buffers. Inputs in the form remain available until the session ends.
Hosting-provider connection metadata/logging remains outside the app's control.
Do not enter confidential operating data into a public research demonstration.

## Reproduction and provenance

- `vendor/h2pipebench/src/`: unmodified release-candidate source; verify against
  `vendor/h2pipebench/SOURCE_HASHES.json`.
- `tests/solver/`: the release's existing numerical/API tests, copied unchanged.
- `tests/reference/`: three retained output files used solely as regression
  references. They are never substituted for live app results.
- `assets/geometry.*`: original project schematic copied unchanged; no journal
  article, manuscript or third-party illustration is included.
- [Deployment](docs/DEPLOYMENT.md), [release checklist](docs/RELEASE_CHECKLIST.md),
  [privacy/security](docs/SECURITY_AND_PRIVACY.md), and [scientific notes](docs/SCIENCE.md).
- [Executed testing](docs/TESTING.md) and [dependency/licence review](docs/DEPENDENCIES_AND_LICENCES.md).

The public repository contains this standalone application tree. See
RELEASE_MANIFEST.json for the payload hashes. AI assistance was used for
implementation and checks. Experimental validation limitations remain visible
independently of the software's release status.
