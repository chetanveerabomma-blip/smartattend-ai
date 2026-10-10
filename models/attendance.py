from datetime import datetime, timezone
from . import db
from services.recovery_service import evaluate_recovery_feasibility


class AttendanceRecord(db.Model):
    __tablename__ = 'attendance_records'

    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id', ondelete='CASCADE'), nullable=False, index=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.id', ondelete='CASCADE'), nullable=False, index=True)
    
    attended = db.Column(db.Integer, nullable=False, default=0)
    total_conducted = db.Column(db.Integer, nullable=False, default=0)
    remaining_classes = db.Column(db.Integer, nullable=False, default=0)
    
    last_updated = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='uq_student_course_attendance'),
    )

    @property
    def evaluation(self):
        """Returns the full evaluation dictionary computed by recovery_service."""
        return evaluate_recovery_feasibility(
            attended=self.attended,
            total=self.total_conducted,
            remaining=self.remaining_classes
        )

    @property
    def percentage(self) -> float:
        return self.evaluation['percentage']

    @property
    def status(self) -> str:
        return self.evaluation['status']

    @property
    def status_label(self) -> str:
        return self.evaluation['status_label']

    @property
    def status_badge(self) -> str:
        return self.evaluation['status_badge']

    @property
    def required_recovery(self) -> int:
        return self.evaluation['required_classes']

    @property
    def feasibility(self) -> str:
        return self.evaluation['feasibility']

    @property
    def feasibility_label(self) -> str:
        return self.evaluation['feasibility_label']

    @property
    def feasibility_badge(self) -> str:
        return self.evaluation['feasibility_badge']

    @property
    def guidance_message(self) -> str:
        return self.evaluation['message']

    def to_dict(self):
        eval_data = self.evaluation
        return {
            "id": self.id,
            "student_pk": self.student_id,
            "student_code": self.student.student_id if self.student else "",
            "student_name": self.student.name if self.student else "",
            "student_dept": self.student.department if self.student else "",
            "student_year": self.student.year if self.student else 1,
            "student_section": self.student.section if self.student else "A",
            "course_pk": self.course_id,
            "course_code": self.course.course_id if self.course else "",
            "course_name": self.course.course_name if self.course else "",
            "attended": self.attended,
            "total_conducted": self.total_conducted,
            "remaining_classes": self.remaining_classes,
            "percentage": eval_data["percentage"],
            "status": eval_data["status"],
            "status_label": eval_data["status_label"],
            "status_badge": eval_data["status_badge"],
            "required_recovery": eval_data["required_classes"],
            "feasibility": eval_data["feasibility"],
            "feasibility_label": eval_data["feasibility_label"],
            "feasibility_badge": eval_data["feasibility_badge"],
            "guidance_message": eval_data["message"],
            "projected_max_percentage": eval_data["projected_max_percentage"],
            "last_updated": self.last_updated.strftime('%Y-%m-%d %H:%M') if self.last_updated else ""
        }

    def __repr__(self):
        return f"<AttendanceRecord S:{self.student_id} C:{self.course_id} {self.attended}/{self.total_conducted}>"
