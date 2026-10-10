from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

from .user import User
from .student import Student
from .faculty import Faculty
from .course import Course
from .enrollment import Enrollment
from .attendance import AttendanceRecord
from .notification import Notification
from .import_job import ImportJob

__all__ = [
    'db',
    'User',
    'Student',
    'Faculty',
    'Course',
    'Enrollment',
    'AttendanceRecord',
    'Notification',
    'ImportJob'
]
