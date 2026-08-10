"""
QuizNova — Result Model
========================
Aggregated result record for a completed (submitted) quiz attempt.
One-to-one with QuizAttempt.
"""

from datetime import datetime
from models import db


class Result(db.Model):
    """
    Stores the computed result for a completed quiz attempt.
    Created atomically when a QuizAttempt is submitted.
    """

    __tablename__ = 'results'

    # -------------------------------------------------------------------------
    # Columns
    # -------------------------------------------------------------------------
    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    attempt_id      = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id',
                                ondelete='CASCADE', onupdate='CASCADE'),
                                nullable=False, unique=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id',
                                ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    subcategory_id  = db.Column(db.Integer, db.ForeignKey('subcategories.id',
                                ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    total_questions = db.Column(db.SmallInteger, nullable=False)
    correct_count   = db.Column(db.SmallInteger, nullable=False)
    wrong_count     = db.Column(db.SmallInteger, nullable=False)
    skipped_count   = db.Column(db.SmallInteger, nullable=False)
    score           = db.Column(db.Integer, nullable=False)       # Raw score
    max_score       = db.Column(db.Integer, nullable=False)       # Maximum possible
    percentage      = db.Column(db.Numeric(5, 2), nullable=False) # 0.00 – 100.00
    rank_at_time    = db.Column(db.Integer, nullable=True)        # Snapshot rank on submit
    is_passed       = db.Column(db.Boolean, nullable=False)
    created_at      = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------
    certificate = db.relationship('Certificate', backref='result', uselist=False,
                                   cascade='all, delete-orphan')

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def percentage_float(self) -> float:
        """Returns percentage as a Python float."""
        return float(self.percentage)

    @property
    def grade(self) -> str:
        """Returns letter grade based on percentage."""
        pct = self.percentage_float
        if pct >= 90:
            return 'A+'
        elif pct >= 80:
            return 'A'
        elif pct >= 70:
            return 'B'
        elif pct >= 60:
            return 'C'
        elif pct >= 50:
            return 'D'
        return 'F'

    @property
    def performance_level(self) -> str:
        """Returns a human-friendly performance label."""
        pct = self.percentage_float
        if pct >= 90:
            return 'Excellent'
        elif pct >= 75:
            return 'Good'
        elif pct >= 60:
            return 'Average'
        elif pct >= 40:
            return 'Below Average'
        return 'Poor'

    @property
    def performance_color(self) -> str:
        """Returns CSS color variable name for the performance level."""
        pct = self.percentage_float
        if pct >= 70:
            return 'success'
        elif pct >= 40:
            return 'warning'
        return 'error'

    @property
    def has_certificate(self) -> bool:
        """Returns True if a certificate has been generated for this result."""
        return self.certificate is not None

    # -------------------------------------------------------------------------
    # String Representation
    # -------------------------------------------------------------------------
    def __repr__(self) -> str:
        return (f'<Result id={self.id} user_id={self.user_id} '
                f'pct={self.percentage} passed={self.is_passed}>')
