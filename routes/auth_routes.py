"""
SmartAttend AI - Authentication & Authorization Routes
Provides role-based access control (RBAC), secure password verification,
and 1-click demo logins.
"""

from functools import wraps
from flask import Blueprint, render_template, request, redirect, url_for, flash, session, g
from models import User, Student

auth_bp = Blueprint('auth', __name__)


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for('auth.login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


def role_required(*allowed_roles):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if 'user_id' not in session:
                flash("Please log in to access this page.", "warning")
                return redirect(url_for('auth.login', next=request.path))
            
            user_role = session.get('role', 'student')
            if user_role not in allowed_roles:
                flash("Access denied: You do not have permission for this resource.", "danger")
                return redirect(url_for('dashboard.index'))
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def admin_required(f):
    return role_required('admin')(f)


def faculty_or_admin_required(f):
    return role_required('admin', 'faculty')(f)


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        if not username or not password:
            flash("Please enter both username and password.", "danger")
            return render_template('login.html')

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session.clear()
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            session['email'] = user.email
            session['student_record_id'] = user.student_record_id
            session['faculty_record_id'] = user.faculty_record_id

            flash(f"Welcome back, {user.username}! Signed in as {user.role.title()}.", "success")
            
            # If student role, redirect directly to student profile
            if user.role == 'student':
                return redirect(url_for('students.my_profile'))
            
            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for('dashboard.index'))
        else:
            flash("Invalid username or password. Please try again or use Demo Login.", "danger")

    return render_template('login.html')


@auth_bp.route('/demo-login/<role>', methods=['GET'])
def demo_login(role):
    """
    1-click demo login option clearly labeled for prototype evaluation.
    """
    role_map = {
        'admin': 'admin',
        'faculty': 'faculty',
        'student': 'student'
    }
    
    username = role_map.get(role.lower())
    if not username:
        flash("Invalid demo role specified.", "danger")
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(username=username).first()
    if not user:
        flash(f"Demo user '{username}' not found. Please restart to re-seed.", "danger")
        return redirect(url_for('auth.login'))

    session.clear()
    session['user_id'] = user.id
    session['username'] = user.username
    session['role'] = user.role
    session['email'] = user.email
    session['student_record_id'] = user.student_record_id
    session['faculty_record_id'] = user.faculty_record_id

    flash(f"Logged in as Demo {user.role.title()} ({user.username}).", "info")

    if user.role == 'student':
        return redirect(url_for('students.my_profile'))
    return redirect(url_for('dashboard.index'))


@auth_bp.route('/logout')
def logout():
    session.clear()
    flash("You have been signed out successfully.", "info")
    return redirect(url_for('auth.login'))
