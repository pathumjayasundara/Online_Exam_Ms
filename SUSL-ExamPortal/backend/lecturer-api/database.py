import sqlite3
from pathlib import Path

from flask import g
from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)


# =========================================================
# DATABASE
# =========================================================

# =========================================================
# DATABASE PATH
# =========================================================

BASE_DIR = Path(__file__).resolve().parent

DB_PATH = BASE_DIR / "exam_portal.db"
DEPARTMENT = "Department of Physical Sciences & Technology"


# =========================================================
# PROGRAMMES
# =========================================================

BSC_PHYSICAL_SCIENCES = "BSc in Physical Sciences"

BSC_HONS_APPLIED_PHYSICS = (
    "BSc Honours in Applied Physics"
)

BSC_HONS_CHEMICAL_TECHNOLOGY = (
    "BSc Honours in Chemical Technology"
)

BSC_HONS_COMPUTER_SCIENCE = (
    "BSc Honours in Computer Science and Technology"
)


PROGRAMMES = [
    BSC_PHYSICAL_SCIENCES,
    BSC_HONS_APPLIED_PHYSICS,
    BSC_HONS_CHEMICAL_TECHNOLOGY,
    BSC_HONS_COMPUTER_SCIENCE
]


# =========================================================
# HANDBOOK SUBJECT DATA
#
# Based on the Department of Physical Sciences &
# Technology curriculum.
#
# Tuple format:
#
# (
#     code,
#     title,
#     credits,
#     subject_type,
#     programme,
#     stream,
#     year,
#     semester
# )
# =========================================================

HANDBOOK_SUBJECTS = []


# =========================================================
# COMMON YEAR I - SEMESTER I
# =========================================================

COMMON_Y1_S1 = [

    (
        "PST 11201",
        "Mechanics and Properties of Matter",
        2,
        "Compulsory"
    ),

    (
        "PST 11202",
        "Introduction to Electricity and Magnetism",
        2,
        "Compulsory"
    ),

    (
        "PST 11103",
        "Physics Laboratory 1-I",
        1,
        "Compulsory"
    ),

    (
        "PST 11204",
        "General Chemistry",
        2,
        "Compulsory"
    ),

    (
        "PST 11205",
        "Fundamentals of Organic Chemistry",
        2,
        "Compulsory"
    ),

    (
        "PST 11106",
        "Inorganic Chemistry Laboratory I",
        1,
        "Compulsory"
    ),

    (
        "PST 11107",
        "Structured Programming",
        1,
        "Compulsory"
    ),

    (
        "PST 11208",
        "Computer Hardware and Software",
        2,
        "Compulsory"
    ),

    (
        "PST 11109",
        "Computer Laboratory 1-I",
        1,
        "Compulsory"
    ),

    (
        "PST 11210",
        "Calculus and Differential Equations",
        2,
        "Compulsory"
    ),

    (
        "PST-EGP-1101",
        "General English I",
        2,
        "Compulsory (Non-GPA)"
    )
]


# =========================================================
# COMMON YEAR I - SEMESTER II
# =========================================================

COMMON_Y1_S2 = [

    (
        "PST 12201",
        "Physics of Heat and Waves",
        2,
        "Compulsory"
    ),

    (
        "PST 12102",
        "Semi-Conductor Physics",
        1,
        "Compulsory"
    ),

    (
        "PST 12103",
        "AC Theory & Circuits",
        1,
        "Compulsory"
    ),

    (
        "PST 12104",
        "Physics Laboratory 1-II",
        1,
        "Compulsory"
    ),

    (
        "PST 12205",
        "Fundamentals of Physical Chemistry",
        2,
        "Compulsory"
    ),

    (
        "PST 12206",
        "Fundamentals of Analytical Chemistry",
        2,
        "Compulsory"
    ),

    (
        "PST 12107",
        "Organic Chemistry Laboratory I",
        1,
        "Compulsory"
    ),

    (
        "PST 12108",
        "Object Oriented Programming",
        1,
        "Compulsory"
    ),

    (
        "PST 12209",
        "Fundamentals of Statistics",
        2,
        "Compulsory"
    ),

    (
        "PST 12110",
        "Computer Laboratory 1-II",
        1,
        "Compulsory"
    ),

    (
        "PST 12211",
        "Database Management Systems",
        2,
        "Compulsory"
    ),

    (
        "PST-EGP-1201",
        "General English II",
        2,
        "Compulsory (Non-GPA)"
    )
]


# =========================================================
# COMMON YEAR II - SEMESTER I
# =========================================================

COMMON_Y2_S1 = [

    (
        "PST 21201",
        "Electronics",
        2,
        "Compulsory"
    ),

    (
        "PST 21202",
        "Geometrical and Physical Optics",
        2,
        "Compulsory"
    ),

    (
        "PST 21103",
        "Physics Laboratory 2-I",
        1,
        "Compulsory"
    ),

    (
        "PST 21204",
        "Organic Chemistry",
        2,
        "Compulsory"
    ),

    (
        "PST 21205",
        "Industrial Chemistry and Technology I (Organic)",
        2,
        "Compulsory"
    ),

    (
        "PST 21106",
        "Organic Chemistry Laboratory II",
        1,
        "Compulsory"
    ),

    (
        "PST 21207",
        "Data Structures & Algorithms",
        2,
        "Compulsory"
    ),

    (
        "PST 21208",
        "Computer Architecture and Assembly Language",
        2,
        "Compulsory"
    ),

    (
        "PST 21209",
        "Statistics for Experimental Analysis",
        2,
        "Compulsory"
    ),

    (
        "PST 21110",
        "Computer Laboratory 2-I",
        1,
        "Compulsory"
    ),

    (
        "PST 21111",
        "Physical Chemistry Laboratory I",
        1,
        "Elective"
    ),

    (
        "PST-EAP-2101",
        "Academic English I",
        2,
        "Compulsory (Non-GPA)"
    )
]


