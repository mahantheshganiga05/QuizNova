"""
QuizNova — Question Model
==========================
Represents a single quiz question with 4 options, correct answer,
difficulty level, explanation, and topic tags.
"""

from datetime import datetime
from models import db


class Question(db.Model):
    """
    A quiz question with 4 MCQ options and a correct answer.
    Questions belong to a Subcategory and feed the quiz randomizer.
    """

    __tablename__ = 'questions'

    # -------------------------------------------------------------------------
    # Columns
    # -------------------------------------------------------------------------
    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('subcategories.id',
                               ondelete='RESTRICT', onupdate='CASCADE'), nullable=False)
    question_text  = db.Column(db.Text, nullable=False)
    option_a       = db.Column(db.String(500), nullable=False)
    option_b       = db.Column(db.String(500), nullable=False)
    option_c       = db.Column(db.String(500), nullable=False)
    option_d       = db.Column(db.String(500), nullable=False)
    correct_option = db.Column(db.Enum('a', 'b', 'c', 'd', name='correct_option_enum'), nullable=False)
    explanation    = db.Column(db.Text, nullable=True)
    difficulty     = db.Column(db.Enum('easy', 'medium', 'hard', name='question_difficulty_enum'),
                               nullable=False, default='medium')
    tags           = db.Column(db.String(255), nullable=True)  # Comma-separated topic tags
    is_active      = db.Column(db.Boolean, nullable=False, default=True)
    created_by     = db.Column(db.Integer, db.ForeignKey('users.id',
                               ondelete='SET NULL', onupdate='CASCADE'), nullable=True)
    created_at     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                               onupdate=datetime.utcnow)

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def options_list(self) -> list:
        """
        Returns the four options as a list in order [A, B, C, D].
        Used by the randomizer to shuffle options.
        """
        return [self.option_a, self.option_b, self.option_c, self.option_d]

    @property
    def correct_option_text(self) -> str:
        """Returns the text of the correct option."""
        option_map = {
            'a': self.option_a,
            'b': self.option_b,
            'c': self.option_c,
            'd': self.option_d,
        }
        return option_map.get(self.correct_option, '')

    @property
    def correct_option_index(self) -> int:
        """Returns 0-based index of the correct option (a=0, b=1, c=2, d=3)."""
        return {'a': 0, 'b': 1, 'c': 2, 'd': 3}.get(self.correct_option, 0)

    @property
    def tags_list(self) -> list:
        """Returns tags as a Python list. Returns empty list if no tags."""
        if not self.tags:
            return []
        return [tag.strip() for tag in self.tags.split(',') if tag.strip()]

    @property
    def difficulty_label(self) -> str:
        """Returns capitalized difficulty label for display."""
        return self.difficulty.capitalize() if self.difficulty else 'Medium'

    @property
    def difficulty_color(self) -> str:
        """Returns a CSS class suffix based on difficulty."""
        colors = {'easy': 'success', 'medium': 'warning', 'hard': 'error'}
        return colors.get(self.difficulty, 'warning')

    # -------------------------------------------------------------------------
    # String Representation
    # -------------------------------------------------------------------------
    def __repr__(self) -> str:
        preview = self.question_text[:40] + '...' if len(self.question_text) > 40 else self.question_text
        return f'<Question id={self.id} sub={self.subcategory_id} diff={self.difficulty!r} text={preview!r}>'
