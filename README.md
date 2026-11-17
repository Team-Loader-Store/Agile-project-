# SCRUM-246 — One-click Windows temporary public HTTPS launcher

**Status: Windows integration test pending.** This is a development/demo tunnel, not the permanent deployment described in SCRUM-139.

## Repository-specific defaults
The repo README identifies Python `server.py` and local port 8000. The launcher has been adjusted to use those settings in `launcher.config.bat`, with the assumption that the launcher files are stored under `SCRUM-246/` in the repository root.

## How to run on Windows
1. Install Python 3.8+ and ensure `python` is on PATH.
2. Install the official Cloudflare `cloudflared` CLI and ensure `cloudflared.exe` is on PATH; or place it alongside the BAT script.
3. Confirm `server.py` exists in the repository root and opens locally at `http://127.0.0.1:8000`; if different, edit `launcher.config.bat`.
4. Double-click `SCRUM-246/run-global-server.bat`.
5. Keep both the server and launcher windows open. The tunnel prints a temporary `https://...trycloudflare.com` link, which changes when restarted.
6. Test the link from another network after confirming auth and permissions.

## Security
This exposes the running application to the public Internet. **Do not use real customer data, shared default admin credentials, or a development server with privileged debugging enabled.** Protect logins and enforce rate limits before testing. Restrict access to a test environment. Never commit secret keys or production SQLite databases.

## Notes
- Does not install Cloudflare CLI automatically or provision a permanent domain.
- Starts a second command window using `python server.py` and checks local HTTP response before starting the HTTPS tunnel.
- Quitting the tunnel does not necessarily terminate the Python server window; close both.
- AC Windows runtime verification still requires a test on an actual Windows machine.
