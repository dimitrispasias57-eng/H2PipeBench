# Security, privacy and resource controls

The application accepts finite numeric fields and fixed enumerated options.
Requests contain a fixed schema and are independently validated before the
worker and again within it. Units are converted explicitly. The solver owns
physical admissibility; failed trajectories are never filled with approximate
answers.

- No accounts, uploads, user-supplied code, URLs, SQL or shell commands.
- No credentials or secrets required; `.streamlit/secrets.toml` and `.env` are excluded.
- No input/result persistence to disk, application logs, analytics or a database.
- Session State holds the active session's most recent result; no shared result cache.
- One worker at a time per server process; two seconds between global starts;
  five seconds between submissions in a session.
- Maximum runtime: 35 seconds forward, 75 seconds four-model comparison,
  90 seconds delivery inversion plus compression. Timed-out workers are killed
  and reaped; no partial result is returned.
- Input JSON is limited to 16 KiB and returned worker JSON to 8 MB. Profiles
  have 801 points for forward calculations and the API's 201 for inversion.
- Numeric library thread counts are one per worker to reduce oversubscription.
- Domain failures map to predefined user messages. Unexpected exceptions and
  worker stderr are not sent to users. Streamlit detailed errors are disabled.
- CORS/XSRF protection remains enabled. Streamlit usage statistics are disabled.
- Downloads contain only input snapshots, whitelisted software metadata,
  computed results, units and scientific assumptions. HTML report strings are escaped.

These are ordinary shared-resource safeguards, not a distributed rate limiter
or a defence against determined denial of service. A hosting provider may
retain connection metadata and platform logs under its own terms. There is no
claim that platform-level retention is disabled. The interface tells users not
to enter confidential operating conditions.

The dependency audit and exact publication manifest are supplied separately for
owner review. Dependency metadata and advisory scans are evidence at a point
in time, not guarantees of security or ownership. No deployment or secret
configuration is authorised by this document.
