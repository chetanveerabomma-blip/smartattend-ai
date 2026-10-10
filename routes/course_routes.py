"""
SmartAttend AI - Course Management Routes
Enables curriculum configuration, faculty assignments, and course attendance summaries.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from routes.auth_routes import faculty_or_admin_required, admin_required
from models import db, Course, Faculty, AttendanceRecord

course_bp = Blueprint('courses', __name__)


@course_bp.route('/courses')
@faculty_or_admin_required
def list_courses():
    search = request.args.get('search', '').strip()
    dept = request.args.get('dept', '').strip()
    semester = request.args.get('semester', type=int)

    query = Course.query

    if search:
        term = f"%{search}%"
        query = query.filter((Course.course_id.ilike(term)) | (Course.course_name.ilike(term)))
    if dept:
        query = query.filter(Course.department == dept)
    if semester:
        query = query.filter(Course.semester == semester)

    courses = query.order_by(Course.course_id).all()
    all_faculty = Faculty.query.order_by(Faculty.name).all()
    departments = [d[0] for d in db.session.query(Course.department).distinct().all()]

    return render_template(
        'courses.html',
        courses=courses,
        all_faculty=all_faculty,
        departments=departments,
        search=search,
        selected_dept=dept,
        selected_sem=semester
    )


@course_bp.route('/courses/add', methods=['POST'])
@admin_required
def add_course():
    course_id = request.form.get('course_id', '').strip().upper()
    course_name = request.form.get('course_name', '').strip()
    department = request.form.get('department', '').strip()
    semester = request.form.get('semester', type=int)
    faculty_id = request.form.get('faculty_id', type=int)
    total_conducted = request.form.get('total_conducted', 0, type=int)
    remaining_classes = request.form.get('remaining_classes', 0, type=int)

    if not course_id or not course_name or not department or not semester:
        flash("Please fill in all mandatory course fields.", "danger")
        return redirect(url_for('courses.list_courses'))

    if total_conducted < 0 or remaining_classes < 0:
        flash("Class counts cannot be negative.", "danger")
        return redirect(url_for('courses.list_courses'))

    if Course.query.filter_by(course_id=course_id).first():
        flash(f"Course ID '{course_id}' already exists.", "danger")
        return redirect(url_for('courses.list_courses'))

    faculty_obj = Faculty.query.get(faculty_id) if faculty_id else None
    faculty_name = faculty_obj.name if faculty_obj else "Unassigned"

    new_course = Course(
        course_id=course_id,
        course_name=course_name,
        department=department,
        semester=semester,
        faculty_id=faculty_id,
        faculty_name=faculty_name,
        total_conducted=total_conducted,
        remaining_classes=remaining_classes
    )
    db.session.add(new_course)
    db.session.commit()

    flash(f"Course {course_name} ({course_id}) created successfully.", "success")
    return redirect(url_for('courses.list_courses'))


@course_bp.route('/courses/<int:id>/edit', methods=['POST'])
@admin_required
def edit_course(id):
    course = Course.query.get_or_404(id)

    course_name = request.form.get('course_name', '').strip()
    department = request.form.get('department', '').strip()
    semester = request.form.get('semester', type=int)
    faculty_id = request.form.get('faculty_id', type=int)
    total_conducted = request.form.get('total_conducted', type=int)
    remaining_classes = request.form.get('remaining_classes', type=int)

    if not course_name or not department or not semester:
        flash("Please provide all required fields.", "danger")
        return redirect(url_for('courses.list_courses'))

    if total_conducted < 0 or remaining_classes < 0:
        flash("Class counts cannot be negative.", "danger")
        return redirect(url_for('courses.list_courses'))

    faculty_obj = Faculty.query.get(faculty_id) if faculty_id else None
    
    course.course_name = course_name
    course.department = department
    course.semester = semester
    course.faculty_id = faculty_id
    course.faculty_name = faculty_obj.name if faculty_obj else "Unassigned"
    course.total_conducted = total_conducted
    course.remaining_classes = remaining_classes

    # Synchronize remaining classes to attendance records for this course if requested
    sync_remaining = request.form.get('sync_remaining') == '1'
    if sync_remaining:
        for r in course.attendance_records:
            r.remaining_classes = remaining_classes
            r.total_conducted = total_conducted

    db.session.commit()
    flash(f"Course {course.course_id} updated successfully.", "success")
    return redirect(url_for('courses.list_courses'))


@course_bp.route('/courses/<int:id>/delete', methods=['POST'])
@admin_required
def delete_course(id):
    course = Course.query.get_or_404(id)
    cid = course.course_id
    db.session.delete(course)
    db.session.commit()
    flash(f"Course {cid} and linked records deleted.", "info")
    return redirect(url_for('courses.list_courses'))
