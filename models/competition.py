"""
QuizNova — Competition Models
===================================
Models for managing coding & quiz competitions, registrations, attempts,
leaderboards, and winner awards.
"""

from datetime import datetime
from models import db


class Competition(db.Model):
    """
    Represents a Quiz & Coding Competition event.
    """
    __tablename__ = 'competitions'

    id                   = db.Column(db.Integer, primary_key=True, autoincrement=True)
    title                = db.Column(db.String(255), nullable=False)
    slug                 = db.Column(db.String(255), unique=True, nullable=False)
    short_description    = db.Column(db.String(500), nullable=True)
    full_description     = db.Column(db.Text, nullable=True)
    banner_url           = db.Column(db.String(255), nullable=True)
    thumbnail_url        = db.Column(db.String(255), nullable=True)
    
    category_id          = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    subcategory_id       = db.Column(db.Integer, db.ForeignKey('subcategories.id', ondelete='SET NULL'), nullable=True)
    
    total_questions      = db.Column(db.SmallInteger, nullable=False, default=20)
    duration_minutes     = db.Column(db.SmallInteger, nullable=False, default=45)
    passing_marks        = db.Column(db.SmallInteger, nullable=False, default=60)
    max_participants     = db.Column(db.Integer, nullable=True, default=1000)
    
    reg_start_date       = db.Column(db.DateTime, nullable=True)
    reg_end_date         = db.Column(db.DateTime, nullable=True)
    start_date           = db.Column(db.DateTime, nullable=False)
    end_date             = db.Column(db.DateTime, nullable=False)
    
    is_free              = db.Column(db.Boolean, nullable=False, default=True)
    prize_pool_text      = db.Column(db.String(255), nullable=True, default='$1,000 Prize Pool')
    prize_1st            = db.Column(db.String(255), nullable=True, default='🥇 Gold Trophy + $500 Amazon Gift Card + Certificate')
    prize_2nd            = db.Column(db.String(255), nullable=True, default='🥈 Silver Medal + $300 Gift Card + Certificate')
    prize_3rd            = db.Column(db.String(255), nullable=True, default='🥉 Bronze Medal + $200 Gift Card + Certificate')
    prize_consolation    = db.Column(db.String(255), nullable=True, default='🎖️ Verifiable Certificate of Excellence')
    
    sponsor_name         = db.Column(db.String(150), nullable=True, default='QuizNova AI')
    organizer_name       = db.Column(db.String(150), nullable=True, default='QuizNova Tech Team')
    rules_text           = db.Column(db.Text, nullable=True)
    eligibility_text     = db.Column(db.Text, nullable=True)
    
    cert_enabled         = db.Column(db.Boolean, nullable=False, default=True)
    leaderboard_enabled  = db.Column(db.Boolean, nullable=False, default=True)
    is_featured          = db.Column(db.Boolean, nullable=False, default=False)
    is_trending          = db.Column(db.Boolean, nullable=False, default=False)
    
    comp_type            = db.Column(db.String(30), nullable=True, default='quiz')
    difficulty           = db.Column(db.String(20), nullable=True, default='intermediate')
    status               = db.Column(db.Enum('draft', 'published', 'live', 'completed', name='comp_status_enum'), nullable=False, default='published')
    created_at           = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at           = db.Column(db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category             = db.relationship('Category', backref='competitions')
    subcategory          = db.relationship('Subcategory', backref='competitions')
    questions            = db.relationship('CompetitionQuestion', backref='competition', cascade='all, delete-orphan')
    registrations        = db.relationship('CompetitionRegistration', backref='competition', cascade='all, delete-orphan')
    results              = db.relationship('CompetitionResult', backref='competition', cascade='all, delete-orphan')
    winners              = db.relationship('CompetitionWinner', backref='competition', cascade='all, delete-orphan')

    @property
    def registered_count(self) -> int:
        return len(self.registrations)

    @property
    def current_status(self) -> str:
        now = datetime.utcnow()
        if self.status == 'draft':
            return 'draft'
        if now > self.end_date or self.status == 'completed':
            return 'completed'
        if self.start_date <= now <= self.end_date or self.status == 'live':
            return 'live'
        return 'upcoming'


class CompetitionQuestion(db.Model):
    """
    Links Questions from existing Question Bank to a Competition.
    """
    __tablename__ = 'competition_questions'

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id', ondelete='CASCADE'), nullable=False)
    question_id    = db.Column(db.Integer, db.ForeignKey('questions.id', ondelete='CASCADE'), nullable=False)
    question_order = db.Column(db.SmallInteger, nullable=False, default=1)

    question       = db.relationship('Question')


class CompetitionRegistration(db.Model):
    """
    User Registration for a Competition — with full student profile data.
    """
    __tablename__ = 'competition_registrations'

    id              = db.Column(db.Integer, primary_key=True, autoincrement=True)
    competition_id  = db.Column(db.Integer, db.ForeignKey('competitions.id', ondelete='CASCADE'), nullable=False)
    user_id         = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)

    # Student Registration Profile
    full_name       = db.Column(db.String(200), nullable=True)
    email           = db.Column(db.String(200), nullable=True)
    phone           = db.Column(db.String(20), nullable=True)
    gender          = db.Column(db.String(20), nullable=True)
    date_of_birth   = db.Column(db.String(20), nullable=True)   # stored as string for simplicity
    country         = db.Column(db.String(80), nullable=True)
    state           = db.Column(db.String(80), nullable=True)
    city            = db.Column(db.String(80), nullable=True)
    college         = db.Column(db.String(255), nullable=True)
    department      = db.Column(db.String(150), nullable=True)
    course          = db.Column(db.String(150), nullable=True)
    year_of_study   = db.Column(db.String(30), nullable=True)
    usn_roll        = db.Column(db.String(50), nullable=True)
    linkedin_url    = db.Column(db.String(255), nullable=True)
    github_url      = db.Column(db.String(255), nullable=True)
    photo_url       = db.Column(db.String(255), nullable=True)

    payment_status  = db.Column(db.Enum('free', 'pending', 'paid', name='payment_status_enum'), nullable=False, default='free')
    registered_at   = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user            = db.relationship('User', backref='competition_registrations')

    __table_args__ = (
        db.UniqueConstraint('competition_id', 'user_id', name='uq_comp_reg'),
    )




