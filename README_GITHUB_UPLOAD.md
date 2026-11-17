# Loader Store — GitHub submission (SCRUM-243 + SCRUM-246)

Repository: https://github.com/Team-Loader-Store/Agile-project-

This bundle contains **only the newly authored task files**; it does not overwrite `server.py`, `static/index.html`, or the existing authentication code.

## Upload paths (preserve folders)
- `SCRUM-243/password_security.py`
- `SCRUM-243/tests/test_password_security.py`
- `SCRUM-243/README.md`
- `SCRUM-246/run-global-server.bat`
- `SCRUM-246/launcher.config.bat`
- `SCRUM-246/README.md`

## GitHub browser workflow
1. Open the existing `Agile-project-` repo; **do not create a new repository**.
2. Create a new branch, e.g. `feature/scrum-243-246-submission`.
3. From repo root, choose `Add file` > `Upload files` and upload the two task folders' contents, preserving the folder structure when possible. If the web UI flattens paths, use Git CLI or create the folders first.
4. Commit: `Add SCRUM-243 password-change service and SCRUM-246 Python HTTPS launcher`.
5. Open a Pull Request to `main`; request review and integrate the password service with the existing `users`, `sessions` and frontend components.

## Important completion status
- SCRUM-243: core library/unit tests are present, but user login/API/frontend integration is pending.
- SCRUM-246: BAT/config is aligned with the repo README, but the Windows/public-link acceptance test has not been run here. Requires Cloudflare CLI and secure test deployment.

Do not commit credentials, session cookies, tokens, production SQLite files, `.env`, or secret keys.
