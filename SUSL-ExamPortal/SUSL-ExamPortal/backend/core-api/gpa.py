"""
Official GPA calculation — Faculty of Applied Sciences handbook,
"Grades and Grade Points" / "Grade Point Average" / "Final GPA (FGPA)".

    Year/Semester GPA = sum(credits_i * grade_point_i) / sum(credits_i)
    FGPA (Honours, 4-year programmes) = 0.2*GPA_y1 + 0.2*GPA_y2 + 0.3*GPA_y3 + 0.3*GPA_y4

Courses whose `kind` contains "Non-GPA" are excluded from every calculation,
per the handbook. This module is intentionally backend-only — the frontend
must call GET /api/student/results/sheet and /results/summary rather than
compute any of this itself.
"""
FGPA_WEIGHTS_HONOURS = [0.2, 0.2, 0.3, 0.3]  # years 1-4

SEM_TO_YEAR = {
    "y1s1": 1, "y1s2": 1, "y2s1": 2, "y2s2": 2,
    "y3s1": 3, "y3s2": 3, "y4s1": 4, "y4s2": 4,
}


def _gpa_rows_for_user(db, user_id, semester=None, year=None):
    query = """
        SELECT s.credits AS credits, cr.grade_point AS grade_point, s.kind AS kind
        FROM course_results cr
        JOIN subjects s ON s.code = cr.subject_code
        WHERE cr.user_id = ? AND cr.published = 1
    """
    params = [user_id]
    if semester:
        query += " AND cr.semester = ?"
        params.append(semester)
    if year:
        sems = [s for s, y in SEM_TO_YEAR.items() if y == year]
        if not sems:
            return []
        query += f" AND cr.semester IN ({','.join('?' for _ in sems)})"
        params.extend(sems)

    rows = db.execute(query, params).fetchall()
    return [(r["credits"], r["grade_point"]) for r in rows if "Non-GPA" not in r["kind"]]


def _credit_weighted_gpa(rows):
    if not rows:
        return None
    total_credits = sum(c for c, _ in rows)
    total_points = sum(c * gp for c, gp in rows)
    return (total_points / total_credits) if total_credits else None


def get_semester_gpa(db, user_id, semester):
    return _credit_weighted_gpa(_gpa_rows_for_user(db, user_id, semester=semester))


def get_year_gpa(db, user_id, year):
    return _credit_weighted_gpa(_gpa_rows_for_user(db, user_id, year=year))


def get_fgpa(db, user_id, programme_years=4):
    weights = FGPA_WEIGHTS_HONOURS[:programme_years]
    year_gpas = [get_year_gpa(db, user_id, y) for y in range(1, programme_years + 1)]
    if any(g is None for g in year_gpas):
        return None
    return round(sum(w * g for w, g in zip(weights, year_gpas)), 2)


def get_overall_gpa(db, user_id, programme_years=4):
    fgpa = get_fgpa(db, user_id, programme_years)
    if fgpa is not None:
        return {"gpa": fgpa, "isFinal": True}
    provisional = _credit_weighted_gpa(_gpa_rows_for_user(db, user_id))
    return {"gpa": round(provisional, 2) if provisional is not None else None, "isFinal": False}
