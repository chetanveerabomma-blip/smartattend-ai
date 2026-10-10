from datetime import datetime, timezone
from . import db


class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    enrolled_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='uq_student_course_enrollment'),
    )

    def __repr__(self):
        return f"<Enrollment Student:{self.student_id} Course:{self.course_id}>"
