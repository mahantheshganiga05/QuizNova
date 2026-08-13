"""
QuizNova — Newsletter Subscriber Model
======================================
Stores email subscriptions for platform updates and newsletters.
"""

from datetime import datetime
from models import db


class NewsletterSubscriber(db.Model):
    __tablename__ = 'newsletter_subscribers'

    id         = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email      = db.Column(db.String(255), unique=True, nullable=False)
    is_active  = db.Column(db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self) -> str:
        return f'<NewsletterSubscriber id={self.id} email={self.email!r}>'
