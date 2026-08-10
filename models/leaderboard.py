"""
QuizNova — Leaderboard Cache Model
=====================================
Separate file for LeaderboardCache to avoid circular imports.
"""

from datetime import datetime
from models import db


class LeaderboardCache(db.Model):
    """
    Denormalized leaderboard scores for fast retrieval.
    subcategory_id=None → global leaderboard entry.
    Refreshed on every quiz submission via services/leaderboard.py.
    """

    __tablename__ = 'leaderboard_cache'

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id',
                                ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    subcategory_id  = db.Column(db.Integer, db.ForeignKey('subcategories.id',
                                ondelete='CASCADE', onupdate='CASCADE'), nullable=True)
    total_score     = db.Column(db.Integer, nullable=False, default=0)
    quiz_count      = db.Column(db.Integer, nullable=False, default=0)
    best_percentage = db.Column(db.Numeric(5, 2), nullable=False, default=0.00)
    rank_position   = db.Column(db.Integer, nullable=True)
    updated_at      = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                                onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'subcategory_id', name='uq_lb_user_sub'),
        db.Index('idx_lb_sub_score', 'subcategory_id', 'total_score'),
    )

    def __repr__(self) -> str:
        scope = f'sub={self.subcategory_id}' if self.subcategory_id else 'global'
        return f'<LeaderboardCache user_id={self.user_id} {scope} score={self.total_score}>'
