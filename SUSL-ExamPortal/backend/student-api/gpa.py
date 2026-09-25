"""
Official GPA calculation — Faculty of Applied Sciences handbook,
"Grades and Grade Points" / "Grade Point Average" / "Final GPA (FGPA)".

    Year GPA = sum(credits_i * grade_point_i) / sum(credits_i)
        "...the sum of the products of the credits assigned per year and
        the grade point granted for each subject divided by the total
        number of credits assigned per year."
    Semester GPA uses the same formula, scoped to one semester's subjects
        (the handbook only defines this at year granularity; applying the
        identical formula at semester granularity is not a different
        formula, just a narrower scope of the same one).
    FGPA (Honours, 4-year programmes) = 0.2*GPA_y1 + 0.2*GPA_y2 + 0.3*GPA_y3 + 0.3*GPA_y4
    FGPA (General, 3-year programmes) = 0.3*GPA_y1 + 0.3*GPA_y2 + 0.4*GPA_y3

Courses whose `kind` contains "Non-GPA" (e.g. General/Academic/Business
English) are excluded from every calculation below, per the handbook.

This module is intentionally backend-only, matching the "GPA calculation
should preferably be performed on the backend rather than trusting
frontend calculations" requirement — the frontend must call
GET /api/student/results/sheet and /api/student/results/summary rather
than compute any of this itself.
"""
from extensions import db
from models import CourseResult, Subject

FGPA_WEIGHTS_HONOURS = [0.2, 0.2, 0.3, 0.3]   # years 1-4
FGPA_WEIGHTS_GENERAL = [0.3, 0.3, 0.4]        # years 1-3

SEM_TO_YEAR = {
    "y1s1": 1, "y1s2": 1,
    "y2s1": 2, "y2s2": 2,
    "y3s1": 3, "y3s2": 3,
    "y4s1": 4, "y4s2": 4,
}


def _gpa_rows_for_user(user_id, semester=None, year=None):
    """Published, GPA-counted (subject, credits, grade_point) rows for a student."""
    q = (
        db.session.query(CourseResult.grade_point, Subject.credits, Subject.kind)
        .join(Subject, Subject.code == CourseResult.subject_code)
        .filter(CourseResult.user_id == user_id, CourseResult.published.is_(True))
    )
    if semester:
        q = q.filter(CourseResult.semester == semester)
    if year:
        sems = [s for s, y in SEM_TO_YEAR.items() if y == year]
        q = q.filter(CourseResult.semester.in_(sems))

    return [(credits, gp) for gp, credits, kind in q.all() if "Non-GPA" not in kind]


def _credit_weighted_gpa(rows):
    if not rows:
        return None
    total_credits = sum(c for c, _ in rows)
    total_points = sum(c * gp for c, gp in rows)
    return (total_points / total_credits) if total_credits else None


def get_semester_gpa(user_id, semester):
    """GET /api/student/results/sheet?semester=<key> uses this."""
    return _credit_weighted_gpa(_gpa_rows_for_user(user_id, semester=semester))


def get_year_gpa(user_id, year):
    return _credit_weighted_gpa(_gpa_rows_for_user(user_id, year=year))


def get_fgpa(user_id, programme_years=4):
    """
    Returns the Final GPA once every year (1..programme_years) has at least
    one published, GPA-counted result — mirroring the handbook's rule that
    FGPA "will be calculated at the completion of all requirements for the
    degree program." Returns None if any year is still incomplete.
    """
    weights = FGPA_WEIGHTS_HONOURS if programme_years == 4 else FGPA_WEIGHTS_GENERAL
    year_gpas = [get_year_gpa(user_id, y) for y in range(1, programme_years + 1)]
    if any(g is None for g in year_gpas):
        return None
    return round(sum(w * g for w, g in zip(weights, year_gpas)), 2)


def get_overall_gpa(user_id, programme_years=4):
    """
    GET /api/student/results/summary uses this. Returns
    {"gpa": float|None, "is_final": bool} — the official weighted FGPA once
    complete, otherwise a provisional credit-weighted average across all
    published results to date (NOT an invented alternative formula — same
    core sum(credit*point)/sum(credit) calculation, just not yet
    year-weighted because the degree isn't finished).
    """
    fgpa = get_fgpa(user_id, programme_years)
    if fgpa is not None:
        return {"gpa": fgpa, "is_final": True}
    provisional = _credit_weighted_gpa(_gpa_rows_for_user(user_id))
    return {"gpa": round(provisional, 2) if provisional is not None else None, "is_final": False}