class CompetitionResult(db.Model):
    """
    Stores User Results and Performance in a Competition.
    """
    __tablename__ = 'competition_results'

    id                  = db.Column(db.Integer, primary_key=True, autoincrement=True)
    competition_id      = db.Column(db.Integer, db.ForeignKey('competitions.id', ondelete='CASCADE'), nullable=False)
    user_id             = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    attempt_id          = db.Column(db.Integer, db.ForeignKey('quiz_attempts.id', ondelete='SET NULL'), nullable=True)
    
    score               = db.Column(db.Integer, nullable=False, default=0)
    percentage          = db.Column(db.Float, nullable=False, default=0.0)
    time_taken_seconds  = db.Column(db.Integer, nullable=False, default=0)
    correct_count       = db.Column(db.SmallInteger, nullable=False, default=0)
    wrong_count         = db.Column(db.SmallInteger, nullable=False, default=0)
    rank_position       = db.Column(db.Integer, nullable=True)
    is_winner           = db.Column(db.Boolean, nullable=False, default=False)
    prize_won           = db.Column(db.String(255), nullable=True)
    submitted_at        = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user                = db.relationship('User', backref='competition_results')
    attempt             = db.relationship('QuizAttempt')

    __table_args__ = (
        db.UniqueConstraint('competition_id', 'user_id', name='uq_comp_user_result'),
    )


class CompetitionWinner(db.Model):
    """
    Top 3 Winners and Consolation Certificate recipients.
    """
    __tablename__ = 'competition_winners'

    id             = db.Column(db.Integer, primary_key=True, autoincrement=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competitions.id', ondelete='CASCADE'), nullable=False)
    user_id        = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    rank_position  = db.Column(db.SmallInteger, nullable=False)  # 1, 2, 3
    prize_title    = db.Column(db.String(255), nullable=True)
    certificate_id = db.Column(db.Integer, db.ForeignKey('certificates.id', ondelete='SET NULL'), nullable=True)
    awarded_at     = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    user           = db.relationship('User')
    certificate    = db.relationship('Certificate')
