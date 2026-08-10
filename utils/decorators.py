"""
QuizNova — Custom Decorators
==============================
Authentication and authorization decorators for route protection.
"""

from functools import wraps
from flask import abort, redirect, url_for, flash, request
from flask_login import current_user


def admin_required(f):
    """
    Decorator that restricts access to admin users only.
    Redirects unauthenticated users to admin login.
    Returns 403 for authenticated non-admins.

    Usage:
        @admin_bp.route('/dashboard')
        @admin_required
        def dashboard():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('admin.login', next=request.url))
        if not current_user.is_admin:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function


def quiz_owner_required(f):
    """
    Decorator that ensures the current user owns the quiz attempt.
    Expects `attempt_id` as a route parameter.
    Returns 403 if the attempt belongs to another user.

    Usage:
        @quiz_bp.route('/<int:attempt_id>/submit', methods=['POST'])
        @login_required
        @quiz_owner_required
        def submit_quiz(attempt_id):
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from models.quiz import QuizAttempt
        attempt_id = kwargs.get('attempt_id')
        if attempt_id:
            attempt = QuizAttempt.query.get_or_404(attempt_id)
            if attempt.user_id != current_user.id:
                abort(403)
        return f(*args, **kwargs)
    return decorated_function


def active_user_required(f):
    """
    Decorator that checks the current user is not banned (is_active=True).
    Use after @login_required.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_active:
            flash('Your account has been suspended. Please contact support.', 'error')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function
