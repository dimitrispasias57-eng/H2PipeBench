# H2PipeBench solver payload

Version 0.1.0rc1. Distributed under the [MIT licence](LICENSE.txt).

This directory carries the unchanged 14 Python source files from the verified
H2PipeBench release candidate. SOURCE_HASHES.json records their SHA-256 hashes.
The scientific source is retained; the packaging metadata records the approved
MIT licence. This short README replaces the original
package README because this web distribution omits its standalone examples,
reports and manuscript-related release instructions.

Install and run from the [web application root](../../README.md), using its
requirements.txt. The local package is installed as a dependency; it is not
downloaded from an unverified package with the same name.

See the web distribution's [scientific methods](../../docs/SCIENCE.md),
[limitations and privacy](../../docs/SECURITY_AND_PRIVACY.md), and
[release checklist](../../docs/RELEASE_CHECKLIST.md).

The source implements steady, horizontal, one-dimensional pure-hydrogen pipe
calculations, four thermodynamic/thermal formulations, delivery-pressure
inversion and single-stage compression power. A separate solid-conduction
verification module remains in the payload but is not an app feature.

Numerical verification does not establish experimental accuracy. Published
laboratory-loop discrepancies remain unresolved; full-scale transmission
accuracy is not experimentally established. No industrial safety or equipment
rating is implied. Dependencies retain their upstream copyright and licence terms.
