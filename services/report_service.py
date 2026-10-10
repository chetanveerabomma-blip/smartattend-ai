"""
SmartAttend AI - Report Service
Provides rich multi-criteria filtering, report type presets, and CSV export generation.
"""

import io
import csv
from typing import Dict, Any, List
from models import AttendanceRecord, Student, Course


def get_filtered_attendance_records(
    report_type: str = 'all',
    search_query: str = '',
    course_id: str = '',
    department: str = '',
    status_filter: str = '',
    feasibility_filter: str = '',
    min_pct: float = None,
    max_pct: float = None,
    sort_by: str = 'student_id',
    sort_dir: str = 'asc'
) -> List[Dict[str, Any]]:
    """
    Applies comprehensive filtering and returns serialized attendance records.
    """
    # Start with all records
    query = AttendanceRecord.query.join(Student).join(Course)

    if course_id:
        query = query.filter(Course.course_id == course_id)
        
    if department:
        query = query.filter(Student.department == department)

    if search_query:
        term = f"%{search_query}%"
        query = query.filter(
            (Student.student_id.ilike(term)) |
            (Student.name.ilike(term)) |
            (Course.course_id.ilike(term)) |
            (Course.course_name.ilike(term))
        )

    records = query.all()
    filtered_results = []

    for r in records:
        eval_data = r.evaluation
        pct = eval_data['percentage']
        status = eval_data['status']
        feasibility = eval_data['feasibility']

        # Apply report type presets
        if report_type == 'below_75' and pct >= 75.0:
            continue
        elif report_type == 'below_65' and pct >= 65.0:
            continue
        elif report_type == 'condonable' and status != 'CONDONABLE':
            continue
        elif report_type == 'impossible_recovery' and feasibility != 'IMPOSSIBLE':
            continue

        # Explicit dropdown filters
        if status_filter and status != status_filter:
            continue
        if feasibility_filter and feasibility != feasibility_filter:
            continue
        if min_pct is not None and pct < min_pct:
            continue
        if max_pct is not None and pct > max_pct:
            continue

        filtered_results.append(r.to_dict())

    # Sorting
    reverse = (sort_dir.lower() == 'desc')
    if sort_by == 'percentage':
        filtered_results.sort(key=lambda x: x['percentage'], reverse=reverse)
    elif sort_by == 'student_name':
        filtered_results.sort(key=lambda x: x['student_name'].lower(), reverse=reverse)
    elif sort_by == 'course_code':
        filtered_results.sort(key=lambda x: x['course_code'].lower(), reverse=reverse)
    elif sort_by == 'status':
        filtered_results.sort(key=lambda x: x['status'], reverse=reverse)
    elif sort_by == 'required_recovery':
        filtered_results.sort(key=lambda x: x['required_recovery'], reverse=reverse)
    else:  # default student_id
        filtered_results.sort(key=lambda x: x['student_code'].lower(), reverse=reverse)

    return filtered_results


def generate_attendance_report_csv(records: List[Dict[str, Any]]) -> str:
    """
    Generates a RFC 4180 compliant CSV string from evaluated attendance records.
    """
    output = io.StringIO()
    writer = csv.writer(output)

    # Headers
    writer.writerow([
        "StudentID",
        "StudentName",
        "Department",
        "Year",
        "Section",
        "CourseID",
        "CourseName",
        "AttendedClasses",
        "TotalConducted",
        "RemainingClasses",
        "AttendancePercentage",
        "AttendanceStatus",
        "RequiredClassesTo75",
        "RecoveryFeasibility",
        "GuidanceMessage"
    ])

    for r in records:
        writer.writerow([
            r['student_code'],
            r['student_name'],
            r['student_dept'],
            r['student_year'],
            r['student_section'],
            r['course_code'],
            r['course_name'],
            r['attended'],
            r['total_conducted'],
            r['remaining_classes'],
            f"{r['percentage']:.2f}%",
            r['status_label'],
            r['required_recovery'],
            r['feasibility_label'],
            r['guidance_message']
        ])

    return output.getvalue()