# =========================================================
# COMMON YEAR II - SEMESTER II
# =========================================================

COMMON_Y2_S2 = [

    (
        "PST 22201",
        "Physics of Electromagnetic Radiation and Introduction to the Laser",
        2,
        "Compulsory"
    ),

    (
        "PST 22202",
        "Quantum Physics, Atomic & Nuclear Physics",
        2,
        "Compulsory"
    ),

    (
        "PST 22103",
        "Physics Laboratory 2-II",
        1,
        "Compulsory"
    ),

    (
        "PST 22204",
        "Chemistry of Elements",
        2,
        "Compulsory"
    ),

    (
        "PST 22205",
        "Physical Chemistry",
        2,
        "Compulsory"
    ),

    (
        "PST 22106",
        "Inorganic Chemistry Laboratory II",
        1,
        "Compulsory"
    ),

    (
        "PST 22107",
        "Analytical Chemistry Laboratory I",
        1,
        "Elective"
    ),

    (
        "PST 22208",
        "Software Engineering",
        2,
        "Compulsory"
    ),

    (
        "PST 22209",
        "Statistical Methodology",
        2,
        "Compulsory"
    ),

    (
        "PST 22110",
        "Computer Laboratory 2-II",
        1,
        "Compulsory"
    ),

    (
        "PST 22211",
        "Operating Systems",
        2,
        "Compulsory"
    ),

    (
        "PST 22112",
        "Leadership and Communication",
        1,
        "Elective"
    ),

    (
        "PST 22213",
        "Biology for Physical Sciences",
        2,
        "Elective"
    ),

    (
        "PST 22114",
        "Soft Skill Development",
        1,
        "Elective"
    ),

    (
        "PST 22215",
        "Mathematical Methods",
        2,
        "Elective"
    ),

    (
        "PST 22116",
        "Introduction to Astronomy",
        1,
        "Elective"
    ),

    (
        "PST 22217",
        "Industrial Metrology",
        2,
        "Elective"
    ),

    (
        "PST 22218",
        "Management Information Systems",
        2,
        "Elective"
    ),

    (
        "PST 22219",
        "Molecular Spectroscopy",
        2,
        "Elective"
    ),

    (
        "PST-EAP-2201",
        "Academic English II",
        2,
        "Compulsory (Non-GPA)"
    )
]


# =========================================================
# BSC GENERAL PHYSICAL SCIENCES
# YEAR III - SEMESTER I
# =========================================================

PHYSICAL_SCIENCES_Y3_S1 = [

    (
        "PST 31201",
        "Solid State Physics",
        2,
        "Compulsory",
        "Physics"
    ),

    (
        "PST 31202",
        "Nuclear Physics & Application",
        2,
        "Compulsory",
        "Physics"
    ),

    (
        "PST 31203",
        "Quantum Mechanics",
        2,
        "Compulsory",
        "Physics"
    ),

    (
        "PST 31104",
        "Material Physics",
        1,
        "Compulsory",
        "Physics"
    ),

    (
        "PST 31205",
        "Special Relativity",
        2,
        "Compulsory",
        "Physics"
    ),

    (
        "PST 31206",
        "Optical Fiber & Telecommunication",
        2,
        "Compulsory",
        "Physics"
    ),

    (
        "PST 31107",
        "Introduction to Nanotechnology",
        1,
        "Compulsory",
        "Physics"
    ),

    (
        "PST 31108",
        "Physics Laboratory 3-I",
        1,
        "Compulsory",
        "Physics"
    ),

    (
        "PST 31209",
        "The Origin and Evolution of the Universe",
        2,
        "Elective",
        "Physics"
    ),

    (
        "PST 31210",
        "Multimedia and Hypermedia Systems Development",
        2,
        "Elective",
        "Physics"
    ),

    (
        "PST 31211",
        "Mathematical Programming",
        2,
        "Compulsory",
        "Physics"
    ),

    (
        "PST 31212",
        "Numerical Methods",
        2,
        "Elective",
        "Physics"
    ),

    (
        "PST 31213",
        "Economics",
        2,
        "Elective",
        "Physics"
    ),

    (
        "PST 31014",
        "Industrial Visit",
        0,
        "Compulsory",
        "Physics"
    ),

    (
        "PST-EBP-3101",
        "Business English",
        2,
        "Compulsory (Non-GPA)",
        "Physics"
    )
]


# =========================================================
# BSC GENERAL PHYSICAL SCIENCES
# YEAR III - CHEMICAL TECHNOLOGY
# =========================================================

