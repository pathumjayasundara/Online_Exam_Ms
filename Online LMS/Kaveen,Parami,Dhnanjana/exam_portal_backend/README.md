# ExamPortal — Lecturer Module Backend

Flask API + SQLite database for Team 01's Lecturer Module: Question Bank
(create/edit/delete MCQs) and Create Exam (select questions, set duration).
Also includes My Subjects, View Results, and a Dashboard summary, since the
frontend prototype covers those too.

## A note on dependencies

The project guide specifies **Flask-SQLAlchemy**, **Flask-JWT-Extended**, and
**Flask-Cors**. This sandbox has no internet access, so those packages
couldn't be installed here — the app instead uses Python's built-in
`sqlite3` for the database and a small HMAC-signed token in `auth_utils.py`
in place of JWT, plus manual CORS headers in `app.py`. Functionally it's
the same shape (tables, routes, "log in and get a token" flow) — on your own
machine, once you `pip install -r requirements.txt`, swapping
`database.py`'s raw SQL for SQLAlchemy models (and `auth_utils.py` for
`flask_jwt_extended`) is a contained change; the route files in `api/`
wouldn't need to change much.

## Setup

```bash
cd exam_portal_backend
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt   # only needed if you swap in the real packages
python3 database.py               # creates + seeds exam_portal.db
python3 app.py                    # starts the server on http://localhost:5001
```

## Demo login

```
email:    davis@susl.ac.lk
password: password123
```

All student accounts use the same password (`password123`) with emails like
`saman.perera@susl.ac.lk`, if you want to test a student login against the
`users` table directly (there's no student-facing route yet — that's Team 02).

## API Reference

All `/api/lecturer/*` routes require `Authorization: Bearer <token>` from
`/api/auth/login`, and only work for the lecturer who owns the
subject/question/exam being accessed.

| Method | Route | Description |
|---|---|---|
| POST | `/api/auth/login` | `{email, password}` → `{token, user}` |
| GET | `/api/lecturer/dashboard` | Stat cards: subjects, questions, active exams, average score, recent questions |
| GET | `/api/lecturer/subjects` | Subjects you teach, with a live question count each |
| GET | `/api/lecturer/questions` | List questions. Query params: `subject_id`, `difficulty`, `search` |
| POST | `/api/lecturer/questions` | Create a question. Body: `subject_id, question_text, option_a..d, correct_option (A-D), difficulty, marks` |
| PUT | `/api/lecturer/questions/<id>` | Update any subset of the same fields |
| DELETE | `/api/lecturer/questions/<id>` | Delete a question (also removes it from any exams) |
| GET | `/api/lecturer/exams` | List exams you created, with attempt counts |
| POST | `/api/lecturer/exams` | Create an exam. Body: `title, subject_id, duration_minutes, start_time, end_time, question_ids: [...]` |
| GET | `/api/lecturer/exams/<id>/results` | Student scores, grades, percentages, and class average for that exam |

### Example: log in and list questions

```bash
TOKEN=$(curl -s -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"davis@susl.ac.lk","password":"password123"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['token'])")

curl http://localhost:5001/api/lecturer/questions \
  -H "Authorization: Bearer $TOKEN"
```

### Example: create an exam

```bash
curl -X POST http://localhost:5001/api/lecturer/exams \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{
        "title": "Data Structures Quiz 2",
        "subject_id": 1,
        "duration_minutes": 45,
        "start_time": "2026-09-10T09:00",
        "end_time": "2026-09-10T09:45",
        "question_ids": [5, 6]
      }'
```

## Database schema

Matches the shared schema in the project guide: `users`, `subjects`,
`questions`, `exams`, `exam_questions`, `attempts`, `answers`. See
`database.py` for the full `CREATE TABLE` statements and seed data (1
lecturer, 12 students, 5 subjects, 7 questions, 3 exams with realistic
attempt/score history).

## Wiring up the frontend prototype

The `exam_portal_lecturer.html` prototype delivered earlier uses in-memory
mock data. To connect it to this backend, replace its data arrays with
`fetch()` calls to the routes above — e.g. `saveQuestion()` would `POST`/`PUT`
to `/api/lecturer/questions`, and `createExam()` would `POST` to
`/api/lecturer/exams`, both sending `Authorization: Bearer <token>` from a
login call.
