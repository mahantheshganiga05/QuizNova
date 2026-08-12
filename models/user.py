"""
QuizNova — User Model
======================
Represents platform users (students and admins).
Implements Flask-Login UserMixin for session management.
"""

from datetime import datetime
from flask_login import UserMixin
from models import db
import bcrypt


class User(UserMixin, db.Model):
    """
    Represents a QuizNova platform user.
    Roles: 'student' (default) | 'admin'
    """

    __tablename__ = 'users'

    # -------------------------------------------------------------------------
    # Columns
    # -------------------------------------------------------------------------
    id            = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username      = db.Column(db.String(30), unique=True, nullable=False)
    email         = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name     = db.Column(db.String(100), nullable=True)
    bio           = db.Column(db.Text, nullable=True)
    profile_photo = db.Column(db.String(255), nullable=True)
    role          = db.Column(db.Enum('student', 'admin', name='user_role_enum'), nullable=False, default='student')
    is_active     = db.Column(db.Boolean, nullable=False, default=True)
    email_verified = db.Column(db.Boolean, nullable=False, default=False)
    oauth_provider = db.Column(db.String(50), nullable=True)
    oauth_id      = db.Column(db.String(255), nullable=True)
    avatar_url    = db.Column(db.String(500), nullable=True)
    last_login_at = db.Column(db.DateTime, nullable=True)
    login_count   = db.Column(db.Integer, nullable=False, default=0)
    created_at    = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at    = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                              onupdate=datetime.utcnow)

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------
    quiz_attempts       = db.relationship('QuizAttempt', backref='user', lazy='dynamic',
                                          cascade='all, delete-orphan')
    certificates        = db.relationship('Certificate', backref='user', lazy='dynamic',
                                          cascade='all, delete-orphan')
    achievements_earned = db.relationship('AchievementEarned', backref='user', lazy='dynamic',
                                          cascade='all, delete-orphan')
    activity_logs       = db.relationship('ActivityLog', backref='user', lazy='dynamic',
                                          cascade='all, delete-orphan')
    leaderboard_entries = db.relationship('LeaderboardCache', backref='user', lazy='dynamic',
                                          cascade='all, delete-orphan')

    # -------------------------------------------------------------------------
    # Flask-Login required properties
    # -------------------------------------------------------------------------
    def get_id(self) -> str:
        return str(self.id)

    @property
    def is_authenticated(self) -> bool:
        return True

    @property
    def is_anonymous(self) -> bool:
        return False

    # is_active is already a column — Flask-Login uses it via the column value

    # -------------------------------------------------------------------------
    # Password Management
    # -------------------------------------------------------------------------
    def set_password(self, plaintext_password: str) -> None:
        """
        Hash a plaintext password and store it.
        Uses bcrypt with cost factor 12.

        Args:
            plaintext_password: The raw password string from the user.
        """
        password_bytes = plaintext_password.encode('utf-8')
        salt = bcrypt.gensalt(rounds=12)
        self.password_hash = bcrypt.hashpw(password_bytes, salt).decode('utf-8')

    def check_password(self, plaintext_password: str) -> bool:
        """
        Verify a plaintext password against the stored hash.

        Args:
            plaintext_password: The raw password string from the login form.

        Returns:
            True if password matches, False otherwise.
        """
        password_bytes = plaintext_password.encode('utf-8')
        hash_bytes = self.password_hash.encode('utf-8')
        return bcrypt.checkpw(password_bytes, hash_bytes)

    # -------------------------------------------------------------------------
    # Permission Helpers
    # -------------------------------------------------------------------------
    @property
    def is_admin(self) -> bool:
        """Returns True if user has admin role."""
        return self.role == 'admin'

    # -------------------------------------------------------------------------
    # Display Helpers
    # -------------------------------------------------------------------------
    @property
    def display_name(self) -> str:
        """Returns full_name if set, otherwise username."""
        return self.full_name or self.username

    @property
    def profile_photo_url(self) -> str:
        """Returns the URL path for the profile photo, OAuth avatar, or default avatar."""
        if self.profile_photo:
            if self.profile_photo.startswith('http://') or self.profile_photo.startswith('https://'):
                return self.profile_photo
            return f'/static/uploads/profiles/{self.profile_photo}'
        if self.avatar_url:
            return self.avatar_url
        return '/static/images/default-avatar.svg'

    # -------------------------------------------------------------------------
    # Record Updates
    # -------------------------------------------------------------------------
    def record_login(self) -> None:
        """Update login tracking fields. Call on successful login."""
        self.last_login_at = datetime.utcnow()
        self.login_count += 1

    # -------------------------------------------------------------------------
    # String Representation
    # -------------------------------------------------------------------------
    def __repr__(self) -> str:
        return f'<User id={self.id} username={self.username!r} role={self.role!r}>'
