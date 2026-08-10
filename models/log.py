"""
QuizNova — Supporting Models
=============================
Contains:
  - Achievement (master list)
  - AchievementEarned (user x achievement junction)
  - LeaderboardCache (denormalized rank scores)
  - ActivityLog (user event timeline)
  - AntiCheatLog (violation audit trail)
  - Settings (platform key-value config)
"""

import json
from datetime import datetime
from models import db


# =============================================================================
# Achievement Models
# =============================================================================

class Achievement(db.Model):
    """Master list of all possible achievements/badges."""

    __tablename__ = 'achievements'

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    code          = db.Column(db.String(50), nullable=False, unique=True)
    name          = db.Column(db.String(100), nullable=False)
    description   = db.Column(db.Text, nullable=False)
    icon          = db.Column(db.String(255), nullable=True)
    points        = db.Column(db.SmallInteger, nullable=False, default=0)
    trigger_type  = db.Column(db.String(50), nullable=False)
    trigger_value = db.Column(db.Integer, nullable=True)
    is_active     = db.Column(db.Boolean, nullable=False, default=True)

    earned_by = db.relationship('AchievementEarned', backref='achievement',
                                lazy='dynamic', cascade='all, delete-orphan')

    @property
    def icon_url(self) -> str:
        if self.icon:
            return f'/static/icons/badges/{self.icon}'
        return '/static/icons/badges/default.svg'

    def __repr__(self) -> str:
        return f'<Achievement code={self.code!r} name={self.name!r}>'


class AchievementEarned(db.Model):
    """Junction table: records when a user earns an achievement."""

    __tablename__ = 'achievements_earned'

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id',
                               ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id',
                               ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    earned_at      = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    context        = db.Column(db.Text, nullable=True)  # JSON string

    __table_args__ = (
        db.UniqueConstraint('user_id', 'achievement_id', name='uq_ae_user_ach'),
    )

    @property
    def context_dict(self) -> dict:
        """Returns context as a Python dict."""
        try:
            return json.loads(self.context) if self.context else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    @context_dict.setter
    def context_dict(self, value: dict) -> None:
        self.context = json.dumps(value) if value else None

    def __repr__(self) -> str:
        return f'<AchievementEarned user_id={self.user_id} ach_id={self.achievement_id}>'


# =============================================================================
# Leaderboard Cache
# =============================================================================
# LeaderboardCache is defined in models/leaderboard.py to avoid circular
# imports. Re-exported here for convenience so callers can import from log.
from models.leaderboard import LeaderboardCache  # noqa: F401


# =============================================================================
# Activity Log
# =============================================================================

class ActivityLog(db.Model):
    """
    General user event log for the activity timeline in the dashboard.
    Examples: quiz_completed, certificate_downloaded, achievement_earned.
    """

    __tablename__ = 'activity_logs'

    EVENT_TYPES = (
        'quiz_started',
        'quiz_completed',
        'quiz_abandoned',
        'certificate_generated',
        'certificate_downloaded',
        'achievement_earned',
        'profile_updated',
        'account_created',
    )

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id     = db.Column(db.Integer, db.ForeignKey('users.id',
                            ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    event_type  = db.Column(db.String(50), nullable=False)
    entity_type = db.Column(db.String(50), nullable=True)
    entity_id   = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, nullable=True)
    created_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    __table_args__ = (
        db.Index('idx_al_user_date', 'user_id', 'created_at'),
    )

    def __repr__(self) -> str:
        return f'<ActivityLog user_id={self.user_id} event={self.event_type!r}>'


# =============================================================================
# Anti-Cheat Log
# =============================================================================

class AntiCheatLog(db.Model):
    """
    Audit log for anti-cheat violation events detected during a quiz.
    Linked to the quiz attempt for full traceability.
    """

    __tablename__ = 'anti_cheat_logs'

    EVENT_TYPES = (
        'tab_switch',
        'fullscreen_exit',
        'window_blur',
        'right_click',
        'copy_paste',
        'keyboard_shortcut',
    )

    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    attempt_id  = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id',
                            ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    event_type  = db.Column(db.Enum(*EVENT_TYPES, name='log_event_type_enum'), nullable=False)
    occurred_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    meta        = db.Column(db.Text, nullable=True)  # JSON string for extra data

    @property
    def meta_dict(self) -> dict:
        try:
            return json.loads(self.meta) if self.meta else {}
        except (json.JSONDecodeError, TypeError):
            return {}

    def __repr__(self) -> str:
        return f'<AntiCheatLog attempt_id={self.attempt_id} event={self.event_type!r}>'


# =============================================================================
# Platform Settings
# =============================================================================

class Settings(db.Model):
    """
    Platform-wide configuration stored as key-value pairs.
    Managed via admin panel. Cached in app config on startup.
    """

    __tablename__ = 'settings'

    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    setting_key   = db.Column(db.String(100), nullable=False, unique=True)
    setting_value = db.Column(db.Text, nullable=False)
    description   = db.Column(db.Text, nullable=True)
    updated_at    = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                              onupdate=datetime.utcnow)

    @classmethod
    def get(cls, key: str, default=None):
        """
        Retrieve a setting value by key.

        Args:
            key: The setting_key to look up.
            default: Value to return if key not found.

        Returns:
            The setting_value string or default.
        """
        record = cls.query.filter_by(setting_key=key).first()
        return record.setting_value if record else default

    @classmethod
    def set(cls, key: str, value: str, description: str = '') -> None:
        """
        Create or update a setting.

        Args:
            key: The setting_key.
            value: The value to store.
            description: Optional description (only applied on create).
        """
        record = cls.query.filter_by(setting_key=key).first()
        if record:
            record.setting_value = value
        else:
            record = cls(setting_key=key, setting_value=value, description=description)
            db.session.add(record)

    def __repr__(self) -> str:
        return f'<Settings key={self.setting_key!r} value={self.setting_value!r}>'
