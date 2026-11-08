# H2PipeBench solver payload

Version 0.1.0. Distributed under the [MIT licence](LICENSE.txt).

This directory carries the 14 Python source files inherited from the verified
0.1.0rc1 solver. Only the package `__version__` string changed for 0.1.0.
All governing equations, coefficients, integration settings and algorithms
are unchanged. SOURCE_HASHES.json records both current and inherited hashes;
release tests verify that the version string is the only source difference.

Install the complete app from the [repository root](https://github.com/dimitrispasias57-eng/H2PipeBench/tree/v0.1.0),
using its requirements.txt. This local package is installed as a dependency;
it is not downloaded from an unverified package with the same name.
The public distribution omits the private research archive, manuscripts and
standalone historical reports.

The source implements steady, horizontal, one-dimensional pure-hydrogen pipe
calculations, four thermodynamic/thermal formulations, delivery-pressure
inversion and single-stage compression power. A separate solid-conduction
verification module remains in the payload but is not an app feature.

Numerical verification does not establish experimental accuracy. Published
laboratory-loop discrepancies remain unresolved; full-scale transmission
accuracy is not experimentally established. No industrial safety or equipment
rating is implied. Dependencies retain their upstream copyright and licence terms.
