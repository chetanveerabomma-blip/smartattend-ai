"""
SmartAttend AI - Attendance Management Routes
Core module for single record entry, updates, CSV streaming batch uploads,
and template downloads.
"""

import os
from datetime import datetime, timezone
from flask import (
    Blueprint, render_template, request, redirect, url_for,
    flash, send_file, current_app, jsonify
)
from werkzeug.utils import secure_filename
from routes.auth_routes import faculty_or_admin_required
from models import db, AttendanceRecord, Student, Course, Enrollment, ImportJob
from services.import_service import process_attendance_csv_stream
from services.attendance_service import generate_system_notifications

attendance_bp = Blueprint('attendance', __name__)


@attendance_bp.route('/attendance')
@faculty_or_admin_required
def manage_attendance():
    course_id = request.args.get('course_id', type=int)
    search = request.args.get('search', '').strip()

    query = AttendanceRecord.query.join(Student).join(Course)

    if course_id:
        query = query.filter(AttendanceRecord.course_id == course_id)
    if search:
        term = f"%{search}%"
        query = query.filter(
            (Student.student_id.ilike(term)) |
            (Student.name.ilike(term)) |
            (Course.course_id.ilike(term))
        )

    records = query.order_by(Course.course_id, Student.student_id).all()
    all_courses = Course.query.order_by(Course.course_id).all()
    all_students = Student.query.order_by(Student.student_id).all()
    recent_jobs = ImportJob.query.order_by(ImportJob.created_at.desc()).limit(5).all()

    return render_template(
        'attendance.html',
        records=records,
        courses=all_courses,
        students=all_students,
        selected_course_id=course_id,
        search=search,
        recent_jobs=recent_jobs
    )


@attendance_bp.route('/attendance/save', methods=['POST'])
@faculty_or_admin_required
def save_attendance():
    """
    Saves or updates a single attendance record with rigorous Python validation.
    """
    student_pk = request.form.get('student_id', type=int)
    course_pk = request.form.get('course_id', type=int)
    attended = request.form.get('attended', type=int)
    total_conducted = request.form.get('total_conducted', type=int)
    remaining_classes = request.form.get('remaining_classes', 0, type=int)

    if not student_pk or not course_pk:
        flash("Student and Course must be selected.", "danger")
        return redirect(url_for('attendance.manage_attendance'))

    if attended is None or total_conducted is None or remaining_classes is None:
        flash("All numerical attendance values must be provided.", "danger")
        return redirect(url_for('attendance.manage_attendance'))

    # Validation checks
    if attended < 0 or total_conducted < 0 or remaining_classes < 0:
        flash("Validation Error: Attendance numbers cannot be negative.", "danger")
        return redirect(url_for('attendance.manage_attendance'))

    if attended > total_conducted:
        flash(f"Validation Error: Attended classes ({attended}) cannot exceed total classes conducted ({total_conducted}).", "danger")
        return redirect(url_for('attendance.manage_attendance'))

    student = Student.query.get_or_404(student_pk)
    course = Course.query.get_or_404(course_pk)

    # Ensure enrollment exists
    enrollment = Enrollment.query.filter_by(student_id=student.id, course_id=course.id).first()
    if not enrollment:
        db.session.add(Enrollment(student_id=student.id, course_id=course.id))

    record = AttendanceRecord.query.filter_by(student_id=student.id, course_id=course.id).first()
    if record:
        record.attended = attended
        record.total_conducted = total_conducted
        record.remaining_classes = remaining_classes
        record.last_updated = datetime.now(timezone.utc)
        flash(f"Updated attendance for {student.name} in {course.course_id} ({record.percentage}%).", "success")
    else:
        record = AttendanceRecord(
            student_id=student.id,
            course_id=course.id,
            attended=attended,
            total_conducted=total_conducted,
            remaining_classes=remaining_classes,
            last_updated=datetime.now(timezone.utc)
        )
        db.session.add(record)
        flash(f"Created attendance record for {student.name} in {course.course_id}.", "success")

    db.session.commit()
    generate_system_notifications()

    return redirect(url_for('attendance.manage_attendance', course_id=course.id))


@attendance_bp.route('/attendance/upload', methods=['POST'])
@faculty_or_admin_required
def upload_csv():
    """
    Handles streaming CSV upload with mode selection ('snapshot' vs 'aggregate').
    """
    if 'csv_file' not in request.files:
        flash("No CSV file selected for upload.", "danger")
        return redirect(url_for('attendance.manage_attendance'))

    file = request.files['csv_file']
    if file.filename == '':
        flash("No file was selected.", "danger")
        return redirect(url_for('attendance.manage_attendance'))

    if not file.filename.lower().endswith('.csv'):
        flash("Unsupported file format. Please upload a valid .csv file.", "danger")
        return redirect(url_for('attendance.manage_attendance'))

    import_mode = request.form.get('import_mode', 'snapshot')
    if import_mode not in ['snapshot', 'aggregate']:
        import_mode = 'snapshot'

    filename = secure_filename(file.filename)

    # Process via streaming service
    result = process_attendance_csv_stream(
        file_stream=file.stream,
        filename=filename,
        import_mode=import_mode,
        batch_size=500
    )

    if result.get("success"):
        flash(
            f"CSV Processed Successfully ({import_mode.title()} Mode)! "
            f"Total Rows: {result['total_rows']} | Valid: {result['valid_rows']} | "
            f"Created: {result['created_count']} | Updated: {result['updated_count']}",
            "success"
        )
        if result['invalid_rows'] > 0:
            flash(
                f"Notice: {result['invalid_rows']} invalid rows encountered. First error: {result['error_log'][0]}",
                "warning"
            )
        generate_system_notifications()
    else:
        flash(f"Error processing CSV: {result.get('error', 'Unknown error')}", "danger")

    return redirect(url_for('attendance.manage_attendance'))


@attendance_bp.route('/attendance/template')
@faculty_or_admin_required
def download_template():
    """Download attendance CSV template"""
    template_path = os.path.join(current_app.root_path, 'data', 'attendance_template.csv')
    return send_file(
        template_path,
        as_attachment=True,
        download_name="smartattend_template.csv",
        mimetype="text/csv"
    )


@attendance_bp.route('/attendance/sample-data')
@faculty_or_admin_required
def download_sample():
    """Download sample attendance dataset for immediate test upload"""
    sample_path = os.path.join(current_app.root_path, 'data', 'sample_attendance.csv')
    return send_file(
        sample_path,
        as_attachment=True,
        download_name="smartattend_sample_dataset.csv",
        mimetype="text/csv"
    )
