"""
QuizNova — Subcategory Model
=============================
Represents topic subdivisions within a Category (e.g., Python within Programming).
Contains quiz configuration: question count, time limit, pass threshold.
"""

from datetime import datetime
from models import db


class Subcategory(db.Model):
    """
    Subcategory (e.g., Python, Java) within a parent Category.
    Holds quiz configuration for that topic.
    """

    __tablename__ = 'subcategories'

    # -------------------------------------------------------------------------
    # Columns
    # -------------------------------------------------------------------------
    id                 = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id        = db.Column(db.Integer, db.ForeignKey('categories.id',
                                   ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    name               = db.Column(db.String(100), nullable=False)
    slug               = db.Column(db.String(100), nullable=False)
    description        = db.Column(db.Text, nullable=True)
    icon               = db.Column(db.String(255), nullable=True)
    questions_per_quiz = db.Column(db.SmallInteger, nullable=False, default=20)
    time_limit_minutes = db.Column(db.SmallInteger, nullable=False, default=30)
    pass_threshold     = db.Column(db.SmallInteger, nullable=False, default=60)  # Percentage
    difficulty_default = db.Column(db.Enum('easy', 'medium', 'hard', name='subcat_difficulty_enum'),
                                   nullable=False, default='medium')
    sort_order         = db.Column(db.Integer, nullable=False, default=0)
    is_active          = db.Column(db.Boolean, nullable=False, default=True)
    created_at         = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at         = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                                   onupdate=datetime.utcnow)

    # -------------------------------------------------------------------------
    # Unique Constraint: category_id + slug must be unique
    # -------------------------------------------------------------------------
    __table_args__ = (
        db.UniqueConstraint('category_id', 'slug', name='uq_sub_cat_slug'),
    )

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------
    questions     = db.relationship('Question', backref='subcategory', lazy='dynamic',
                                    cascade='all, delete-orphan')
    quiz_attempts = db.relationship('QuizAttempt', backref='subcategory', lazy='dynamic')

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def active_question_count(self) -> int:
        """Returns count of active questions available in this subcategory."""
        return self.questions.filter_by(is_active=True).count()

    @property
    def has_enough_questions(self) -> bool:
        """Returns True if subcategory has at least 1 active question available."""
        return self.active_question_count >= 1

    @property
    def time_limit_seconds(self) -> int:
        """Returns time limit in seconds for use in JS timer."""
        return self.time_limit_minutes * 60

    @property
    def icon_url(self) -> str:
        """Returns icon URL or default."""
        if self.icon:
            return f'/static/icons/categories/{self.icon}'
        return '/static/icons/categories/default.svg'

    # -------------------------------------------------------------------------
    # String Representation
    # -------------------------------------------------------------------------
    def __repr__(self) -> str:
        return f'<Subcategory id={self.id} name={self.name!r} category_id={self.category_id}>'
