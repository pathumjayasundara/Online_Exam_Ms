# ExamPortal — Sabaragamuwa University of Sri Lanka

Integrated front-end for the Online Examination Management System: one sign-in page that routes to the
**Administrator**, **Lecturer** and **Student** portals, all sharing the SUSL emblem, colours and session handling.

## Run it

Requires Python 3.9+ (get it from https://www.python.org/downloads — on Windows, tick "Add python.exe to PATH" during setup). Nothing else to install by hand: the launcher below installs Flask itself the first time it runs.

```bash
./start.sh          # macOS / Linux          (Windows: double-click start.bat)
```

The launcher checks for Python, installs Flask if it's missing, starts the Lecturer API, and opens
http://localhost:8000 in your browser automatically. Leave its window (and the "Lecturer API" window
it opens on Windows) running while you use the app; closing it stops the app.
Then open **http://localhost:8000**.

You can also double-click **`index.html`** in the project root (never open a folder such as `admin/` — a
folder link only shows a file list). Chrome and Edge handle this fine; Firefox may not keep the session
between pages when opened from disk, so prefer `start.sh` / `start.bat` there.

| Role | Sign in with | Authenticated by |
|------|--------------|------------------|
| Administrator | `admin@sab.ac.lk` / `Admin@SUSL2026` | Browser only (demo — no admin backend yet) |
| Lecturer | `davis@susl.ac.lk` / `password123` | **Flask API** on port 5001 (`backend/lecturer-api`) |
| Student | "Continue to Student Portal", then Student ID + email | Student portal's own mock store (register / OTP / reset flows) |

The Student portal loads Bootstrap, Font Awesome and Google Fonts from CDNs, so it needs internet access.

## Layout

```
index.html            unified sign-in (role cards → routes to a portal)
assets/               susl-logo.png · config.js (API URL) · session.js (guards, sign-out) · login.css/js
admin/                Administrator portal        (front-end only, sample data kept in localStorage)
lecturer/             Lecturer portal             (talks to backend/lecturer-api)
student/              Student portal              (front-end only; "API HOOK" comments mark backend calls)
backend/lecturer-api  Flask + SQLite API used by the Lecturer portal
backend/student-api   Student Flask API — NOT connected to the student front-end yet
_archive/             earlier drafts and team files kept for reference (not used by the app)
```

Change the Lecturer API address in one place: `assets/config.js`.

## What was integrated

- One sign-in page; Admin and Lecturer routes are guarded (signed-out visitors are sent back to sign-in).
- Sign-out works everywhere and clears the session (and the lecturer API token).
- Lecturer sign-in on the shared page calls the real API and hands the token to the Lecturer portal, which skips its own login box.
- An expired lecturer token returns the user to sign-in instead of failing silently.
- One brand: SUSL emblem (the original student copy was a clipped low-res crop) and the maroon palette, applied to the login and admin pages, which were blue.
- Admin is now functional: validated add/edit forms, row actions (edit, delete, suspend/activate, change exam status, publish results), search and filters, CSV export/reports, persistence, responsive layout.

## Before real use — known limitations

1. **Admin sign-in is client-side only.** The admin password is visible in `assets/login.js`; treat the admin portal as a prototype until an admin API with server-side auth exists. The same applies to the Student portal's mock accounts.
2. **Admin data is sample data** stored in the browser, not a database. Dashboard totals include fixed baseline numbers.
3. **Lecturer API issues (not changed):** `backend/lecturer-api/api/auth.py` prints plaintext passwords to the console on every login; `app.py` exposes a `/debug-auth` route that echoes request headers; CORS allows any origin; and the token secret has a default value — set `EXAMPORTAL_SECRET` in production. Remove these before deployment.
4. `backend/lecturer-api/requirements.txt` was rewritten to `Flask` only (the original listed packages the code doesn't import). `backend/student-api` files were arranged into the `api/` package its `app.py` expects; it is untested.
5. The unrelated `MortgageCalculator` C# project (present in three folders of the upload) was left out.
