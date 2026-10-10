"""
SmartAttend AI - Reports & Notification Routes
Generates multi-criteria reports, printable summaries, CSV exports, and alert tracking.
"""

from flask import Blueprint, render_template, request, Response, flash, redirect, url_for
from routes.auth_routes import login_required, faculty_or_admin_required
from models import db, Course, Student, Notification
from services.report_service import get_filtered_attendance_records, generate_attendance_report_csv
from services.attendance_service import get_course_wise_analytics

report_bp = Blueprint('reports', __name__)


@report_bp.route('/reports')
@faculty_or_admin_required
def generate_reports():
    report_type = request.args.get('report_type', 'all')
    search = request.args.get('search', '').strip()
    course_id = request.args.get('course_id', '').strip()
    department = request.args.get('dept', '').strip()
    status_filter = request.args.get('status', '').strip()
    feasibility_filter = request.args.get('feasibility', '').strip()
    
    min_pct = request.args.get('min_pct', type=float)
    max_pct = request.args.get('max_pct', type=float)
    sort_by = request.args.get('sort_by', 'student_id')
    sort_dir = request.args.get('sort_dir', 'asc')

    records = get_filtered_attendance_records(
        report_type=report_type,
        search_query=search,
        course_id=course_id,
        department=department,
        status_filter=status_filter,
        feasibility_filter=feasibility_filter,
        min_pct=min_pct,
        max_pct=max_pct,
        sort_by=sort_by,
        sort_dir=sort_dir
    )

    all_courses = Course.query.order_by(Course.course_id).all()
    departments = [d[0] for d in db.session.query(Student.department).distinct().all()]
    course_summaries = get_course_wise_analytics()

    return render_template(
        'reports.html',
        records=records,
        courses=all_courses,
        departments=departments,
        course_summaries=course_summaries,
        report_type=report_type,
        search=search,
        selected_course=course_id,
        selected_dept=department,
        selected_status=status_filter,
        selected_feasibility=feasibility_filter,
        min_pct=min_pct,
        max_pct=max_pct,
        sort_by=sort_by,
        sort_dir=sort_dir,
        total_results=len(records)
    )


@report_bp.route('/reports/export')
@faculty_or_admin_required
def export_report_csv():
    report_type = request.args.get('report_type', 'all')
    search = request.args.get('search', '').strip()
    course_id = request.args.get('course_id', '').strip()
    department = request.args.get('dept', '').strip()
    status_filter = request.args.get('status', '').strip()
    feasibility_filter = request.args.get('feasibility', '').strip()
    
    min_pct = request.args.get('min_pct', type=float)
    max_pct = request.args.get('max_pct', type=float)
    sort_by = request.args.get('sort_by', 'student_id')
    sort_dir = request.args.get('sort_dir', 'asc')

    records = get_filtered_attendance_records(
        report_type=report_type,
        search_query=search,
        course_id=course_id,
        department=department,
        status_filter=status_filter,
        feasibility_filter=feasibility_filter,
        min_pct=min_pct,
        max_pct=max_pct,
        sort_by=sort_by,
        sort_dir=sort_dir
    )

    csv_data = generate_attendance_report_csv(records)
    filename = f"smartattend_report_{report_type}.csv"

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={filename}"}
    )


@report_bp.route('/notifications')
@login_required
def list_notifications():
    severity_filter = request.args.get('severity')
    query = Notification.query
    if severity_filter:
        query = query.filter_by(severity=severity_filter)
        
    notifications = query.order_by(Notification.created_at.desc()).all()
    unread_count = Notification.query.filter_by(is_read=False).count()

    return render_template(
        'notifications.html',
        notifications=notifications,
        unread_count=unread_count,
        severity_filter=severity_filter
    )


@report_bp.route('/notifications/mark-read/<int:id>', methods=['POST', 'GET'])
@login_required
def mark_read(id):
    notif = Notification.query.get_or_404(id)
    notif.is_read = True
    db.session.commit()
    flash("Notification marked as read.", "info")
    return redirect(url_for('reports.list_notifications'))


@report_bp.route('/notifications/mark-all-read', methods=['POST', 'GET'])
@login_required
def mark_all_read():
    Notification.query.update({Notification.is_read: True})
    db.session.commit()
    flash("All notifications marked as read.", "success")
    return redirect(url_for('reports.list_notifications'))
