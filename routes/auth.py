"""
QuizNova — Auth Routes Blueprint
===================================
Handles user registration, login, logout, and profile management.
"""

import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename

from models import db
from models.user import User
from models.log import ActivityLog
from utils.validators import validate_username, validate_email, validate_password, validate_password_match
from utils.helpers import secure_uuid_filename, ensure_dir

auth_bp = Blueprint('auth', __name__)


# =============================================================================
# Registration
# =============================================================================

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration page and handler."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = {}

        # Validate inputs
        if err := validate_username(username):
            errors['username'] = err
        if err := validate_email(email):
            errors['email'] = err
        if err := validate_password(password):
            errors['password'] = err
        if err := validate_password_match(password, confirm_password):
            errors['confirm_password'] = err

        # Check uniqueness
        if not errors.get('username') and User.query.filter_by(username=username).first():
            errors['username'] = 'This username is already taken.'
        if not errors.get('email') and User.query.filter_by(email=email).first():
            errors['email'] = 'An account with this email already exists.'

        if errors:
            return render_template('auth/register.html', errors=errors,
                                   form_data={'username': username, 'email': email})

        # Create user
        user = User(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.flush()  # Get user.id before commit

        # Log account creation
        log = ActivityLog(user_id=user.id, event_type='account_created',
                          description=f'Account created for {username}')
        db.session.add(log)
        db.session.commit()

        login_user(user)
        flash('Welcome to QuizNova! Your account has been created.', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('auth/register.html', errors={}, form_data={})


# =============================================================================
# Login
# =============================================================================

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login page and handler."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        remember_me = bool(request.form.get('remember_me'))

        user = User.query.filter_by(email=email).first()

        # Generic error — don't reveal whether email exists
        if not user or not user.check_password(password):
            flash('Invalid email or password. Please try again.', 'error')
            return render_template('auth/login.html', form_data={'email': email})

        if not user.is_active:
            flash('Your account has been suspended. Please contact support.', 'error')
            return render_template('auth/login.html', form_data={'email': email})

        login_user(user, remember=remember_me)
        user.record_login()
        db.session.commit()

        next_page = request.args.get('next')
        if next_page and next_page.startswith('/'):
            return redirect(next_page)

        if user.is_admin:
            return redirect(url_for('admin.dashboard'))

        return redirect(url_for('dashboard.index'))

    return render_template('auth/login.html', form_data={})


# =============================================================================
# Logout
# =============================================================================

@auth_bp.route('/logout')
@login_required
def logout():
    """Log the current user out and redirect to home."""
    logout_user()
    flash('You have been logged out successfully.', 'info')
    return redirect(url_for('public.home'))


# =============================================================================
# Profile
# =============================================================================

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    """View and update user profile."""
    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        bio = request.form.get('bio', '').strip()
        profile_photo = request.files.get('profile_photo')

        # Update text fields
        if full_name:
            current_user.full_name = full_name[:100]
        current_user.bio = bio[:500] if bio else None

        # Handle photo upload
        if profile_photo and profile_photo.filename:
            file_data = profile_photo.read()
            from utils.validators import validate_image_file
            err = validate_image_file(profile_photo.filename, len(file_data))
            if err:
                flash(err, 'error')
                return redirect(url_for('auth.profile'))

            upload_dir = os.path.join(current_app.root_path,
                                      current_app.config['UPLOAD_FOLDER_PROFILES'])
            ensure_dir(upload_dir)

            filename = secure_uuid_filename(profile_photo.filename)
            filepath = os.path.join(upload_dir, filename)

            # Delete old photo if exists
            if current_user.profile_photo:
                old_path = os.path.join(upload_dir, current_user.profile_photo)
                if os.path.exists(old_path):
                    os.remove(old_path)

            with open(filepath, 'wb') as f:
                f.write(file_data)

            current_user.profile_photo = filename

        # Log activity
        log = ActivityLog(user_id=current_user.id, event_type='profile_updated',
                          description='Profile information updated')
        db.session.add(log)
        db.session.commit()

        flash('Profile updated successfully.', 'success')
        return redirect(url_for('auth.profile'))

    return render_template('auth/profile.html')