PHYSICAL_SCIENCES_CHEM_Y3_S1 = [

    (
        "PST 31107",
        "Introduction to Nanotechnology",
        1,
        "Elective",
        "Chemical Technology"
    ),

    (
        "PST 31211",
        "Mathematical Programming",
        2,
        "Elective",
        "Chemical Technology"
    ),

    (
        "PST 31212",
        "Numerical Methods",
        2,
        "Elective",
        "Chemical Technology"
    ),

    (
        "PST 31213",
        "Economics",
        2,
        "Elective",
        "Chemical Technology"
    ),

    (
        "PST 31014",
        "Industrial Visit",
        0,
        "Compulsory",
        "Chemical Technology"
    ),

    (
        "PST 31216",
        "Biochemistry-I",
        2,
        "Compulsory",
        "Chemical Technology"
    ),

    (
        "PST 31217",
        "Electroanalytical Techniques",
        2,
        "Compulsory",
        "Chemical Technology"
    ),

    (
        "PST 31218",
        "Industrial Chemistry and Technology II (Inorganic)",
        2,
        "Compulsory",
        "Chemical Technology"
    ),

    (
        "PST 31219",
        "Environmental Chemistry",
        2,
        "Compulsory",
        "Chemical Technology"
    ),

    (
        "PST 31120",
        "Coordination Chemistry",
        1,
        "Compulsory",
        "Chemical Technology"
    ),

    (
        "PST 31121",
        "Laboratory Quality Control and Assurance",
        1,
        "Compulsory",
        "Chemical Technology"
    ),

    (
        "PST 31122",
        "Physical Chemistry Laboratory II",
        1,
        "Compulsory",
        "Chemical Technology"
    ),

    (
        "PST 31123",
        "Analytical Chemistry Laboratory II",
        1,
        "Compulsory",
        "Chemical Technology"
    ),

    (
        "PST-EBP-3101",
        "Business English",
        2,
        "Compulsory",
        "Chemical Technology"
    )
]


# =========================================================
# BSC GENERAL PHYSICAL SCIENCES
# YEAR III - COMPUTER SCIENCE & TECHNOLOGY
# =========================================================

PHYSICAL_SCIENCES_CST_Y3_S1 = [

    (
        "PST 31210",
        "Multimedia and Hypermedia Systems Development",
        2,
        "Compulsory",
        ""
    ),

    (
        "PST 31211",
        "Mathematical Programming",
        2,
        "Elective",
        ""
    ),

    (
        "PST 31212",
        "Numerical Methods",
        2,
        "Elective",
        ""
    ),

    (
        "PST 31014",
        "Industrial Visit",
        0,
        "Compulsory",
        ""
    ),

    (
        "PST 31215",
        "Agile Software Development",
        2,
        "Elective",
        ""
    ),

    (
        "PST 31224",
        "Artificial Intelligence & Expert Systems",
        2,
        "Compulsory",
        ""
    ),

    (
        "PST 31225",
        "Software Project Management",
        2,
        "Compulsory",
        ""
    ),

    (
        "PST 31226",
        "Software Quality Assurances",
        2,
        "Compulsory",
        ""
    ),

    (
        "PST 31227",
        "Object Oriented Analysis and Design",
        2,
        "Compulsory",
        ""
    ),

    (
        "PST 31128",
        "Computer Laboratory 3-I",
        1,
        "Compulsory",
        ""
    ),

    (
        "PST 31229",
        "Advanced Database Management Systems",
        2,
        "Compulsory",
        ""
    ),

    (
        "PST 31230",
        "Social and Professional Issues in Computing",
        2,
        "Elective",
        ""
    ),

    (
        "PST-EBP-3101",
        "Business English",
        2,
        "Compulsory (Non-GPA)",
        ""
    )
]


# =========================================================
# SPECIAL APPLIED PHYSICS
# YEAR III - SEMESTER I
# =========================================================

APPLIED_PHYSICS_Y3_S1 = [

    ("PST 31201", "Solid State Physics", 2, "Compulsory"),
    ("PST 31202", "Nuclear Physics & Applications", 2, "Compulsory"),
    ("PST 31203", "Quantum Mechanics", 2, "Compulsory"),
    ("PST 31104", "Material Physics", 1, "Compulsory"),
    ("PST 31105", "Special Relativity", 2, "Compulsory"),
    ("PST 31206", "Optical Fiber & Telecommunication", 2, "Compulsory"),
    ("PST 31107", "Introduction to Nanotechnology", 1, "Compulsory"),
    ("PST 31108", "Physics Laboratory 3-I", 1, "Compulsory"),
    ("PST 31209", "The Origin and Evolution of the Universe", 2, "Compulsory"),
    ("PST 31210", "Multimedia and Hypermedia Systems Development", 2, "Elective"),
    ("PST 31211", "Mathematical Programming", 2, "Compulsory"),
    ("PST 31212", "Numerical Methods", 1, "Elective"),
    ("PST 31213", "Economics", 2, "Elective"),
    ("PST 31014", "Industrial Visit", 0, "Compulsory"),
    ("PST-EBP-3101", "Business English", 2, "Compulsory (Non-GPA)")
]


# =========================================================
# SPECIAL CHEMICAL TECHNOLOGY
# YEAR III - SEMESTER I
# =========================================================

