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

## Linux execution

No suitable Linux environment was available locally. After publication, the
standard GitHub-hosted Ubuntu runner installed requirements-dev.txt, passed
`pip check`, and passed all 87 tests on Python 3.12.16. The Windows runner also
passed all 87 tests on Python 3.12.10. Evidence:
https://github.com/dimitrispasias57-eng/H2PipeBench/actions/runs/42388470631

The Streamlit Community Cloud app also executed the actual solver with
CoolProp 8.0.0, NumPy 2.5.4, SciPy 1.16.3 and pandas 2.3.3. The default run's
801-point CSV matched all 21 numeric columns of the retained reference within
rtol=2e-9 and atol=1e-7. These are execution and regression checks, not evidence
of experimental accuracy or a guarantee of compatibility with other versions.
