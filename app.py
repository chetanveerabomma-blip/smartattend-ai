"""
SmartAttend AI — Intelligent Student Attendance Monitoring and Shortage Prediction System
Main Flask Application Entrypoint
"""

import os
from flask import Flask, render_template, session, g
from config import Config
from models import db, User, Student, Notification
from routes.auth_routes import auth_bp
from routes.dashboard_routes import dashboard_bp
from routes.student_routes import student_bp
from routes.course_routes import course_bp
from routes.attendance_routes import attendance_bp
from routes.report_routes import report_bp
from services.seed_service import seed_database_if_empty


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)

    # Register Blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(course_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(report_bp)

    # Global template context processor
    @app.context_processor
    def inject_global_vars():
        current_user = None
        unread_notifs = 0
        if 'user_id' in session:
            current_user = db.session.get(User, session['user_id'])
            unread_notifs = Notification.query.filter_by(is_read=False).count()
        return {
            'current_user': current_user,
            'unread_notifications_count': unread_notifs,
            'app_title': 'SmartAttend AI',
            'current_year': 2026
        }

    # Custom Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('500.html'), 500

    @app.errorhandler(403)
    def forbidden_error(e):
        return render_template('403.html'), 403

    # Database initialization & seeding within application context
    with app.app_context():
        # Ensure uploads folder exists
        os.makedirs(app.config.get('UPLOAD_FOLDER', 'uploads'), exist_ok=True)
        # Create tables
        db.create_all()
        # Seed initial dataset if database is empty
        seed_database_if_empty()

    return app


app = create_app()

if __name__ == '__main__':
    print("=" * 60)
    print("[*] SmartAttend AI Server Starting...")
    print("[*] URL: http://127.0.0.1:5000")
    print("[*] Demo Logins:")
    print("   - Administrator: admin / admin123")
    print("   - Faculty:       faculty / faculty123")
    print("   - Student:       student / student123")
    print("=" * 60)
    app.run(host='127.0.0.1', port=5000, debug=True)