CHEMICAL_TECHNOLOGY_Y3_S1 = [

    ("PST 31107", "Introduction to Nanotechnology", 1, "Elective"),
    ("PST 31211", "Mathematical Programming", 2, "Elective"),
    ("PST 31212", "Numerical Methods", 2, "Elective"),
    ("PST 31213", "Economics", 2, "Elective"),
    ("PST 31014", "Industrial Visit", 0, "Compulsory"),
    ("PST 31216", "Biochemistry-I", 2, "Compulsory"),
    ("PST 31217", "Electroanalytical Techniques", 2, "Compulsory"),
    ("PST 31218", "Industrial Chemistry and Technology II (Inorganic)", 2, "Compulsory"),
    ("PST 31219", "Environmental Chemistry", 2, "Compulsory"),
    ("PST 31120", "Coordination Chemistry", 1, "Compulsory"),
    ("PST 31121", "Laboratory Quality Control and Assurance", 1, "Compulsory"),
    ("PST 31122", "Physical Chemistry Laboratory II", 1, "Compulsory"),
    ("PST 31123", "Analytical Chemistry Laboratory II", 1, "Compulsory"),
    ("PST-EBP-3101", "Business English", 2, "Compulsory")
]


# =========================================================
# SPECIAL COMPUTER SCIENCE & TECHNOLOGY
# YEAR III - SEMESTER I
# =========================================================

CST_Y3_S1 = [

    ("PST 31210", "Multimedia and Hypermedia Systems Development", 2, "Compulsory"),
    ("PST 31211", "Mathematical Programming", 2, "Elective"),
    ("PST 31212", "Numerical Methods", 2, "Elective"),
    ("PST 31014", "Industrial Visit", 0, "Compulsory"),
    ("PST 31215", "Agile Software Development", 2, "Elective"),
    ("PST 31224", "Artificial Intelligence & Expert Systems", 2, "Compulsory"),
    ("PST 31225", "Software Project Management", 2, "Compulsory"),
    ("PST 31226", "Software Quality Assurances", 2, "Compulsory"),
    ("PST 31227", "Object Oriented Analysis and Design", 2, "Compulsory"),
    ("PST 31128", "Computer Laboratory 3-I", 1, "Compulsory"),
    ("PST 31229", "Advanced Database Management Systems", 2, "Compulsory"),
    ("PST 31230", "Social and Professional Issues in Computing", 2, "Elective"),
    ("PST-EBP-3101", "Business English", 2, "Compulsory (Non-GPA)")
]


# =========================================================
# SPECIAL APPLIED PHYSICS
# YEAR III - SEMESTER II
# =========================================================

APPLIED_PHYSICS_Y3_S2 = [

    ("PST 32201", "Statistical Physics", 2, "Compulsory"),
    ("PST 32102", "Interaction of Radiation with Matter", 1, "Compulsory"),
    ("PST 32203", "Atmospheric Physics & Applications", 2, "Compulsory"),
    ("PST 32104", "Advanced Electronics", 1, "Compulsory"),
    ("PST 32205", "Solid State Devices", 2, "Compulsory"),
    ("PST 32206", "Astrophysics", 2, "Compulsory"),
    ("PST 32207", "Atomic and Molecular Spectroscopy", 2, "Elective"),
    ("PST 32108", "Current Topics in Physics", 1, "Compulsory"),
    ("PST 32109", "Human Resource Management", 1, "Elective"),
    ("PST 32210", "Statistics in Quality Control", 2, "Elective"),
    ("PST 32111", "Physics Laboratory 3-II", 1, "Compulsory"),
    ("PST 32212", "Graph Theory", 2, "Elective"),
    ("PST 32213", "Resource Efficient and Cleaner Production", 2, "Elective")
]


# =========================================================
# SPECIAL CHEMICAL TECHNOLOGY
# YEAR III - SEMESTER II
# =========================================================

CHEMICAL_TECHNOLOGY_Y3_S2 = [

    ("PST 32109", "Human Resource Management", 1, "Elective"),
    ("PST 32210", "Statistics in Quality Control", 2, "Elective"),
    ("PST 32213", "Resource Efficient and Cleaner Production", 2, "Elective"),
    ("PST 32214", "Chemistry of Drug Design and Drug Action", 2, "Compulsory"),
    ("PST 32215", "Polymer Chemistry and Technology", 2, "Compulsory"),
    ("PST 32216", "Surface and Colloid Chemistry", 2, "Compulsory"),
    ("PST 32217", "Biochemistry II", 2, "Compulsory"),
    ("PST 32118", "Advanced Organic Chemistry", 1, "Compulsory"),
    ("PST 32219", "Introduction to Organic Electronics", 2, "Elective"),
    ("PST 32220", "Structures and Properties of Solids", 2, "Compulsory"),
    ("PST 32121", "Advanced Inorganic Chemistry Laboratory", 1, "Compulsory"),
    ("PST 32122", "Biochemistry Laboratory", 1, "Compulsory"),
    ("PST 32223", "Organometallic Chemistry", 2, "Elective")
]


# =========================================================
# SPECIAL COMPUTER SCIENCE & TECHNOLOGY
# YEAR III - SEMESTER II
# =========================================================

