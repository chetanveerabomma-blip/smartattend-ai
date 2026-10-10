"""
SmartAttend AI - Student Routes & Profile
Comprehensive student directory, profile views, CRUD actions, and What-If scenario simulations.
"""

import io
import csv
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session, Response
from routes.auth_routes import login_required, admin_required, faculty_or_admin_required
from models import db, Student, AttendanceRecord, Course, User
from services.recovery_service import simulate_attendance_scenario

student_bp = Blueprint('students', __name__)


@student_bp.route('/students')
@faculty_or_admin_required
def list_students():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    
    search = request.args.get('search', '').strip()
    dept = request.args.get('dept', '').strip()
    year = request.args.get('year', type=int)
    section_val = request.args.get('section', '').strip()
    
    query = Student.query
    
    if search:
        term = f"%{search}%"
        query = query.filter((Student.student_id.ilike(term)) | (Student.name.ilike(term)) | (Student.email.ilike(term)))
    if dept:
        query = query.filter(Student.department == dept)
    if year:
        query = query.filter(Student.year == year)
    if section_val:
        query = query.filter(Student.section == section_val)
        
    pagination = query.order_by(Student.student_id).paginate(page=page, per_page=per_page, error_out=False)
    students = pagination.items
    
    departments = [d[0] for d in db.session.query(Student.department).distinct().all()]

    return render_template(
        'students.html',
        students=students,
        pagination=pagination,
        search=search,
        selected_dept=dept,
        selected_year=year,
        selected_section=section_val,
        departments=departments
    )


@student_bp.route('/students/add', methods=['POST'])
@admin_required
def add_student():
    student_id = request.form.get('student_id', '').strip().upper()
    name = request.form.get('name', '').strip()
    department = request.form.get('department', '').strip()
    year = request.form.get('year', type=int)
    section_val = request.form.get('section', '').strip().upper()
    email = request.form.get('email', '').strip().lower()

    if not student_id or not name or not department or not year or not email:
        flash("All fields are required to register a student.", "danger")
        return redirect(url_for('students.list_students'))

    # Check duplicates
    if Student.query.filter_by(student_id=student_id).first():
        flash(f"Student ID '{student_id}' is already registered.", "danger")
        return redirect(url_for('students.list_students'))

    if Student.query.filter_by(email=email).first():
        flash(f"Email '{email}' is already in use.", "danger")
        return redirect(url_for('students.list_students'))

    new_student = Student(
        student_id=student_id,
        name=name,
        department=department,
        year=year,
        section=section_val or 'A',
        email=email,
        enrollment_status='Active'
    )
    db.session.add(new_student)
    db.session.commit()

    flash(f"Student {name} ({student_id}) added successfully.", "success")
    return redirect(url_for('students.list_students'))


@student_bp.route('/students/<int:id>/edit', methods=['POST'])
@admin_required
def edit_student(id):
    student = Student.query.get_or_404(id)
    
    name = request.form.get('name', '').strip()
    department = request.form.get('department', '').strip()
    year = request.form.get('year', type=int)
    section_val = request.form.get('section', '').strip().upper()
    email = request.form.get('email', '').strip().lower()
    status = request.form.get('enrollment_status', 'Active')

    if not name or not department or not year or not email:
        flash("Please fill in all required fields.", "danger")
        return redirect(url_for('students.list_students'))

    # Check email duplicate if changed
    existing = Student.query.filter(Student.email == email, Student.id != id).first()
    if existing:
        flash(f"Email '{email}' is already in use by another student.", "danger")
        return redirect(url_for('students.list_students'))

    student.name = name
    student.department = department
    student.year = year
    student.section = section_val
    student.email = email
    student.enrollment_status = status
    db.session.commit()

    flash(f"Updated record for {student.name} ({student.student_id}).", "success")
    return redirect(url_for('students.list_students'))


@student_bp.route('/students/<int:id>/delete', methods=['POST'])
@admin_required
def delete_student(id):
    student = Student.query.get_or_404(id)
    sid = student.student_id
    name = student.name
    
    db.session.delete(student)
    db.session.commit()

    flash(f"Student {name} ({sid}) and associated records deleted.", "info")
    return redirect(url_for('students.list_students'))


@student_bp.route('/students/export')
@faculty_or_admin_required
def export_students():
    students = Student.query.order_by(Student.student_id).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["StudentID", "Name", "Department", "Year", "Section", "Email", "EnrollmentStatus"])
    for s in students:
        writer.writerow([s.student_id, s.name, s.department, s.year, s.section, s.email, s.enrollment_status])
        
    return Response(
        output.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=smartattend_students.csv"}
    )


@student_bp.route('/student/profile')
@login_required
def my_profile():
    """Direct profile access for logged-in students or default S1"""
    student_record_id = session.get('student_record_id')
    if student_record_id:
        student = db.session.get(Student, student_record_id)
    else:
        # Fallback to S1
        student = Student.query.filter_by(student_id='S1').first()
        
    if not student:
        flash("Student record not found.", "warning")
        return redirect(url_for('dashboard.index'))
        
    return view_student_profile(student.id)


@student_bp.route('/students/<int:id>/profile')
@login_required
def view_student_profile(id):
    student = Student.query.get_or_404(id)
    records = AttendanceRecord.query.filter_by(student_id=student.id).all()
    
    # Calculate overall profile stats
    tot_attended = sum(r.attended for r in records)
    tot_conducted = sum(r.total_conducted for r in records)
    overall_pct = round((tot_attended / tot_conducted * 100.0), 2) if tot_conducted > 0 else 0.0
    
    shortages = sum(1 for r in records if r.status == 'SHORTAGE')
    condonables = sum(1 for r in records if r.status == 'CONDONABLE')
    safe_courses = sum(1 for r in records if r.status == 'OK')
    
    return render_template(
        'student_profile.html',
        student=student,
        records=records,
        overall_pct=overall_pct,
        tot_attended=tot_attended,
        tot_conducted=tot_conducted,
        shortages=shortages,
        condonables=condonables,
        safe_courses=safe_courses
    )


@student_bp.route('/api/simulate', methods=['POST'])
@login_required
def simulate_scenario():
    """
    Simulates attendance scenario without altering database records.
    """
    data = request.get_json() or {}
    record_id = data.get('record_id')
    attended_add = data.get('additional_attended', 0)
    missed_add = data.get('additional_missed', 0)
    
    try:
        attended_add = int(attended_add)
        missed_add = int(missed_add)
    except ValueError:
        return jsonify({"error": "Inputs must be valid integers"}), 400
        
    if attended_add < 0 or missed_add < 0:
        return jsonify({"error": "Additional class numbers cannot be negative"}), 400

    record = db.session.get(AttendanceRecord, record_id)
    if not record:
        return jsonify({"error": "Attendance record not found"}), 404

    result = simulate_attendance_scenario(
        attended=record.attended,
        total=record.total_conducted,
        additional_attended=attended_add,
        additional_missed=missed_add
    )
    
    return jsonify({
        "success": True,
        "course_code": record.course.course_id,
        "course_name": record.course.course_name,
        "simulation": result
    })
