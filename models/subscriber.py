"""
QuizNova — Newsletter Subscriber Model
======================================
Stores email subscriptions for platform updates and newsletters.
"""

import uuid
from datetime import datetime
from models import db


def _generate_unsubscribe_token() -> str:
    return uuid.uuid4().hex


class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscribers'

    id                = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email             = db.Column(db.String(255), unique=True, nullable=False)
    user_id           = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    is_active         = db.Column(db.Boolean, nullable=False, default=True)
    unsubscribe_token = db.Column(db.String(64), unique=True, nullable=True, default=_generate_unsubscribe_token)
    created_at        = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    unsubscribed_at   = db.Column(db.DateTime, nullable=True)

    @property
    def is_subscribed(self) -> bool:
        return bool(self.is_active)

    @is_subscribed.setter
    def is_subscribed(self, value: bool):
        self.is_active = bool(value)
        if not value and not self.unsubscribed_at:
            self.unsubscribed_at = datetime.utcnow()

    def __repr__(self) -> str:
        return f'<NewsletterSubscriber id={self.id} email={self.email!r}>'