CST_Y3_S2 = [

    ("PST 32109", "Human Resource Management", 1, "Elective"),
    ("PST 32210", "Statistics in Quality Control", 2, "Elective"),
    ("PST 32212", "Graph Theory", 2, "Elective"),
    ("PST 32224", "Artificial Neural Networks", 2, "Compulsory"),
    ("PST 32225", "Digital Image Processing", 2, "Compulsory"),
    ("PST 32226", "Data Mining and Applications", 2, "Compulsory"),
    ("PST 32227", "Data Communication and Computer Networks", 2, "Compulsory"),
    ("PST 32228", "Computer Graphics & Visualization", 2, "Compulsory"),
    ("PST 32229", "Project in Computer Science and Technology (Mini Project)", 2, "Compulsory"),
    ("PST 32130", "Computer Laboratory 3-II", 1, "Compulsory"),
    ("PST 32231", "Human Computer Interactions", 2, "Elective"),
    ("PST 32232", "Bioinformatics", 2, "Elective"),
    ("PST 32133", "Current Topics in Computer Technology", 1, "Elective")
]


# =========================================================
# SPECIAL APPLIED PHYSICS
# YEAR IV - SEMESTER I
# =========================================================

APPLIED_PHYSICS_Y4_S1 = [

    ("PST 41201", "Research Methodology and Scientific Communication", 2, "Compulsory"),
    ("PST 41202", "Computational Physics", 2, "Compulsory"),
    ("PST 41203", "Robotics", 2, "Elective"),
    ("PST 41204", "Remote Sensing & GIS", 2, "Compulsory"),
    ("PST 41205", "Geophysics", 2, "Compulsory"),
    ("PST 41206", "Medical and Bio Physics", 2, "Compulsory"),
    ("PST 41207", "Advanced Nanotechnology", 2, "Elective"),
    ("PST 41208", "Data Acquisition and Signal Processing Methods", 2, "Compulsory"),
    ("PST 41209", "Advanced Laser Physics", 2, "Elective"),
    ("PST 41210", "Automation", 2, "Elective"),
    ("PST 41211", "Astronomical Instruments and Data Reduction & Analysis", 2, "Compulsory"),
    ("PST 41212", "Electrochemical Power Conversion", 2, "Elective"),
    ("PST 41013", "Literature Search Seminar in Applied Physics", 1, "Compulsory (Non-Credited)"),
    ("PST 41014", "Independent Research / Project in Applied Physics", 2, "Compulsory (Non-Credited)"),
    ("PST 41215", "Industrial Management", 2, "Elective"),
    ("PST 41216", "Classical Mechanics", 2, "Compulsory"),
    ("PST 41235", "Critical Thinking", 2, "Elective")
]


# =========================================================
# SPECIAL CHEMICAL TECHNOLOGY
# YEAR IV - SEMESTER I
# =========================================================

CHEMICAL_TECHNOLOGY_Y4_S1 = [

    ("PST 41201", "Research Methodology and Scientific Communication", 0, "Compulsory"),
    ("PST 41207", "Advanced Nanotechnology", 2, "Elective"),
    ("PST 41212", "Electrochemical Power Conversion", 2, "Elective"),
    ("PST 41215", "Industrial Management", 2, "Elective"),
    ("PST 41217", "Natural Products Chemistry", 2, "Compulsory"),
    ("PST 41218", "Biotechnology", 2, "Compulsory"),
    ("PST 41219", "Advanced Solid State Chemistry", 2, "Compulsory"),
    ("PST 41120", "Bioinorganic Chemistry", 1, "Compulsory"),
    ("PST 41221", "Instrumental Analysis", 2, "Compulsory"),
    ("PST 41222", "Applied Molecular Modeling", 2, "Elective"),
    ("PST 41223", "State of Matter", 2, "Elective"),
    ("PST 41124", "Literature Search Seminar in Chemical Technology", 1, "Compulsory"),
    ("PST 41225", "Independent Research / Project in Chemical Technology", 2, "Compulsory"),
    ("PST 41226", "Computer Applications in Instrumentation", 2, "Elective"),
    ("PST 41235", "Critical Thinking", 1, "Elective")
]


# =========================================================
# SPECIAL COMPUTER SCIENCE & TECHNOLOGY
# YEAR IV - SEMESTER I
# =========================================================

CST_Y4_S1 = [

    ("PST 41201", "Research Methodology and Scientific Communication", 0, "Compulsory"),
    ("PST 41203", "Robotics", 2, "Elective"),
    ("PST 41215", "Industrial Management", 2, "Elective"),
    ("PST 41227", "Web services", 2, "Compulsory"),
    ("PST 41228", "Computer System Security", 2, "Compulsory"),
    ("PST 41229", "Advanced Computer Networks", 2, "Compulsory"),
    ("PST 41230", "Internet of Things (IoT)", 2, "Elective"),
    ("PST 41231", "Natural Language Processing", 2, "Elective"),
    ("PST 41232", "Cloud Computing", 2, "Compulsory"),
    ("PST 41233", "Business Process Management Systems", 2, "Elective"),
    ("PST 41234", "Mobile Computing", 2, "Elective"),
    ("PST 41235", "Critical Thinking", 2, "Elective")
]


# =========================================================
# YEAR IV - SEMESTER II
# =========================================================

