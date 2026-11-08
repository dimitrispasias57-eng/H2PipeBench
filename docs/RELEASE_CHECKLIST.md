# Release and deployment checklist

Deployment verified on 7 November 2026. See TESTING.md for the exact checks,
versions and limitations, including the distinction between browser inspection
and fresh unauthenticated protocol-client testing.

## Before publication

- [x] Review the payload and produce the complete file/hash manifest.
- [x] Maintainer explicitly affirmed authority to release the inherited solver, app and geometry.
- [x] Apply MIT using the public GitHub handle in the copyright notice; no legal personal name inferred.
- [x] Update release wording and package licence metadata; preserve scientific source hashes.
- [x] Review installed dependency licences and advisory snapshot; repeat if dependencies change.
- [x] Exclude personal project paths, credentials, private emails, manuscripts and research archives. Public upstream copyright notices are retained.
- [x] Confirm all package Python source hashes match the verified release candidate.
- [x] Execute local tests and browser checks; check generated CSV/figure bytes and browser download controls.
- [x] Identify GitHub owner `dimitrispasias57-eng` from the existing MicroStructAI repository and select the separate name `H2PipeBench` as requested.
- [x] Receive explicit instruction to publish from the maintainer after the review and ownership question.
- [x] Configure free hosting only: public GitHub repository, standard public CI runners and Streamlit Community Cloud; no paid options or MicroStructAI changes.
- [x] Use Community Cloud Python 3.12, root app.py, no secrets and public access.

## After approval, before announcing a public app

- [x] Publish only the approved source tree.
- [x] GitHub Actions passes on Ubuntu and Windows with the pinned dependencies.
- [x] Community Cloud installs CoolProp/SciPy/H2PipeBench and executes the solver.
- [x] The real URL runs the default, comparison and compressor examples successfully.
- [x] Tested invalid geometry gives a useful error with no substituted result or traceback.
- [x] Actual CSV/JSON/report/PNG/SVG exports retrieved; profile values checked against references.
- [x] Desktop, tablet and mobile viewport layouts visually inspected.
- [x] Public sharing enabled; fresh unauthenticated client runs the app and downloads results.
- [x] Record URL, repository, tested source commit, deployed scientific versions and evidence.
- [x] Prepare a separate proposed manuscript update after public-app verification; manuscripts unchanged.

The anonymous-access check used a fresh HTTP/WebSocket client, not a signed-out
browser profile. The browser's cloud PNG event was not captured; its actual
generated payload was successfully retrieved separately. See TESTING.md.

Do not convert numerical agreement into an experimental-validation claim.

## Version 0.1.0 release gate

The maintainer requested the first official GitHub release on 8 November 2026.
Version metadata is aligned across package, installed distribution and web app.
Current and inherited source hashes distinguish the single version-string edit
from the unchanged scientific implementation. Numerical reference files retain
their original bytes and version labels.

Publish the tag only after the final commit passes the complete test matrix,
installation checks and public-app smoke verification. Record executed results
in the GitHub release notes. GitHub supplies ZIP and tar.gz source downloads.
Keep the existing MIT licence and free hosting. No Zenodo archive or manuscript
submission is part of this release. The 0.x API remains subject to change.
