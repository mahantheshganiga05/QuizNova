"""
QuizNova — Email Log Model
===========================
Tracks all sent, queued, and failed email notifications for auditing and idempotency.
"""

from datetime import datetime
from models import db


class EmailLog(db.Model):
    """
    Log record for email dispatches to track status, idempotency, and audit trail.
    """

    __tablename__ = 'email_logs'

    id                = db.Column(db.Integer, primary_key=True, autoincrement=True)
    recipient         = db.Column(db.String(255), nullable=False, index=True)
    notification_type = db.Column(db.String(100), nullable=False, index=True)
    subject           = db.Column(db.String(255), nullable=False)
    status            = db.Column(db.String(50), nullable=False, default='QUEUED')  # QUEUED, SENT, FAILED
    sent_at           = db.Column(db.DateTime, nullable=True)
    error_message     = db.Column(db.Text, nullable=True)
    related_object_id = db.Column(db.String(100), nullable=True)
    event_key         = db.Column(db.String(255), unique=True, nullable=True, index=True)
    created_at        = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<EmailLog id={self.id} recipient={self.recipient!r} type={self.notification_type!r} status={self.status!r}>'
