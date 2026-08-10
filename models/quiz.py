"""
QuizNova — Quiz Models
=======================
Three related models managing the quiz lifecycle:
  - QuizAttempt: One session of a user taking a quiz
  - AttemptQuestion: Snapshot of questions shown (with shuffled options)
  - AttemptAnswer: User's response to each question
"""

import json
from datetime import datetime
from models import db


class QuizAttempt(db.Model):
    """
    Represents a single quiz session.
    Created when a user starts a quiz; updated on submission.
    """

    __tablename__ = 'quiz_attempts'

    STATUSES = ('in_progress', 'submitted', 'abandoned')

    # -------------------------------------------------------------------------
    # Columns
    # -------------------------------------------------------------------------
    id               = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id          = db.Column(db.Integer, db.ForeignKey('users.id',
                                 ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    subcategory_id   = db.Column(db.Integer, db.ForeignKey('subcategories.id',
                                 ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    status           = db.Column(db.Enum(*STATUSES, name='quiz_status_enum'), nullable=False, default='in_progress')
    started_at       = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    submitted_at     = db.Column(db.DateTime, nullable=True)
    time_taken_seconds = db.Column(db.Integer, nullable=True)
    violation_count  = db.Column(db.SmallInteger, nullable=False, default=0)
    auto_submitted   = db.Column(db.Boolean, nullable=False, default=False)
    ip_address       = db.Column(db.String(45), nullable=True)
    user_agent       = db.Column(db.String(255), nullable=True)
    created_at       = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------
    attempt_questions = db.relationship('AttemptQuestion', backref='attempt', lazy='dynamic',
                                        cascade='all, delete-orphan',
                                        order_by='AttemptQuestion.question_order')
    attempt_answers   = db.relationship('AttemptAnswer', backref='attempt', lazy='dynamic',
                                        cascade='all, delete-orphan')
    result            = db.relationship('Result', backref='attempt', uselist=False,
                                        cascade='all, delete-orphan')
    anti_cheat_logs   = db.relationship('AntiCheatLog', backref='attempt', lazy='dynamic',
                                        cascade='all, delete-orphan')

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def is_in_progress(self) -> bool:
        return self.status == 'in_progress'

    @property
    def is_submitted(self) -> bool:
        return self.status == 'submitted'

    @property
    def time_taken_display(self) -> str:
        """Format time_taken_seconds as MM:SS string."""
        if not self.time_taken_seconds:
            return '00:00'
        minutes = self.time_taken_seconds // 60
        seconds = self.time_taken_seconds % 60
        return f'{minutes:02d}:{seconds:02d}'

    # -------------------------------------------------------------------------
    # Methods
    # -------------------------------------------------------------------------
    def submit(self, auto: bool = False) -> None:
        """
        Mark the attempt as submitted.

        Args:
            auto: True if submitted by timer/violation, False if manual.
        """
        now = datetime.utcnow()
        self.status = 'submitted'
        self.submitted_at = now
        self.auto_submitted = auto
        if self.started_at:
            delta = now - self.started_at
            self.time_taken_seconds = int(delta.total_seconds())

    def increment_violation(self) -> int:
        """
        Increment violation counter by 1.

        Returns:
            New violation count after increment.
        """
        self.violation_count += 1
        return self.violation_count

    # -------------------------------------------------------------------------
    # String Representation
    # -------------------------------------------------------------------------
    def __repr__(self) -> str:
        return (f'<QuizAttempt id={self.id} user_id={self.user_id} '
                f'sub_id={self.subcategory_id} status={self.status!r}>')


class AttemptQuestion(db.Model):
    """
    Snapshot of a question as it appeared in a specific quiz attempt.
    Stores shuffled options and the new index of the correct answer.
    This preserves the exact state even if the original question changes later.
    """

    __tablename__ = 'attempt_questions'

    # -------------------------------------------------------------------------
    # Columns
    # -------------------------------------------------------------------------
    id                    = db.Column(db.Integer, primary_key=True, autoincrement=True)
    attempt_id            = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id',
                                      ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    question_id           = db.Column(db.Integer, db.ForeignKey('questions.id',
                                      ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    question_order        = db.Column(db.SmallInteger, nullable=False)  # 1-based display order
    shuffled_options      = db.Column(db.Text, nullable=False)  # JSON string
    correct_shuffled_index = db.Column(db.SmallInteger, nullable=False)  # 0-based index
    is_bookmarked         = db.Column(db.Boolean, nullable=False, default=False)

    # -------------------------------------------------------------------------
    # Unique constraint: question appears once per attempt
    # -------------------------------------------------------------------------
    __table_args__ = (
        db.UniqueConstraint('attempt_id', 'question_id', name='uq_aq_attempt_question'),
        db.Index('idx_aq_attempt_order', 'attempt_id', 'question_order'),
    )

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------
    question = db.relationship('Question', backref='attempt_instances', lazy='joined')
    answer   = db.relationship('AttemptAnswer', backref='attempt_question', uselist=False,
                               cascade='all, delete-orphan')

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def options(self) -> list:
        """Returns the shuffled options as a Python list."""
        try:
            return json.loads(self.shuffled_options)
        except (json.JSONDecodeError, TypeError):
            return []

    @options.setter
    def options(self, value: list) -> None:
        """Sets shuffled options from a Python list."""
        self.shuffled_options = json.dumps(value)

    # -------------------------------------------------------------------------
    # String Representation
    # -------------------------------------------------------------------------
    def __repr__(self) -> str:
        return (f'<AttemptQuestion id={self.id} attempt_id={self.attempt_id} '
                f'q_id={self.question_id} order={self.question_order}>')


class AttemptAnswer(db.Model):
    """
    Stores the user's selected option for a question in an attempt.
    selected_index is None if the question was skipped.
    """

    __tablename__ = 'attempt_answers'

    # -------------------------------------------------------------------------
    # Columns
    # -------------------------------------------------------------------------
    id                  = db.Column(db.Integer, primary_key=True, autoincrement=True)
    attempt_id          = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id',
                                    ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    attempt_question_id = db.Column(db.Integer, db.ForeignKey('attempt_questions.id',
                                    ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    selected_index      = db.Column(db.SmallInteger, nullable=True)  # 0-3 or None = skipped
    is_correct          = db.Column(db.Boolean, nullable=True)  # Computed on submission
    answered_at         = db.Column(db.DateTime, nullable=True)

    # -------------------------------------------------------------------------
    # Constraints
    # -------------------------------------------------------------------------
    __table_args__ = (
        db.UniqueConstraint('attempt_id', 'attempt_question_id', name='uq_aa_attempt_q'),
    )

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def is_skipped(self) -> bool:
        return self.selected_index is None

    @property
    def selected_option_label(self) -> str:
        """Returns 'A', 'B', 'C', 'D' or 'Skipped' for the selected index."""
        if self.selected_index is None:
            return 'Skipped'
        return ['A', 'B', 'C', 'D'][self.selected_index]

    # -------------------------------------------------------------------------
    # Methods
    # -------------------------------------------------------------------------
    def evaluate(self, correct_shuffled_index: int) -> None:
        """
        Determine if this answer is correct.

        Args:
            correct_shuffled_index: The 0-based index of the correct option
                                    in the shuffled options array.
        """
        if self.selected_index is None:
            self.is_correct = False
        else:
            self.is_correct = (self.selected_index == correct_shuffled_index)

    # -------------------------------------------------------------------------
    # String Representation
    # -------------------------------------------------------------------------
    def __repr__(self) -> str:
        return (f'<AttemptAnswer id={self.id} attempt_id={self.attempt_id} '
                f'selected={self.selected_index} correct={self.is_correct}>')
