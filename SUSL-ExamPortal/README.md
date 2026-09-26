# ExamPortal — Sabaragamuwa University of Sri Lanka

Integrated Online Examination Management System: one sign-in page that routes to the
**Administrator**, **Lecturer** and **Student** portals, all backed by real Flask APIs
sharing the SUSL emblem, colours and session handling.

## Run it

Requires Python 3.9+ (get it from https://www.python.org/downloads — on Windows, tick "Add
python.exe to PATH" during setup). Nothing else to install by hand: both backends depend on
Flask only, and the launcher below installs it the first time it runs.

```bash
./start.sh          # macOS / Linux          (Windows: double-click start.bat)
```

The launcher checks for Python, installs Flask if it's missing, starts **both** backend APIs
(Core API on port 5000, Lecturer API on port 5001), and opens http://localhost:8000 in your
browser automatically. Leave its window (and the two API windows it opens on Windows) running
while you use the app; closing it stops everything.

You can also double-click **`index.html`** in the project root (never open a folder such as
`admin/` — a folder link only shows a file list). Chrome and Edge handle this fine; Firefox may
not keep the session between pages when opened from disk, so prefer `start.sh` / `start.bat`
there.

| Role | Sign in with | Authenticated by |
|------|--------------|------------------|
| Administrator | `admin@sab.ac.lk` / `Admin@SUSL2026` | **Flask API** on port 5000 (`backend/core-api`) |
| Lecturer | `davis@susl.ac.lk` / `password123` | **Flask API** on port 5001 (`backend/lecturer-api`) |
| Student | "Continue to Student Portal" → Register, or sign in as the seeded demo student below | **Flask API** on port 5000 (`backend/core-api`) |
| Student (seeded demo account) | `nimasha.perera@std.sab.ac.lk` / `Student@2026`, Student ID `22APP5678` | same |

The Student portal loads Bootstrap, Font Awesome and Google Fonts from CDNs, so it needs internet
access even though its data now comes from the local backend.

Both backends auto-create and seed their own SQLite database (`exam_portal.db`, one file per
backend folder) the first time they run — nothing to configure. Delete a database file and
restart that backend to reset it back to the seeded demo data.

## Layout

```
index.html              unified sign-in (role cards → routes to a portal)
assets/                 susl-logo.png · config.js (API URLs) · session.js (guards, sign-out) · login.css/js
admin/                  Administrator portal   — talks to backend/core-api  (/api/admin/*)
lecturer/               Lecturer portal        — talks to backend/lecturer-api
student/                Student portal         — talks to backend/core-api  (/api/auth/*, /api/student/*)
backend/core-api        Flask + SQLite API for the Admin and Student modules (port 5000)
backend/lecturer-api    Flask + SQLite API for the Lecturer module (port 5001)
_archive/               earlier drafts and team files kept for reference (not used by the app)
```

Change either API's address in one place: `assets/config.js` (`CORE_API`, `LECTURER_API`).

## What's integrated now

**Backend (new)**
- `backend/core-api` is a new, complete Flask + sqlite3 backend (zero dependencies beyond
  Flask, same as `lecturer-api`) covering the **Admin** and **Student** modules, which
  previously had no backend, or an unconnected one.
- Auth is shared between Admin and Student: register, email-confirmation, login, and a full
  forgot-password → OTP → reset flow. No mail server is configured in this project, so codes are
  logged to the backend's console **and** returned to the caller as `devCode`/`resetToken` so the
  demo works end-to-end without one — see "Before real use" below.
- Student: profile, subject catalogue + enroll/unenroll, exam listing, a real gradable exam
  (server-side marking — the browser never sees the correct answers), official result sheets and
  the handbook's real GPA/FGPA formula.
- Admin: dashboard stats, exams, students, lecturers, question bank and results are all real,
  persisted records with full CRUD, replacing the old localStorage sample data.
- **The one place Admin and Student meet:** publishing a result set in the Admin portal also
  publishes the matching `course_results` rows for the same subject, so a student's "My Results"
  page and GPA update the moment an admin publishes — try it: publish "Database Management
  Systems" as the admin, then check the demo student's results.
- A student an admin creates (with the temporary password shown in the Students page's tooltip —
  `Student@123`) is a real account that can log in immediately and reset its own password.

**Backend (fixed)**
- `backend/lecturer-api` no longer logs plaintext passwords on login, no longer exposes the
  `/debug-auth` header-echo route, CORS is now restricted via a `CORS_ORIGINS` env var (defaults
  to `*` for local development), and it now warns on startup if `EXAM_PORTAL_SECRET` is left at
  its default.

**Frontend (fixed/wired)**
- Admin sign-in on the shared login page now calls the real API instead of checking a hardcoded
  password in JavaScript.
- `admin/script.js` was rewritten end-to-end: every add/edit/delete/suspend/publish/settings
  action is now a real API call; the dashboard, tables and activity feed all load real data on
  open.
- The Student portal's register / email-verify / login / forgot-password / OTP / reset-password
  flow now calls the real backend instead of a client-side mock store.
- Taking the seeded "Mid-Semester Examination" (AI & Expert Systems) now fetches real questions,
  autosaves each answer to the server, and is marked server-side on submit. Any other exam on the
  Student dashboard is demo data the backend doesn't model yet (see below) and still uses the
  original front-end simulation so the rest of the portal keeps working.
- Sign-out clears the Admin/Student API token as well as the session.

## Before real use — known limitations

1. **No email provider is configured.** Registration and password-reset codes are printed to
   each backend's console and also returned in the API response (`devCode` / the OTP shown on
   the Student portal's confirm-code screen). Wire a real provider (Flask-Mail, SES, etc.) and
   remove `devCode` from every response in `backend/core-api/api/auth.py` before real use.
2. **Not everything on the Student dashboard is backed by a database table.** Assignments,
   timetable and notifications were never modelled in this project's database design (only
   auth, subjects, exams/questions/results were), so those three pages still show the original
   front-end sample data. The Subjects/Enroll page and its multi-programme curriculum browser
   are also still the original static reference data — only the one seeded exam and the seeded
   published results are live, database-backed data end to end.
3. **Two separate "lecturer" records.** The Admin portal's Lecturers page manages a roster of
   `role="lecturer"` rows in `backend/core-api`'s own database, for admin reporting — it does
   **not** create a login for `backend/lecturer-api`, which has its own separate database and
   accounts. Keep this in mind if you add a lecturer as admin and expect them to be able to sign
   into the Lecturer portal with the temporary password shown; they can't, yet.
4. **Default secrets.** Both backends fall back to an insecure default JWT-signing secret if
   `EXAM_PORTAL_SECRET` isn't set, with a startup warning either way. Set it (to the same value
   for both, if you want either backend's tokens to be verifiable in isolation — they don't need
   to match each other, since each only ever checks its own tokens) before deploying anywhere
   reachable by anyone else.
5. The unrelated `MortgageCalculator` C# project mentioned in earlier drafts of this README is
   not present in this build.
