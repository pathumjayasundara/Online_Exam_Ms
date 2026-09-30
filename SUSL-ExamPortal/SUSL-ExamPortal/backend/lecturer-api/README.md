# ExamPortal — Lecturer Module

## Online Examination Management System

A Flask-based backend for the **Lecturer Module** of the Online Examination Management System developed for the Faculty of Applied Sciences, Sabaragamuwa University of Sri Lanka (SUSL).

The system allows lecturers to select subjects from the department's handbook, manage questions, create examinations, and view examination results through a secure REST API.

---

## Features

### Lecturer Authentication

- Lecturer login
- Email and password authentication
- Secure password hashing
- Token-based authentication
- Lecturer role verification
- Protected lecturer API routes

### Lecturer Dashboard

- Total subjects
- Total questions
- Active examinations
- Average examination score
- Recent questions

### Subject Management

Lecturers can:

- View all handbook subjects
- Filter subjects by:
  - Programme
  - Stream / Major
  - Year
  - Semester
- Select subjects for the logged-in lecturer
- View selected subjects under **My Subjects**
- Remove subjects from My Subjects

### Question Bank

Lecturers can manage questions belonging to their selected subjects.

Supported question types:

- Multiple Choice
- True / False
- Short Answer
- Essay / Long Answer
- Fill in the Blank
- Matching
- Scenario / Structured

Question operations:

- Add question
- View questions
- Search questions
- Filter by subject
- Filter by difficulty
- Edit question
- Delete question

### Examination Management

Lecturers can:

- Create examinations
- Select a subject
- Select questions from their question bank
- Set examination duration
- Set examination date/time
- View created examinations
- Delete examinations

### Results

Lecturers can view results for examinations they created, including:

- Student name
- Score
- Total marks
- Percentage
- Class average
- Submission information

---

## Programmes and Subjects

The system contains handbook subjects from the **Department of Physical Sciences & Technology**.

Supported programmes include:

1. **BSc in Physical Sciences**
2. **BSc Honours in Applied Physics**
3. **BSc Honours in Chemical Technology**
4. **BSc Honours in Computer Science and Technology**

Subjects are organized according to:

- Programme
- Stream / Major
- Academic Year
- Semester
- Subject Code
- Credits
- Subject Type

---

## Technology Stack

### Backend

- Python
- Flask
- SQLite
- REST API
- Werkzeug Security

### Authentication

- Password hashing using Werkzeug
- HMAC-signed authentication tokens
- Bearer token authentication

### Frontend

- HTML5
- CSS3
- JavaScript

### Development Tools

- Visual Studio Code
- Git
- GitHub

---

## Project Structure

```text
exam_portal_Lecturer_Part/
│
├── api/
│   ├── __init__.py
│   ├── auth.py
│   └── lecturer.py
│
├── static/
│   └── SUSL.png
│
├── templates/
│   └── exam_portal_lecturer.html
│
├── app.py
├── auth_utils.py
├── database.py
├── exam_portal.db
├── README.md
└── requirements.txt