APPLIED_PHYSICS_Y4_S2 = [

    (
        "PST 42801",
        "Project Work (Industrial Exposure): B.Sc. Thesis in Applied Physics",
        8,
        "Compulsory"
    ),

    (
        "PST 42102",
        "Literature Search Seminar in Applied Physics",
        1,
        "Compulsory"
    ),

    (
        "PST 42203",
        "Independent Research / Project in Applied Physics",
        2,
        "Compulsory"
    )
]


CHEMICAL_TECHNOLOGY_Y4_S2 = [

    (
        "PST 42804",
        "Project Work (Industrial Exposure): B.Sc. Thesis in Chemical Technology",
        8,
        "Compulsory"
    )
]


CST_Y4_S2 = [

    (
        "PST 42803",
        "Project: B.Sc. Thesis in Computer Science and Technology",
        8,
        "Compulsory"
    ),

    (
        "PST 42606",
        "Industrial Training",
        6,
        "Compulsory"
    )
]


# =========================================================
# HELPER - ADD COMMON SUBJECTS
# =========================================================

def add_common_subjects():

    for programme in PROGRAMMES:

        for subject in COMMON_Y1_S1:

            code, title, credits, subject_type = subject

            HANDBOOK_SUBJECTS.append(
                (
                    code,
                    title,
                    credits,
                    subject_type,
                    programme,
                    "",
                    1,
                    1
                )
            )

        for subject in COMMON_Y1_S2:

            code, title, credits, subject_type = subject

            HANDBOOK_SUBJECTS.append(
                (
                    code,
                    title,
                    credits,
                    subject_type,
                    programme,
                    "",
                    1,
                    2
                )
            )

        for subject in COMMON_Y2_S1:

            code, title, credits, subject_type = subject

            HANDBOOK_SUBJECTS.append(
                (
                    code,
                    title,
                    credits,
                    subject_type,
                    programme,
                    "",
                    2,
                    1
                )
            )

        for subject in COMMON_Y2_S2:

            code, title, credits, subject_type = subject

            # Programme-specific compulsory requirements
            # are handled here.

            final_type = subject_type

            if code == "PST 21111" and programme == BSC_HONS_CHEMICAL_TECHNOLOGY:
                final_type = "Compulsory"

            if code == "PST 22107" and programme == BSC_HONS_CHEMICAL_TECHNOLOGY:
                final_type = "Compulsory"

            if code == "PST 22215" and programme == BSC_HONS_APPLIED_PHYSICS:
                final_type = "Compulsory"

            if code == "PST 22116" and programme == BSC_HONS_APPLIED_PHYSICS:
                final_type = "Compulsory"

            if code == "PST 22218" and programme == BSC_HONS_COMPUTER_SCIENCE:
                final_type = "Compulsory"

            if code == "PST 22219" and programme == BSC_HONS_CHEMICAL_TECHNOLOGY:
                final_type = "Compulsory"

            HANDBOOK_SUBJECTS.append(
                (
                    code,
                    title,
                    credits,
                    final_type,
                    programme,
                    "",
                    2,
                    2
                )
            )


# =========================================================
# HELPER - ADD SUBJECT LIST
# =========================================================

def add_subject_list(
    programme,
    subject_list,
    year,
    semester,
    stream=""
):

    for subject in subject_list:

        if len(subject) == 4:

            code, title, credits, subject_type = subject

        else:

            code, title, credits, subject_type, stream = subject

        HANDBOOK_SUBJECTS.append(
            (
                code,
                title,
                credits,
                subject_type,
                programme,
                stream,
                year,
                semester
            )
        )


# =========================================================
# BUILD HANDBOOK DATA
# =========================================================

add_common_subjects()


# ---------------------------------------------------------
# BSc GENERAL PHYSICAL SCIENCES
# ---------------------------------------------------------

add_subject_list(
    BSC_PHYSICAL_SCIENCES,
    PHYSICAL_SCIENCES_Y3_S1,
    3,
    1
)

add_subject_list(
    BSC_PHYSICAL_SCIENCES,
    PHYSICAL_SCIENCES_CHEM_Y3_S1,
    3,
    1,
    "Chemical Technology"
)

add_subject_list(
    BSC_PHYSICAL_SCIENCES,
    PHYSICAL_SCIENCES_CST_Y3_S1,
    3,
    1,
    "Computer Science and Technology"
)


# General degree Year III Semester II

add_subject_list(
    BSC_PHYSICAL_SCIENCES,
    [
        (
            "PST 32801",
            "Project Work (Industrial Exposure): B.Sc. Thesis in Physical Sciences (Major in Applied Physics)",
            8,
            "Compulsory"
        )
    ],
    3,
    2,
    "Physics"
)

add_subject_list(
    BSC_PHYSICAL_SCIENCES,
    [
        (
            "PST 32802",
            "Project Work (Industrial Exposure): B.Sc. Thesis in Physical Sciences (Major in Chemical Technology)",
            8,
            "Compulsory"
        )
    ],
    3,
    2,
    "Chemical Technology"
)

add_subject_list(
    BSC_PHYSICAL_SCIENCES,
    [
        (
            "PST 32803",
            "Project Work (Industrial Exposure): B.Sc. Thesis in Physical Sciences (Major in Computer Science & Technology)",
            8,
            "Compulsory"
        )
    ],
    3,
    2,
    "Computer Science and Technology"
)


# ---------------------------------------------------------
# BSc Hons Applied Physics
# ---------------------------------------------------------

