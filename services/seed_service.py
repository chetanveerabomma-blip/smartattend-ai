"""
SmartAttend AI - Database Seeder Service
Populates default accounts, sample students, courses, and attendance records on first boot.
"""

from datetime import datetime, timezone
from models import db, User, Student, Faculty, Course, Enrollment, AttendanceRecord
from services.attendance_service import generate_system_notifications


def seed_database_if_empty():
    """
    Checks if database contains users; if empty, populates initial sample dataset.
    Prevents duplicate sample data every time application starts.
    """
    if User.query.first() is not None:
        return False  # Already seeded

    print("[SmartAttend Seed] Seeding initial database...")

    # 1. Create Faculty
    f1 = Faculty(
        faculty_id="F101",
        name="Dr. Rajesh Sharma",
        department="Computer Science",
        email="rajesh.sharma@smartattend.edu",
        phone="+91 98765 43210",
        office="CS Block, Room 304"
    )
    f2 = Faculty(
        faculty_id="F102",
        name="Prof. Ananya Iyer",
        department="Electronics",
        email="ananya.iyer@smartattend.edu",
        phone="+91 98765 43211",
        office="EC Block, Room 201"
    )
    f3 = Faculty(
        faculty_id="F103",
        name="Dr. Vikram Rao",
        department="Information Technology",
        email="vikram.rao@smartattend.edu",
        phone="+91 98765 43212",
        office="IT Block, Room 105"
    )
    db.session.add_all([f1, f2, f3])
    db.session.commit()

    # 2. Create Courses
    c1 = Course(
        course_id="CS101",
        course_name="Data Structures & Algorithms",
        department="Computer Science",
        semester=3,
        faculty_id=f1.id,
        faculty_name=f1.name,
        total_conducted=50,
        remaining_classes=20
    )
    c2 = Course(
        course_id="CS102",
        course_name="Operating Systems",
        department="Computer Science",
        semester=3,
        faculty_id=f1.id,
        faculty_name=f1.name,
        total_conducted=50,
        remaining_classes=40
    )
    c3 = Course(
        course_id="EC201",
        course_name="Digital Signal Processing",
        department="Electronics",
        semester=4,
        faculty_id=f2.id,
        faculty_name=f2.name,
        total_conducted=60,
        remaining_classes=25
    )
    c4 = Course(
        course_id="IT301",
        course_name="Database Management Systems",
        department="Information Technology",
        semester=5,
        faculty_id=f3.id,
        faculty_name=f3.name,
        total_conducted=50,
        remaining_classes=15
    )
    c5 = Course(
        course_id="CS103",
        course_name="Computer Networks",
        department="Computer Science",
        semester=4,
        faculty_id=f1.id,
        faculty_name=f1.name,
        total_conducted=45,
        remaining_classes=30
    )
    db.session.add_all([c1, c2, c3, c4, c5])
    db.session.commit()

    # 3. Create Students
    students_data = [
        ("S1", "Rahul Verma", "Computer Science", 2, "A", "rahul.verma@college.edu"),
        ("S2", "Priya Patel", "Computer Science", 2, "A", "priya.patel@college.edu"),
        ("S3", "Amit Kumar", "Computer Science", 2, "B", "amit.kumar@college.edu"),
        ("S4", "Sneha Reddy", "Electronics", 2, "A", "sneha.reddy@college.edu"),
        ("S5", "Rohan Deshmukh", "Information Technology", 3, "A", "rohan.d@college.edu"),
        ("S6", "Anjali Gupta", "Computer Science", 2, "A", "anjali.g@college.edu"),
        ("S7", "Karthik N", "Computer Science", 2, "B", "karthik.n@college.edu"),
        ("S8", "Divya Nair", "Electronics", 2, "B", "divya.n@college.edu"),
        ("S9", "Harish Mehta", "Information Technology", 3, "B", "harish.m@college.edu"),
        ("S10", "Pooja Joshi", "Computer Science", 2, "A", "pooja.j@college.edu")
    ]
    student_objs = {}
    for sid, name, dept, year, sec, email in students_data:
        s = Student(
            student_id=sid,
            name=name,
            department=dept,
            year=year,
            section=sec,
            email=email,
            enrollment_status="Active"
        )
        db.session.add(s)
        student_objs[sid] = s
    db.session.commit()

    # 4. Create Users (Admin, Faculty, Student)
    admin_user = User(
        username="admin",
        email="admin@smartattend.edu",
        role="admin"
    )
    admin_user.set_password("admin123")

    faculty_user = User(
        username="faculty",
        email="faculty@smartattend.edu",
        role="faculty",
        faculty_record_id=f1.id
    )
    faculty_user.set_password("faculty123")

    student_user = User(
        username="student",
        email="rahul.verma@college.edu",
        role="student",
        student_record_id=student_objs["S1"].id
    )
    student_user.set_password("student123")

    db.session.add_all([admin_user, faculty_user, student_user])
    db.session.commit()

    # 5. Create Enrollments and Attendance Records
    # Format: (student_id_code, course_obj, attended, total_conducted, remaining)
    attendance_data = [
        # S1: Shortage in CS101 (Recovery Impossible), Shortage in CS102 (Recovery Possible), Safe in CS103
        ("S1", c1, 30, 50, 20),  # 60%, shortage, needs 30, rem 20 -> IMPOSSIBLE
        ("S1", c2, 30, 50, 40),  # 60%, shortage, needs 30, rem 40 -> POSSIBLE
        ("S1", c5, 40, 45, 30),  # 88.89%, safe, needs 0 -> NOT REQUIRED

        # S2: CS101 Condonable
        ("S2", c1, 36, 50, 10),  # 72%, condonable, needs 6, rem 10 -> POSSIBLE
        ("S2", c2, 42, 50, 40),  # 84%, safe

        # S3: CS101 Safe
        ("S3", c1, 45, 50, 20),  # 90%, safe
        ("S3", c2, 38, 50, 40),  # 76%, safe

        # S4: EC201 Exact 75% boundary
        ("S4", c3, 45, 60, 25),  # 75.0%, safe boundary, needs 0

        # S5: IT301 Shortage 64%
        ("S5", c4, 32, 50, 15),  # 64%, shortage, needs 22, rem 15 -> IMPOSSIBLE

        # S6: CS101 Severe Shortage 50%
        ("S6", c1, 25, 50, 15),  # 50%, shortage, needs 50, rem 15 -> IMPOSSIBLE
        ("S6", c2, 35, 50, 40),  # 70%, condonable, needs 10, rem 40 -> POSSIBLE

        # S7: CS102 Condonable 68%
        ("S7", c2, 34, 50, 35),  # 68%, condonable, needs 14, rem 35 -> POSSIBLE

        # S8: EC201 Exact 65% boundary
        ("S8", c3, 39, 60, 20),  # 65.0%, condonable, needs 24, rem 20 -> IMPOSSIBLE

        # S9: IT301 Safe 84%
        ("S9", c4, 42, 50, 15),  # 84%, safe

        # S10: CS101 Safe 76%
        ("S10", c1, 38, 50, 20), # 76%, safe
    ]

    for sid_code, course_obj, att, tot, rem in attendance_data:
        s_obj = student_objs[sid_code]
        # Enrollment
        db.session.add(Enrollment(student_id=s_obj.id, course_id=course_obj.id))
        # Attendance Record
        db.session.add(AttendanceRecord(
            student_id=s_obj.id,
            course_id=course_obj.id,
            attended=att,
            total_conducted=tot,
            remaining_classes=rem,
            last_updated=datetime.now(timezone.utc)
        ))

    db.session.commit()

    # Generate initial notifications
    generate_system_notifications()
    print("[SmartAttend Seed] Successfully seeded sample dataset!")
    return True
