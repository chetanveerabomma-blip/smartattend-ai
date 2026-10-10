from datetime import datetime, timezone
from . import db


class ImportJob(db.Model):
    __tablename__ = 'import_jobs'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.String(64), unique=True, nullable=False, index=True)
    filename = db.Column(db.String(255), nullable=False)
    import_mode = db.Column(db.String(30), nullable=False, default='snapshot')  # 'snapshot' or 'aggregate'
    
    total_rows = db.Column(db.Integer, default=0)
    processed_rows = db.Column(db.Integer, default=0)
    valid_rows = db.Column(db.Integer, default=0)
    invalid_rows = db.Column(db.Integer, default=0)
    
    status = db.Column(db.String(30), default='pending')  # 'pending', 'processing', 'completed', 'failed'
    summary_text = db.Column(db.Text, nullable=True)
    error_details = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    completed_at = db.Column(db.DateTime, nullable=True)

    def to_dict(self):
        return {
            "id": self.id,
            "job_id": self.job_id,
            "filename": self.filename,
            "import_mode": self.import_mode,
            "total_rows": self.total_rows,
            "processed_rows": self.processed_rows,
            "valid_rows": self.valid_rows,
            "invalid_rows": self.invalid_rows,
            "status": self.status,
            "summary_text": self.summary_text or "",
            "error_details": self.error_details or "",
            "created_at": self.created_at.strftime('%Y-%m-%d %H:%M:%S') if self.created_at else "",
            "completed_at": self.completed_at.strftime('%Y-%m-%d %H:%M:%S') if self.completed_at else ""
        }

    def __repr__(self):
        return f"<ImportJob {self.job_id} ({self.status})>"
