from datetime import datetime, timezone
from . import db


class Faculty(db.Model):
    __tablename__ = 'faculty'

    id = db.Column(db.Integer, primary_key=True)
    faculty_id = db.Column(db.String(50), unique=True, nullable=False, index=True)
    name = db.Column(db.String(120), nullable=False, index=True)
    department = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone = db.Column(db.String(30), nullable=True)
    office = db.Column(db.String(50), nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    # Relationships
    courses = db.relationship('Course', backref='assigned_faculty_rel', lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "faculty_id": self.faculty_id,
            "name": self.name,
            "department": self.department,
            "email": self.email,
            "phone": self.phone or '',
            "office": self.office or ''
        }

    def __repr__(self):
        return f"<Faculty {self.faculty_id} - {self.name}>"