add_subject_list(
    BSC_HONS_APPLIED_PHYSICS,
    APPLIED_PHYSICS_Y3_S1,
    3,
    1
)

add_subject_list(
    BSC_HONS_APPLIED_PHYSICS,
    APPLIED_PHYSICS_Y3_S2,
    3,
    2
)

add_subject_list(
    BSC_HONS_APPLIED_PHYSICS,
    APPLIED_PHYSICS_Y4_S1,
    4,
    1
)

add_subject_list(
    BSC_HONS_APPLIED_PHYSICS,
    APPLIED_PHYSICS_Y4_S2,
    4,
    2
)


# ---------------------------------------------------------
# BSc Hons Chemical Technology
# ---------------------------------------------------------

add_subject_list(
    BSC_HONS_CHEMICAL_TECHNOLOGY,
    CHEMICAL_TECHNOLOGY_Y3_S1,
    3,
    1
)

add_subject_list(
    BSC_HONS_CHEMICAL_TECHNOLOGY,
    CHEMICAL_TECHNOLOGY_Y3_S2,
    3,
    2
)

add_subject_list(
    BSC_HONS_CHEMICAL_TECHNOLOGY,
    CHEMICAL_TECHNOLOGY_Y4_S1,
    4,
    1
)

add_subject_list(
    BSC_HONS_CHEMICAL_TECHNOLOGY,
    CHEMICAL_TECHNOLOGY_Y4_S2,
    4,
    2
)


# ---------------------------------------------------------
# BSc Hons Computer Science & Technology
# ---------------------------------------------------------

add_subject_list(
    BSC_HONS_COMPUTER_SCIENCE,
    CST_Y3_S1,
    3,
    1
)

add_subject_list(
    BSC_HONS_COMPUTER_SCIENCE,
    CST_Y3_S2,
    3,
    2
)

add_subject_list(
    BSC_HONS_COMPUTER_SCIENCE,
    CST_Y4_S1,
    4,
    1
)

add_subject_list(
    BSC_HONS_COMPUTER_SCIENCE,
    CST_Y4_S2,
    4,
    2
)


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db():

    if "db" not in g:

        g.db = sqlite3.connect(
            str(DB_PATH)
        )

        g.db.row_factory = sqlite3.Row

        g.db.execute(
            "PRAGMA foreign_keys = ON"
        )

    return g.db

def close_db(exception=None):

    db = g.pop("db", None)

    if db is not None:
        db.close()


# =========================================================
# PASSWORD
# =========================================================

def verify_password(
    entered_password,
    stored_password
):

    return check_password_hash(
        stored_password,
        entered_password
    )


# =========================================================
# DATABASE MIGRATION
# =========================================================

def add_column_if_missing(
    db,
    table_name,
    column_name,
    column_definition
):

    columns = db.execute(
        f"PRAGMA table_info({table_name})"
    ).fetchall()

    existing_columns = {
        column["name"]
        for column in columns
    }

    if column_name not in existing_columns:

        db.execute(
            f"""
            ALTER TABLE {table_name}
            ADD COLUMN {column_name}
            {column_definition}
            """
        )


# =========================================================
# INSERT / UPDATE HANDBOOK SUBJECTS
# =========================================================

def seed_subjects():

    db = get_db()

    for subject in HANDBOOK_SUBJECTS:

        (
            code,
            title,
            credits,
            subject_type,
            programme,
            stream,
            year,
            semester
        ) = subject

        existing = db.execute(
            """
            SELECT id
            FROM subjects
            WHERE code = ?
              AND programme = ?
              AND stream = ?
              AND year = ?
              AND semester = ?
            """,
            (
                code,
                programme,
                stream,
                year,
                semester
            )
        ).fetchone()

        if existing is None:

            db.execute(
                """
                INSERT INTO subjects
                (
                    code,
                    title,
                    credits,
                    subject_type,
                    programme,
                    stream,
                    year,
                    semester,
                    department,
                    lecturer_id
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, NULL)
                """,
                (
                    code,
                    title,
                    credits,
                    subject_type,
                    programme,
                    stream,
                    year,
                    semester,
                    DEPARTMENT
                )
            )

        else:

            db.execute(
                """
                UPDATE subjects

                SET
                    title = ?,
                    credits = ?,
                    subject_type = ?,
                    department = ?

                WHERE id = ?
                """,
                (
                    title,
                    credits,
                    subject_type,
                    DEPARTMENT,
                    existing["id"]
                )
            )

    db.commit()


# =========================================================
# INITIALIZE DATABASE
# =========================================================

