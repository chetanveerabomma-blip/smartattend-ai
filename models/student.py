from datetime import datetime, timezone
from . import db


class Student(db.Model):
    __tablename__ = 'students'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    department = db.Column(db.String(100), nullable=False, index=True)
    year = db.Column(db.Integer, nullable=False, default=1)
    section = db.Column(db.String(10), nullable=False, default='A')
    email = db.Column(db.String(120), unique=True, nullable=False)
    enrollment_status = db.Column(db.String(20), nullable=False, default='Active')  # Active, Inactive, Suspended
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    attendance_records = db.relationship('AttendanceRecord', backref='student', cascade='all, delete-orphan', lazy=True)
    enrollments = db.relationship('Enrollment', backref='student', cascade='all, delete-orphan', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "student_id": self.student_id,
            "name": self.name,
            "department": self.department,
            "year": self.year,
            "section": self.section,
            "email": self.email,
            "enrollment_status": self.enrollment_status,
            "created_at": self.created_at.strftime('%Y-%m-%d') if self.created_at else ''
        }

    def __repr__(self):
        return f"<Student {self.student_id} - {self.name}>"
