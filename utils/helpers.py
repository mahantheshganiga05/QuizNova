"""
QuizNova — Helper Utilities
=============================
General-purpose utility functions used across the application.
"""

import re
import os
import uuid
from datetime import datetime
from typing import Optional


# =============================================================================
# Text Utilities
# =============================================================================

def slugify(text: str) -> str:
    """
    Convert a string to a URL-friendly slug.

    Examples:
        "Python Programming" → "python-programming"
        "Data Science & AI" → "data-science-ai"

    Args:
        text: Input string to slugify.

    Returns:
        Lowercase hyphen-separated slug string.
    """
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)       # Remove non-alphanumeric except spaces and hyphens
    text = re.sub(r'[\s_]+', '-', text)          # Replace spaces/underscores with hyphens
    text = re.sub(r'-+', '-', text)              # Collapse multiple hyphens
    text = text.strip('-')                        # Strip leading/trailing hyphens
    return text


def truncate(text: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    Truncate text to max_length characters with a suffix.

    Args:
        text: Input string.
        max_length: Maximum characters before truncation.
        suffix: String appended when truncated.

    Returns:
        Truncated string.
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)].rstrip() + suffix


# =============================================================================
# Time Utilities
# =============================================================================

def format_seconds(seconds: int) -> str:
    """
    Format a number of seconds as MM:SS string.

    Args:
        seconds: Duration in seconds.

    Returns:
        Formatted string like "26:36".
    """
    if seconds is None or seconds < 0:
        return '00:00'
    minutes = seconds // 60
    secs = seconds % 60
    return f'{minutes:02d}:{secs:02d}'


def time_ago(dt: datetime) -> str:
    """
    Return a human-readable relative time string.

    Examples:
        "just now", "5 minutes ago", "2 hours ago", "3 days ago"

    Args:
        dt: Datetime object to format.

    Returns:
        Human-readable relative time string.
    """
    now = datetime.utcnow()
    diff = now - dt
    total_seconds = int(diff.total_seconds())

    if total_seconds < 60:
        return 'just now'
    elif total_seconds < 3600:
        minutes = total_seconds // 60
        return f'{minutes} minute{"s" if minutes != 1 else ""} ago'
    elif total_seconds < 86400:
        hours = total_seconds // 3600
        return f'{hours} hour{"s" if hours != 1 else ""} ago'
    elif total_seconds < 604800:
        days = total_seconds // 86400
        return f'{days} day{"s" if days != 1 else ""} ago'
    elif total_seconds < 2592000:
        weeks = total_seconds // 604800
        return f'{weeks} week{"s" if weeks != 1 else ""} ago'
    else:
        return dt.strftime('%b %d, %Y')


# =============================================================================
# File Utilities
# =============================================================================

def secure_uuid_filename(original_filename: str) -> str:
    """
    Generate a secure UUID-based filename preserving the extension.
    Prevents path traversal and malicious filenames.

    Args:
        original_filename: The user-provided filename.

    Returns:
        A safe UUID filename like "550e8400-e29b-41d4-a716.jpg"
    """
    extension = ''
    if '.' in original_filename:
        extension = '.' + original_filename.rsplit('.', 1)[-1].lower()
    return str(uuid.uuid4()) + extension


def ensure_dir(path: str) -> None:
    """
    Create a directory if it does not exist.

    Args:
        path: Directory path to create.
    """
    os.makedirs(path, exist_ok=True)


# =============================================================================
# Score Utilities
# =============================================================================

def calculate_percentage(correct: int, total: int) -> float:
    """
    Calculate percentage score, safe against zero division.

    Args:
        correct: Number of correct answers.
        total: Total number of questions.

    Returns:
        Percentage as float (0.00 – 100.00). Returns 0.0 if total is 0.
    """
    if total == 0:
        return 0.0
    return round((correct / total) * 100, 2)


def get_performance_label(percentage: float) -> str:
    """
    Map percentage to a descriptive performance label.

    Args:
        percentage: Score percentage (0–100).

    Returns:
        Performance label string.
    """
    if percentage >= 90:
        return 'Excellent'
    elif percentage >= 75:
        return 'Good'
    elif percentage >= 60:
        return 'Average'
    elif percentage >= 40:
        return 'Below Average'
    return 'Poor'


def get_grade(percentage: float) -> str:
    """Return letter grade for a percentage score."""
    if percentage >= 90:
        return 'A+'
    elif percentage >= 80:
        return 'A'
    elif percentage >= 70:
        return 'B'
    elif percentage >= 60:
        return 'C'
    elif percentage >= 50:
        return 'D'
    return 'F'


# =============================================================================
# Pagination Helper
# =============================================================================

def paginate_query(query, page: int, per_page: int):
    """
    Apply pagination to a SQLAlchemy query.

    Args:
        query: A SQLAlchemy query object.
        page: Current page number (1-indexed).
        per_page: Number of items per page.

    Returns:
        Flask-SQLAlchemy Pagination object.
    """
    page = max(1, page)
    per_page = min(max(1, per_page), 100)  # Cap at 100
    return query.paginate(page=page, per_page=per_page, error_out=False)
