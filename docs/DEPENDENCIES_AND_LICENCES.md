# Dependency and licence review

Review date: 7 November 2026. The project's MIT terms are in the root LICENSE;
this document records separate dependency terms and verification limits.

The clean Windows/Python 3.12 environment contains 45 runtime distributions
(including H2PipeBench), plus five test dependencies. Exact installed versions,
licence metadata and notice hashes are in `dependency_inventory.json`.
`tested_windows_versions.txt` is an inventory, not a Linux lock file.
The root `constraints.txt` pins these tested runtime and test dependency
versions when they are selected by the resolver. It does not force
Windows-only dependencies to install on Linux or establish Linux compatibility.

All 49 third-party packages have retained notices: 81 notice files total.
Streamlit's installed wheel did not include a licence file in its metadata;
its Apache-2.0 text was retrieved from the official 1.67.0 source tag:
https://github.com/streamlit/streamlit/blob/1.67.0/LICENSE

The principal packages declare MIT (CoolProp, Plotly), BSD-family terms
(NumPy, SciPy, pandas), Apache-2.0 (Streamlit, PyArrow) and the Matplotlib/PSF
licence. Their bundled components can have additional notices. These notices
are retained, not replaced by the project MIT licence.

Certifi declares MPL-2.0. It is an unmodified, separately installed dependency;
its covered files are not relicensed as MIT. Mozilla explains the file-level
scope and combination with other licences in its official FAQ:
https://www.mozilla.org/en-US/MPL/2.0/FAQ/

No dependency-level incompatibility with a separately MIT-licensed application
was identified in this review. This is conditional on preserving the applicable
notices and obligations. The maintainer affirmed authority to release the
inherited solver, web code and geometry. The copyright notice identifies the
maintainer by the public GitHub handle; no legal personal or institutional
name has been inferred.

The candidate contains project source and notices, not third-party Python
binary wheels. Streamlit installation retrieves dependencies from the normal
package registry. The application itself does not modify their source files.

## Advisory checks

An OSV batch lookup queried the exact installed versions of all 49 third-party
distributions on the review date. It returned no advisory records for those
queries. This does not prove the absence of vulnerabilities, malicious changes
or undisclosed flaws. Repeat the check before publication and after upgrades.

An additional PyPI version-metadata check succeeded for 44 distributions and
was incomplete for five because their responses could not be parsed in full.
Its empty advisory lists are not a substitute for those missing responses.
The complete OSV lookup is the reported advisory result.

## Linux boundary

No working Linux, WSL, Docker or Podman environment was available on the host.
No Linux execution has been claimed. Registry metadata lists CPython 3.12
manylinux x86-64 wheels for CoolProp 8.0.0 and SciPy 1.16.3, and a universal
wheel for Streamlit 1.67.0. This demonstrates availability only; it does not
establish successful installation, shared-library loading or solver execution.

The included Ubuntu/Windows CI matrix must pass after the approved repository
is created. Community Cloud must then be checked on its actual Linux runtime,
including a real simulation, four-model comparison, compression and exports.
Do not bypass a Linux failure by silently changing the verified physics stack.
