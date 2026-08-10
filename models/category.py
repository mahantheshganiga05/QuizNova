"""
QuizNova — Category Model
==========================
Represents top-level knowledge domains (Programming, AI, Data Science, etc.)
"""

from datetime import datetime
from models import db


class Category(db.Model):
    """
    Top-level category (e.g., Programming, Artificial Intelligence).
    Contains multiple subcategories.
    """

    __tablename__ = 'categories'

    # -------------------------------------------------------------------------
    # Columns
    # -------------------------------------------------------------------------
    id          = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name        = db.Column(db.String(100), nullable=False, unique=True)
    slug        = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    icon        = db.Column(db.String(255), nullable=True)
    color_hex   = db.Column(db.String(7), nullable=True)   # e.g. "#7C3AED"
    sort_order  = db.Column(db.Integer, nullable=False, default=0)
    is_active   = db.Column(db.Boolean, nullable=False, default=True)
    created_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    updated_at  = db.Column(db.DateTime, nullable=False, default=datetime.utcnow,
                            onupdate=datetime.utcnow)

    # -------------------------------------------------------------------------
    # Relationships
    # -------------------------------------------------------------------------
    subcategories = db.relationship(
        'Subcategory',
        backref='category',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    # -------------------------------------------------------------------------
    # Properties
    # -------------------------------------------------------------------------
    @property
    def active_subcategory_count(self) -> int:
        """Returns count of active subcategories in this category."""
        return self.subcategories.filter_by(is_active=True).count()

    @property
    def icon_url(self) -> str:
        """Returns the URL path for the category icon."""
        if self.icon:
            return f'/static/icons/categories/{self.icon}'
        return '/static/icons/categories/default.svg'

    @property
    def banner_image_url(self) -> str:
        """Returns unique high-quality 16:9 dark-themed category banner image URL."""
        slug_clean = self.slug.lower()
        if 'program' in slug_clean or 'code' in slug_clean or 'python' in slug_clean or 'java' in slug_clean:
            return '/static/images/categories/cat_programming.jpg'
        elif 'data' in slug_clean and 'struct' in slug_clean or 'dsa' in slug_clean:
            return '/static/images/categories/cat_dsa.jpg'
        elif 'database' in slug_clean or 'dbms' in slug_clean or 'sql' in slug_clean:
            return '/static/images/categories/cat_databases.jpg'
        elif 'ai' in slug_clean or 'artificial' in slug_clean or 'machine' in slug_clean or 'intelligence' in slug_clean:
            return '/static/images/categories/cat_ai.jpg'
        elif 'cyber' in slug_clean or 'security' in slug_clean or 'hack' in slug_clean:
            return '/static/images/categories/cat_cybersecurity.jpg'
        elif 'cloud' in slug_clean or 'aws' in slug_clean or 'azure' in slug_clean:
            return '/static/images/categories/cat_cloud.jpg'
        elif 'math' in slug_clean or 'geometry' in slug_clean or 'calculus' in slug_clean:
            return '/static/images/categories/cat_math.jpg'
        elif 'web' in slug_clean or 'html' in slug_clean or 'css' in slug_clean or 'javascript' in slug_clean:
            return '/static/images/categories/cat_webdev.jpg'
        elif 'aptitude' in slug_clean or 'logic' in slug_clean or 'reason' in slug_clean:
            return '/static/images/categories/cat_aptitude.jpg'
        elif 'network' in slug_clean or 'internet' in slug_clean:
            return '/static/images/categories/cat_networking.jpg'
        elif 'operating' in slug_clean or 'os' in slug_clean or 'linux' in slug_clean:
            return '/static/images/categories/cat_os.jpg'
        elif 'soft' in slug_clean or 'skill' in slug_clean or 'comm' in slug_clean:
            return '/static/images/categories/cat_softskills.jpg'
        elif 'computer' in slug_clean or 'cs' in slug_clean or 'science' in slug_clean:
            return '/static/images/categories/cat_cs.jpg'
        return '/static/images/categories/cat_programming.jpg'

    # -------------------------------------------------------------------------
    # String Representation
    # -------------------------------------------------------------------------
    def __repr__(self) -> str:
        return f'<Category id={self.id} name={self.name!r}>'
