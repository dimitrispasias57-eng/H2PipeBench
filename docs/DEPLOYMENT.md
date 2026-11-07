# GitHub and Streamlit Community Cloud deployment

GitHub destination: `dimitrispasias57-eng/H2PipeBench`, separate from
`microstructai-reproducible-benchmark`. The maintainer authorised publication
on 7 November 2026. The project uses MIT with the public account handle in
the copyright notice. Public deployment was verified on that date:
https://h2pipebench.streamlit.app/. See TESTING.md for executed checks and limits.

## Release scope

The root LICENSE records the approved MIT terms. RELEASE_MANIFEST.json identifies
the distributable files. The solver equations and retained numerical references
are unchanged. Only this standalone tree belongs in the public repository.

## Deployment settings

| Setting | Value |
|---|---|
| Repository | `dimitrispasias57-eng/H2PipeBench` — new and separate from MicroStructAI |
| Hosting cost | Free GitHub public-repository hosting and free Streamlit Community Cloud only |
| Source scope | Only the reviewed app directory, never the parent research workspace |
| Visibility | Public, authorised by the maintainer |
| Branch | `main` |
| Entry point | `app.py` at repository root |
| Python | 3.12, explicitly selected in Advanced settings |
| Dependencies | Root `requirements.txt`, including the local vendored package |
| Streamlit configuration | Root `.streamlit/config.toml` |
| Secrets | None required; leave empty |
| App access | Public / anyone with the link; no visitor login |
| Subdomain | `h2pipebench.streamlit.app` — assigned and verified |

`.python-version` documents local use; Community Cloud's Python dropdown is
the deployment setting. The live deployment explicitly uses Python 3.12.

Do not modify the MicroStructAI repository or its settings. Do not enable paid
plans, trials, Codespaces, larger Actions runners, paid domains or paid hosting.
The included CI uses standard public-repository Ubuntu/Windows runners; it
does not upload artifacts or enable a dependency cache. Its public-repository
guard prevents accidentally running the workflow in a private repository.

## Deployment procedure

1. Check the release manifest, root MIT licence and unchanged solver hashes.
2. Authenticate GitHub interactively. Do not send tokens in chat or commit them.
3. From the reviewed standalone tree, initialize a local repository with
   `git init -b main`. Configure the human-approved public commit author and
   email (a GitHub no-reply address is suitable), inspect `git status`, then
   use `git add .` and `git commit -m "Prepare H2PipeBench web application"`.
   Do not inherit a private email inadvertently from a global Git setting.
   Create the approved public repository from the reviewed candidate only. A
   creation command is `gh repo create dimitrispasias57-eng/H2PipeBench
   --public --source . --remote origin --push` from the prepared local repository.
   Use this command only once. Subsequent releases update H2PipeBench, never
   the existing MicroStructAI repository.
4. Require the included GitHub Actions matrix to pass on **Ubuntu and Windows**.
   A workflow file is not an executed Linux test. Investigate any failures
   before enabling public use; preserve numerical references and source hashes.
5. Sign in to https://share.streamlit.io/ and connect the approved GitHub account
   using its normal authentication UI. Select Create app, the approved repo,
   branch `main`, and entry point `app.py`.
6. In Advanced settings choose Python **3.12** and leave secrets empty. Deploy.
7. Confirm access is public in app sharing settings. Do not distribute an
   invitation-only URL as a public app.
8. Open the actual assigned `.streamlit.app` URL, run the default M4 case and
   verify approximately 7.912069 MPa and 286.420271 K at the outlet. Compare all
   four models; test the 7 MPa delivery calculation (7.098695 MPa required inlet,
   16.147618 MW total electricity and 214.489480 kW incremental power).
9. Test invalid burial geometry, report/CSV/PNG/SVG downloads and a mobile-size
   viewport. Verify the downloaded values match the displayed completed run.
10. Repeat a real calculation in a fresh, signed-out/incognito browser session.
    A successful signed-in admin visit alone does not establish public access.
11. Record the actual URL, public repository URL, commit, runtime versions,
    test records, date, anonymous-access result and approved manifest. Only then
    describe the app as publicly deployed.

For later releases, obtain any newly necessary authentication or approval before
publishing outside the approved scope. Propose manuscript updates separately;
do not edit the research manuscripts as part of application deployment.

## Official deployment references (checked 7 November 2026)

- https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/app-settings
- https://docs.streamlit.io/deploy/streamlit-community-cloud/status
- https://docs.streamlit.io/deploy/concepts/dependencies
- https://docs.streamlit.io/deploy/streamlit-community-cloud
- https://github.com/pricing
- https://docs.github.com/en/billing/concepts/product-billing/github-actions

Community Cloud starts apps from the repository root and uses the declared
dependency files. Python 3.12 is selectable. Public GitHub repository access
and app visibility must both be checked; host availability and resource
limits remain subject to the service's current rules.
GitHub Free includes public repositories, standard public-repository Actions
runners are free, and Streamlit documents Community Cloud as free. This setup
does not change the existing account plan or enable any paid service.
