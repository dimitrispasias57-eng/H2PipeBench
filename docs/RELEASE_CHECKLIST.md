# Release and deployment checklist

This checklist records required gates. Unchecked deployment items are not
claims of successful execution. See the actual test/audit reports supplied
with the candidate for local results and environment details.

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

- [ ] Publish only the approved source tree.
- [ ] GitHub Actions passes on Ubuntu and Windows with the exact deployed dependencies.
- [ ] Community Cloud installs CoolProp/SciPy/H2PipeBench and starts without errors.
- [ ] The real URL runs the default, comparison and compressor examples successfully.
- [ ] Unsupported cases give useful errors with no fabricated outputs or private traceback.
- [ ] Downloads match the displayed run and contain no private/session data.
- [ ] Desktop, tablet and mobile layouts are usable.
- [ ] A signed-out browser can access and run the app without login or payment.
- [ ] Record URL, repository, commit, deployed versions, date and verification evidence.
- [ ] Prepare a proposed manuscript update only after the public app passes these checks.

Do not convert numerical agreement into an experimental-validation claim.
