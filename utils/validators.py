"""
QuizNova — Input Validators
=============================
Server-side validation functions for all user input.
Client-side validation is UX-only; these are the authoritative checks.
"""

import re
from typing import Optional


# =============================================================================
# Auth Validators
# =============================================================================

def validate_username(username: str) -> Optional[str]:
    """
    Validate a username string.

    Rules:
      - 3–30 characters
      - Only alphanumeric + underscore
      - No leading/trailing underscores

    Args:
        username: Raw username string from form input.

    Returns:
        Error message string if invalid, None if valid.
    """
    if not username:
        return 'Username is required.'
    if len(username) < 3:
        return 'Username must be at least 3 characters.'
    if len(username) > 30:
        return 'Username must be at most 30 characters.'
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return 'Username can only contain letters, numbers, and underscores.'
    if username.startswith('_') or username.endswith('_'):
        return 'Username cannot start or end with an underscore.'
    return None


def validate_email(email: str) -> Optional[str]:
    """
    Validate an email address format.

    Args:
        email: Raw email string from form input.

    Returns:
        Error message string if invalid, None if valid.
    """
    if not email:
        return 'Email address is required.'
    if len(email) > 255:
        return 'Email address is too long (max 255 characters).'

    email_pattern = r'^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return 'Please enter a valid email address.'
    return None


def validate_password(password: str) -> Optional[str]:
    """
    Validate password strength.

    Rules:
      - Minimum 8 characters
      - At least one uppercase letter
      - At least one digit
      - At least one special character (!@#$%^&*_-)

    Args:
        password: Raw password string from form input.

    Returns:
        Error message string if invalid, None if valid.
    """
    if not password:
        return 'Password is required.'
    if len(password) < 8:
        return 'Password must be at least 8 characters.'
    if not re.search(r'[A-Z]', password):
        return 'Password must contain at least one uppercase letter.'
    if not re.search(r'\d', password):
        return 'Password must contain at least one digit.'
    if not re.search(r'[!@#$%^&*_\-]', password):
        return 'Password must contain at least one special character (!@#$%^&*_-).'
    return None


def validate_password_match(password: str, confirm: str) -> Optional[str]:
    """
    Check that password and confirm_password match.

    Returns:
        Error message string if they don't match, None if they do.
    """
    if password != confirm:
        return 'Passwords do not match.'
    return None


# =============================================================================
# Content Validators
# =============================================================================

def validate_question_text(text: str) -> Optional[str]:
    """Validate a question text field."""
    if not text or not text.strip():
        return 'Question text is required.'
    if len(text.strip()) < 10:
        return 'Question text must be at least 10 characters.'
    if len(text) > 5000:
        return 'Question text is too long (max 5000 characters).'
    return None


def validate_option_text(text: str, label: str) -> Optional[str]:
    """Validate an individual MCQ option."""
    if not text or not text.strip():
        return f'Option {label} is required.'
    if len(text.strip()) < 1:
        return f'Option {label} cannot be empty.'
    if len(text) > 500:
        return f'Option {label} is too long (max 500 characters).'
    return None


def validate_correct_option(correct: str) -> Optional[str]:
    """Validate the correct_option field."""
    if correct not in ('a', 'b', 'c', 'd'):
        return 'Correct option must be a, b, c, or d.'
    return None


def validate_difficulty(difficulty: str) -> Optional[str]:
    """Validate difficulty level."""
    if difficulty not in ('easy', 'medium', 'hard'):
        return 'Difficulty must be easy, medium, or hard.'
    return None


# =============================================================================
# File Upload Validators
# =============================================================================

def validate_image_file(filename: str, file_size_bytes: int) -> Optional[str]:
    """
    Validate an uploaded image file.

    Args:
        filename: Original filename from the upload.
        file_size_bytes: File size in bytes.

    Returns:
        Error message string if invalid, None if valid.
    """
    if not filename:
        return 'No file selected.'

    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if extension not in ('jpg', 'jpeg', 'png', 'webp'):
        return 'Only JPG, PNG, and WebP images are allowed.'

    max_bytes = 2 * 1024 * 1024  # 2MB
    if file_size_bytes > max_bytes:
        return 'Image file size must not exceed 2MB.'

    return None


def validate_csv_file(filename: str) -> Optional[str]:
    """
    Validate an uploaded CSV file extension.

    Args:
        filename: Original filename from the upload.

    Returns:
        Error message string if invalid, None if valid.
    """
    if not filename:
        return 'No file selected.'
    extension = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
    if extension != 'csv':
        return 'Only CSV files are accepted for bulk question import.'
    return None


# =============================================================================
# Slug Validator
# =============================================================================

def validate_slug(slug: str) -> Optional[str]:
    """
    Validate a URL slug.

    Rules:
      - Lowercase letters, digits, hyphens only
      - No leading/trailing hyphens
      - 2–100 characters

    Returns:
        Error message string if invalid, None if valid.
    """
    if not slug:
        return 'Slug is required.'
    if not re.match(r'^[a-z0-9\-]+$', slug):
        return 'Slug can only contain lowercase letters, numbers, and hyphens.'
    if slug.startswith('-') or slug.endswith('-'):
        return 'Slug cannot start or end with a hyphen.'
    if len(slug) < 2 or len(slug) > 100:
        return 'Slug must be between 2 and 100 characters.'
    return None
