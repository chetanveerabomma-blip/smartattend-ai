from datetime import datetime, timezone
from . import db


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=True, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=True, index=True)
    
    severity = db.Column(db.String(20), nullable=False, default='warning')  # 'critical', 'warning', 'info', 'success'
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Optional relationships
    student = db.relationship('Student', backref=db.backref('notifications', cascade='all, delete-orphan', lazy=True))
    course = db.relationship('Course', backref=db.backref('notifications', cascade='all, delete-orphan', lazy=True))

    def to_dict(self):
        return {
            "id": self.id,
            "severity": self.severity,
            "title": self.title,
            "message": self.message,
            "is_read": self.is_read,
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else "",
            "student_id": self.student.student_id if self.student else None,
            "student_name": self.student.name if self.student else None,
            "course_id": self.course.course_id if self.course else None
        }

    def __repr__(self):
        return f"<Notification [{self.severity}] {self.title}>"
