"""
SmartAttend AI - Attendance Service
Aggregates analytics, KPI statistics, and generates real-time system alerts.
"""

from typing import Dict, Any, List
from sqlalchemy import func
from models import db, Student, Course, AttendanceRecord, Notification


def get_dashboard_metrics(course_filter_id: int = None) -> Dict[str, Any]:
    """
    Computes real-time dashboard KPIs from actual database records.
    Supports optional course-level filtering.
    """
    query = AttendanceRecord.query
    if course_filter_id:
        query = query.filter(AttendanceRecord.course_id == course_filter_id)
        
    records = query.all()
    
    total_students = Student.query.count()
    total_courses = Course.query.count()
    total_records = len(records)
    
    safe_count = 0
    condonable_count = 0
    shortage_count = 0
    recovery_possible_count = 0
    recovery_impossible_count = 0
    
    sum_attended = 0
    sum_conducted = 0
    
    for r in records:
        sum_attended += r.attended
        sum_conducted += r.total_conducted
        
        status = r.status
        feasibility = r.feasibility
        
        if status == 'OK':
            safe_count += 1
        elif status == 'CONDONABLE':
            condonable_count += 1
        elif status == 'SHORTAGE':
            shortage_count += 1
            
        if feasibility == 'POSSIBLE':
            recovery_possible_count += 1
        elif feasibility == 'IMPOSSIBLE':
            recovery_impossible_count += 1
            
    overall_percentage = round((sum_attended / sum_conducted * 100.0), 2) if sum_conducted > 0 else 0.0
    
    return {
        "total_students": total_students,
        "total_courses": total_courses,
        "total_records": total_records,
        "safe_count": safe_count,
        "condonable_count": condonable_count,
        "shortage_count": shortage_count,
        "recovery_possible_count": recovery_possible_count,
        "recovery_impossible_count": recovery_impossible_count,
        "overall_percentage": overall_percentage,
        "total_attended_classes": sum_attended,
        "total_conducted_classes": sum_conducted
    }


def get_course_wise_analytics() -> List[Dict[str, Any]]:
    """
    Calculates course-by-course attendance averages and statistics for Chart.js.
    """
    courses = Course.query.all()
    results = []
    
    for course in courses:
        records = course.attendance_records
        total_students = len(records)
        
        if total_students > 0:
            total_att = sum(r.attended for r in records)
            total_cond = sum(r.total_conducted for r in records)
            avg_pct = round((total_att / total_cond * 100.0), 2) if total_cond > 0 else 0.0
            
            shortage_in_course = sum(1 for r in records if r.status == 'SHORTAGE')
            condonable_in_course = sum(1 for r in records if r.status == 'CONDONABLE')
            safe_in_course = sum(1 for r in records if r.status == 'OK')
        else:
            avg_pct = 0.0
            shortage_in_course = 0
            condonable_in_course = 0
            safe_in_course = 0
            
        results.append({
            "course_id": course.id,
            "course_code": course.course_id,
            "course_name": course.course_name,
            "department": course.department,
            "enrolled_students": total_students,
            "average_percentage": avg_pct,
            "safe_count": safe_in_course,
            "condonable_count": condonable_in_course,
            "shortage_count": shortage_in_course,
            "total_conducted": course.total_conducted,
            "remaining_classes": course.remaining_classes
        })
        
    return results


def get_lowest_attendance_students(limit: int = 7) -> List[Dict[str, Any]]:
    """
    Finds students with the lowest attendance percentages for the dashboard chart and alert table.
    """
    records = AttendanceRecord.query.all()
    # Sort by percentage ascending, total_conducted descending
    records_with_pct = [
        (r, r.percentage) for r in records if r.total_conducted > 0
    ]
    records_with_pct.sort(key=lambda x: x[1])
    
    lowest = []
    for r, pct in records_with_pct[:limit]:
        lowest.append({
            "record_id": r.id,
            "student_id": r.student.student_id,
            "student_name": r.student.name,
            "course_code": r.course.course_id,
            "course_name": r.course.course_name,
            "department": r.student.department,
            "attended": r.attended,
            "total": r.total_conducted,
            "percentage": pct,
            "status": r.status,
            "status_label": r.status_label,
            "status_badge": r.status_badge,
            "required_recovery": r.required_recovery,
            "feasibility": r.feasibility,
            "feasibility_badge": r.feasibility_badge
        })
        
    return lowest


def generate_system_notifications():
    """
    Scans attendance records and populates/refreshes notifications based on attendance status.
    Keeps alerts synchronized with current database records.
    """
    records = AttendanceRecord.query.all()
    existing_count = Notification.query.count()
    
    # If notifications exist, avoid endless duplication
    if existing_count > 30:
        return
        
    new_notifs = []
    for r in records:
        # Case 1: Recovery Impossible (Critical)
        if r.feasibility == 'IMPOSSIBLE':
            msg = (f"Student {r.student.name} ({r.student.student_id}) in {r.course.course_id} "
                   f"requires {r.required_recovery} classes to reach 75%, but only {r.remaining_classes} remain. "
                   f"Recovery is mathematically IMPOSSIBLE.")
            new_notifs.append(Notification(
                student_id=r.student_id,
                course_id=r.course_id,
                severity='critical',
                title=f"Impossible Recovery Alert: {r.student.student_id}",
                message=msg
            ))
        # Case 2: Shortage with possible recovery (Warning)
        elif r.status == 'SHORTAGE' and r.feasibility == 'POSSIBLE':
            msg = (f"Student {r.student.name} ({r.student.student_id}) has severe attendance shortage "
                   f"({r.percentage}% in {r.course.course_id}). Must attend next {r.required_recovery} consecutive classes.")
            new_notifs.append(Notification(
                student_id=r.student_id,
                course_id=r.course_id,
                severity='warning',
                title=f"Attendance Shortage Alert: {r.student.student_id}",
                message=msg
            ))
        # Case 3: Condonable boundary
        elif r.status == 'CONDONABLE':
            msg = (f"Student {r.student.name} ({r.student.student_id}) is in condonable range "
                   f"({r.percentage}% in {r.course.course_id}). Needs {r.required_recovery} more classes to achieve safe 75%.")
            new_notifs.append(Notification(
                student_id=r.student_id,
                course_id=r.course_id,
                severity='info',
                title=f"Condonable Range Alert: {r.student.student_id}",
                message=msg
            ))

    if new_notifs:
        # Only add up to 20 notifications to keep DB clean
        for n in new_notifs[:20]:
            # check if similar exists
            exists = Notification.query.filter_by(
                student_id=n.student_id,
                course_id=n.course_id,
                title=n.title
            ).first()
            if not exists:
                db.session.add(n)
        db.session.commit()