def init_db():

    db = get_db()


    # =====================================================
    # USERS
    # =====================================================

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS users
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            email TEXT UNIQUE NOT NULL,

            password_hash TEXT NOT NULL,

            role TEXT NOT NULL,

            department TEXT
        )
        """
    )


    # =====================================================
    # SUBJECTS
    # =====================================================

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS subjects
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            code TEXT NOT NULL,

            title TEXT NOT NULL,

            credits INTEGER DEFAULT 0,

            subject_type TEXT DEFAULT 'Compulsory',

            programme TEXT,

            stream TEXT,

            year INTEGER,

            semester INTEGER,

            department TEXT,

            lecturer_id INTEGER,

            UNIQUE
            (
                code,
                programme,
                stream,
                year,
                semester
            ),

            FOREIGN KEY(lecturer_id)
                REFERENCES users(id)
                ON DELETE SET NULL
        )
        """
    )


    # =====================================================
    # LECTURER SUBJECTS
    # =====================================================

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS lecturer_subjects
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            lecturer_id INTEGER NOT NULL,

            subject_id INTEGER NOT NULL,

            UNIQUE
            (
                lecturer_id,
                subject_id
            ),

            FOREIGN KEY(lecturer_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY(subject_id)
                REFERENCES subjects(id)
                ON DELETE CASCADE
        )
        """
    )


    # =====================================================
    # QUESTIONS
    # =====================================================

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS questions
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            subject_id INTEGER NOT NULL,

            question_type TEXT
                DEFAULT 'Multiple Choice',

            question_text TEXT NOT NULL,

            option_a TEXT,

            option_b TEXT,

            option_c TEXT,

            option_d TEXT,

            correct_answer TEXT,

            expected_answer TEXT,

            marks INTEGER DEFAULT 1,

            difficulty TEXT
                DEFAULT 'Medium',

            created_by INTEGER,

            created_at DATETIME,

            FOREIGN KEY(subject_id)
                REFERENCES subjects(id)
                ON DELETE CASCADE,

            FOREIGN KEY(created_by)
                REFERENCES users(id)
                ON DELETE SET NULL
        )
        """
    )


    # =====================================================
    # MIGRATE OLD QUESTIONS TABLE
    # =====================================================

    add_column_if_missing(
        db,
        "questions",
        "question_type",
        "TEXT DEFAULT 'Multiple Choice'"
    )

    add_column_if_missing(
        db,
        "questions",
        "expected_answer",
        "TEXT"
    )

    add_column_if_missing(
        db,
        "questions",
        "difficulty",
        "TEXT DEFAULT 'Medium'"
    )

    add_column_if_missing(
        db,
        "questions",
        "created_at",
        "DATETIME"
    )


    # =====================================================
    # EXAMS
    # =====================================================

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS exams
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            title TEXT NOT NULL,

            subject_id INTEGER NOT NULL,

            lecturer_id INTEGER NOT NULL,

            duration INTEGER DEFAULT 60,

            exam_date TEXT,

            status TEXT DEFAULT 'Draft',

            FOREIGN KEY(subject_id)
                REFERENCES subjects(id)
                ON DELETE CASCADE,

            FOREIGN KEY(lecturer_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        )
        """
    )


    # =====================================================
    # EXAM QUESTIONS
    # =====================================================

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS exam_questions
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            exam_id INTEGER NOT NULL,

            question_id INTEGER NOT NULL,

            UNIQUE
            (
                exam_id,
                question_id
            ),

            FOREIGN KEY(exam_id)
                REFERENCES exams(id)
                ON DELETE CASCADE,

            FOREIGN KEY(question_id)
                REFERENCES questions(id)
                ON DELETE CASCADE
        )
        """
    )


    # =====================================================
    # RESULTS
    # =====================================================

    db.execute(
        """
        CREATE TABLE IF NOT EXISTS results
        (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            exam_id INTEGER NOT NULL,

            student_id INTEGER,

            student_name TEXT,

            score REAL DEFAULT 0,

            total_marks REAL DEFAULT 0,

            submitted_at DATETIME,

            FOREIGN KEY(exam_id)
                REFERENCES exams(id)
                ON DELETE CASCADE
        )
        """
    )


    # =====================================================
    # DEFAULT LECTURER
    # =====================================================

    existing_user = db.execute(
        """
        SELECT id
        FROM users
        WHERE LOWER(email) = ?
        """,
        ("davis@susl.ac.lk",)
    ).fetchone()


    if existing_user is None:

        db.execute(
            """
            INSERT INTO users
            (
                name,
                email,
                password_hash,
                role,
                department
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                "Dr. A. Davis",

                "davis@susl.ac.lk",

                generate_password_hash(
                    "password123"
                ),

                "lecturer",

                DEPARTMENT
            )
        )


    # =====================================================
    # SAVE TABLE STRUCTURE
    # =====================================================

    db.commit()


    # =====================================================
    # LOAD HANDBOOK SUBJECTS
    # =====================================================

    seed_subjects()


    # =====================================================
    # DISPLAY INFORMATION
    # =====================================================

    subject_count = db.execute(
        """
        SELECT COUNT(*)
        FROM subjects
        """
    ).fetchone()[0]

    programme_count = db.execute(
        """
        SELECT COUNT(DISTINCT programme)
        FROM subjects
        """
    ).fetchone()[0]

    print()
    print("=" * 65)
    print("Database initialized successfully.")
    print(
        f"{subject_count} handbook subjects loaded."
    )
    print(
        f"{programme_count} programmes loaded."
    )
    print("=" * 65)
    print()


# =========================================================
# OPTIONAL DATABASE INFORMATION
# =========================================================

def get_database_summary():

    db = get_db()

    subjects = db.execute(
        """
        SELECT
            programme,
            COUNT(*) AS total_subjects
        FROM subjects
        GROUP BY programme
        ORDER BY programme
        """
    ).fetchall()

    return [
        dict(row)
        for row in subjects
    ]