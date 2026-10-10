from datetime import datetime, timezone
from . import db


class Course(db.Model):
    __tablename__ = 'courses'

    id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    course_name = db.Column(db.String(150), nullable=False)
    department = db.Column(db.String(100), nullable=False, index=True)
    semester = db.Column(db.Integer, nullable=False, default=1)
    
    faculty_id = db.Column(db.Integer, db.ForeignKey('faculty.id', ondelete='SET NULL'), nullable=True)
    faculty_name = db.Column(db.String(120), nullable=True, default='Unassigned')
    
    total_conducted = db.Column(db.Integer, nullable=False, default=0)
    remaining_classes = db.Column(db.Integer, nullable=False, default=0)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    attendance_records = db.relationship('AttendanceRecord', backref='course', cascade='all, delete-orphan', lazy=True)
    enrollments = db.relationship('Enrollment', backref='course', cascade='all, delete-orphan', lazy=True)

    @property
    def enrolled_students_count(self) -> int:
        return len(self.enrollments)

    def to_dict(self):
        return {
            "id": self.id,
            "course_id": self.course_id,
            "course_name": self.course_name,
            "department": self.department,
            "semester": self.semester,
            "faculty_id": self.faculty_id,
            "faculty_name": self.faculty_name or 'Unassigned',
            "total_conducted": self.total_conducted,
            "remaining_classes": self.remaining_classes,
            "enrolled_count": self.enrolled_students_count
        }

    def __repr__(self):
        return f"<Course {self.course_id} - {self.course_name}>"
