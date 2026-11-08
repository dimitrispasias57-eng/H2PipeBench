# Changelog

## 0.1.0 — 8 November 2026

First official, non-prerelease GitHub distribution of H2PipeBench under MIT.
Package and web interface versions are both 0.1.0. The API is still pre-1.0
and may change; this is a research software release, not industrial certification.

Included functionality from the public application:

- Steady one-dimensional pure-hydrogen pipeline calculations using ideal/real
  gas and isothermal/coupled-energy formulations (M1–M4).
- Delivery-pressure inversion and total/incremental compressor electrical power.
- Profiles and exports in CSV, JSON, HTML, PNG and SVG.
- Audited LaTeX methodology, nomenclature, geometry and validation limitations.
- Explicit four-model comparison and 1 km length controls accepting decimals,
  including the tested 12.5 km case; default length remains 50 km.
- Scientific regression, conservation, convergence, API, Streamlit interface and
  release-integrity tests with Windows/Ubuntu CI.

Compared with public commit d932671900b62d87db8082e49a350bcd9e4173c0,
this release changes version metadata, documentation, manifests and release
checks. The only solver-source edit is `__version__`; all scientific equations,
coefficients, algorithms and retained numerical results are unchanged.

Numerical verification is not experimental validation. Published laboratory-loop
discrepancies remain unresolved, and full-scale transmission accuracy has not
been established experimentally. No Zenodo archive or DOI is created by this release.
