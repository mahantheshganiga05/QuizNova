"""
QuizNova — Auth Routes Blueprint
===================================
Handles user registration, login, logout, and profile management.
"""

import os
import secrets
import json
import urllib.parse
import urllib.request
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify, session
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

        # Send Welcome Email
        try:
            from services.email_service import send_html_email
            send_html_email(
                to_email=user.email,
                subject="Welcome to QuizNova! 🎉",
                template_name="welcome.html",
                context={'user_name': user.full_name or user.username},
                notification_type="registration",
                related_object_id=str(user.id)
            )
        except Exception as e:
            current_app.logger.warning(f"Could not send welcome email: {e}")

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

        # Send Login Security Alert
        try:
            from services.email_service import send_html_email
            from datetime import datetime
            send_html_email(
                to_email=user.email,
                subject="Security Alert: New Login to QuizNova 🛡️",
                template_name="login_alert.html",
                context={
                    'user_name': user.full_name or user.username,
                    'login_time': datetime.utcnow().strftime('%d %B %Y, %H:%M UTC'),
                    'ip_address': request.remote_addr or '127.0.0.1',
                    'user_agent': request.user_agent.string[:100] if request.user_agent else 'Browser'
                },
                notification_type="security_alert",
                related_object_id=f"login_{user.id}_{int(datetime.utcnow().timestamp())}"
            )
        except Exception as e:
            current_app.logger.warning(f"Could not send login alert email: {e}")

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


# =============================================================================
# OAuth Helpers & Routes (Google & GitHub 2.0)
# =============================================================================

def get_callback_url(endpoint_name: str, env_var_name: str) -> str:
    """Helper to get exact callback URL, resolving HTTPS scheme for production/Vercel."""
    configured = os.environ.get(env_var_name)
    if configured:
        return configured
    
    url = url_for(endpoint_name, _external=True)
    is_secure = (
        request.headers.get('X-Forwarded-Proto') == 'https' or
        request.is_secure or
        'vercel.app' in request.host.lower()
    )
    if is_secure and url.startswith('http://'):
        url = 'https://' + url[7:]
    return url


@auth_bp.route('/google/login')
def google_login():
    """Initiate Google OAuth 2.0 authentication."""
    client_id = os.environ.get('GOOGLE_CLIENT_ID') or current_app.config.get('GOOGLE_CLIENT_ID')
    if not client_id:
        flash('Google Login is not configured. Please set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables.', 'error')
        return redirect(url_for('auth.login'))

    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    session['oauth_provider'] = 'google'

    redirect_uri = get_callback_url('auth.google_callback', 'GOOGLE_REDIRECT_URI')

    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'prompt': 'select_account'
    }
    auth_url = 'https://accounts.google.com/o/oauth2/v2/auth?' + urllib.parse.urlencode(params)
    return redirect(auth_url)


@auth_bp.route('/google/callback')
def google_callback():
    """Handle Google OAuth 2.0 authorization callback."""
    client_id = os.environ.get('GOOGLE_CLIENT_ID') or current_app.config.get('GOOGLE_CLIENT_ID')
    client_secret = os.environ.get('GOOGLE_CLIENT_SECRET') or current_app.config.get('GOOGLE_CLIENT_SECRET')

    if not client_id or not client_secret:
        flash('Google Login is missing client credentials.', 'error')
        return redirect(url_for('auth.login'))

    state = request.args.get('state')
    expected_state = session.pop('oauth_state', None)
    if not state or state != expected_state:
        flash('OAuth security state validation failed. Please try logging in again.', 'error')
        return redirect(url_for('auth.login'))

    if request.args.get('error'):
        flash('Google sign-in was cancelled or failed.', 'info')
        return redirect(url_for('auth.login'))

    code = request.args.get('code')
    if not code:
        flash('Missing authorization code from Google.', 'error')
        return redirect(url_for('auth.login'))

    redirect_uri = get_callback_url('auth.google_callback', 'GOOGLE_REDIRECT_URI')

    try:
        token_url = 'https://oauth2.googleapis.com/token'
        token_data = urllib.parse.urlencode({
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        }).encode('utf-8')

        req = urllib.request.Request(token_url, data=token_data, headers={'Content-Type': 'application/x-www-form-urlencoded'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            tokens = json.loads(resp.read().decode('utf-8'))

        access_token = tokens.get('access_token')
        if not access_token:
            flash('Failed to obtain access token from Google.', 'error')
            return redirect(url_for('auth.login'))

        userinfo_req = urllib.request.Request('https://www.googleapis.com/oauth2/v2/userinfo', headers={'Authorization': f'Bearer {access_token}'})
        with urllib.request.urlopen(userinfo_req, timeout=10) as userinfo_resp:
            google_user = json.loads(userinfo_resp.read().decode('utf-8'))

        email = google_user.get('email', '').strip().lower()
        google_id = str(google_user.get('id', ''))
        name = google_user.get('name') or email.split('@')[0]
        picture = google_user.get('picture')

        if not email:
            flash('Google account does not have a public email address.', 'error')
            return redirect(url_for('auth.login'))

        user = User.query.filter_by(email=email).first()
        if not user and google_id:
            user = User.query.filter_by(oauth_provider='google', oauth_id=google_id).first()

        if user:
            if not user.oauth_provider:
                user.oauth_provider = 'google'
                user.oauth_id = google_id
            if picture and not user.avatar_url:
                user.avatar_url = picture
            user.email_verified = True
        else:
            base_username = email.split('@')[0].replace('.', '_')[:20]
            username = base_username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1

            user = User(
                username=username,
                email=email,
                full_name=name,
                oauth_provider='google',
                oauth_id=google_id,
                avatar_url=picture,
                email_verified=True
            )
            user.set_password(secrets.token_urlsafe(16))
            db.session.add(user)
            db.session.flush()

            log = ActivityLog(user_id=user.id, event_type='oauth_registration', description=f'Registered via Google OAuth: {email}')
            db.session.add(log)

        login_user(user, remember=True)
        user.record_login()
        db.session.commit()

        flash(f'Welcome, {user.display_name}! Successfully logged in with Google.', 'success')
        return redirect(url_for('dashboard.index'))

    except Exception as e:
        current_app.logger.error(f'Google OAuth error: {e}')
        flash('An error occurred while authenticating with Google. Please try again.', 'error')
        return redirect(url_for('auth.login'))


# =============================================================================
# GitHub OAuth 2.0
# =============================================================================

@auth_bp.route('/github/login')
def github_login():
    """Initiate GitHub OAuth 2.0 authentication."""
    client_id = os.environ.get('GITHUB_CLIENT_ID') or current_app.config.get('GITHUB_CLIENT_ID')
    if not client_id:
        flash('GitHub Login is not configured. Please set GITHUB_CLIENT_ID and GITHUB_CLIENT_SECRET environment variables.', 'error')
        return redirect(url_for('auth.login'))

    state = secrets.token_urlsafe(32)
    session['oauth_state'] = state
    session['oauth_provider'] = 'github'

    redirect_uri = get_callback_url('auth.github_callback', 'GITHUB_REDIRECT_URI')

    params = {
        'client_id': client_id,
        'redirect_uri': redirect_uri,
        'scope': 'user:email read:user',
        'state': state
    }
    auth_url = 'https://github.com/login/oauth/authorize?' + urllib.parse.urlencode(params)
    return redirect(auth_url)


@auth_bp.route('/github/callback')
def github_callback():
    """Handle GitHub OAuth 2.0 authorization callback."""
    client_id = os.environ.get('GITHUB_CLIENT_ID') or current_app.config.get('GITHUB_CLIENT_ID')
    client_secret = os.environ.get('GITHUB_CLIENT_SECRET') or current_app.config.get('GITHUB_CLIENT_SECRET')

    if not client_id or not client_secret:
        flash('GitHub Login is missing client credentials.', 'error')
        return redirect(url_for('auth.login'))

    state = request.args.get('state')
    expected_state = session.pop('oauth_state', None)
    if not state or state != expected_state:
        flash('OAuth security state validation failed. Please try logging in again.', 'error')
        return redirect(url_for('auth.login'))

    if request.args.get('error'):
        flash('GitHub sign-in was cancelled or failed.', 'info')
        return redirect(url_for('auth.login'))

    code = request.args.get('code')
    if not code:
        flash('Missing authorization code from GitHub.', 'error')
        return redirect(url_for('auth.login'))

    redirect_uri = get_callback_url('auth.github_callback', 'GITHUB_REDIRECT_URI')

    try:
        token_url = 'https://github.com/login/oauth/access_token'
        token_data = urllib.parse.urlencode({
            'code': code,
            'client_id': client_id,
            'client_secret': client_secret,
            'redirect_uri': redirect_uri
        }).encode('utf-8')

        req = urllib.request.Request(token_url, data=token_data, headers={'Accept': 'application/json', 'Content-Type': 'application/x-www-form-urlencoded'})
        with urllib.request.urlopen(req, timeout=10) as resp:
            tokens = json.loads(resp.read().decode('utf-8'))

        access_token = tokens.get('access_token')
        if not access_token:
            flash('Failed to obtain access token from GitHub.', 'error')
            return redirect(url_for('auth.login'))

        user_req = urllib.request.Request('https://api.github.com/user', headers={'Authorization': f'token {access_token}', 'User-Agent': 'QuizNova-OAuth'})
        with urllib.request.urlopen(user_req, timeout=10) as user_resp:
            gh_user = json.loads(user_resp.read().decode('utf-8'))

        github_id = str(gh_user.get('id', ''))
        email = gh_user.get('email')
        name = gh_user.get('name') or gh_user.get('login') or 'GitHub User'
        avatar_url = gh_user.get('avatar_url')

        if not email:
            emails_req = urllib.request.Request('https://api.github.com/user/emails', headers={'Authorization': f'token {access_token}', 'User-Agent': 'QuizNova-OAuth'})
            with urllib.request.urlopen(emails_req, timeout=10) as emails_resp:
                emails_list = json.loads(emails_resp.read().decode('utf-8'))
                for em in emails_list:
                    if em.get('primary') and em.get('verified'):
                        email = em.get('email')
                        break
                if not email and emails_list:
                    email = emails_list[0].get('email')

        if not email:
            email = f"github_{github_id}@quiznova.local"

        email = email.strip().lower()

        user = User.query.filter_by(email=email).first()
        if not user and github_id:
            user = User.query.filter_by(oauth_provider='github', oauth_id=github_id).first()

        if user:
            if not user.oauth_provider:
                user.oauth_provider = 'github'
                user.oauth_id = github_id
            if avatar_url and not user.avatar_url:
                user.avatar_url = avatar_url
            user.email_verified = True
        else:
            base_username = (gh_user.get('login') or email.split('@')[0])[:20]
            username = base_username
            counter = 1
            while User.query.filter_by(username=username).first():
                username = f"{base_username}{counter}"
                counter += 1

            user = User(
                username=username,
                email=email,
                full_name=name,
                oauth_provider='github',
                oauth_id=github_id,
                avatar_url=avatar_url,
                email_verified=True
            )
            user.set_password(secrets.token_urlsafe(16))
            db.session.add(user)
            db.session.flush()

            log = ActivityLog(user_id=user.id, event_type='oauth_registration', description=f'Registered via GitHub OAuth: {email}')
            db.session.add(log)

        login_user(user, remember=True)
        user.record_login()
        db.session.commit()

        flash(f'Welcome, {user.display_name}! Successfully logged in with GitHub.', 'success')
        return redirect(url_for('dashboard.index'))

    except Exception as e:
        current_app.logger.error(f'GitHub OAuth error: {e}')
        flash('An error occurred while authenticating with GitHub. Please try again.', 'error')
        return redirect(url_for('auth.login'))


# =============================================================================
# Password Reset Routes
# =============================================================================

@auth_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password():
    """Request password reset link."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        user = User.query.filter_by(email=email).first()
        if user:
            token = secrets.token_urlsafe(32)
            user.reset_token = token
            from datetime import datetime, timedelta
            user.reset_token_expires = datetime.utcnow() + timedelta(hours=1)
            db.session.commit()

            site_url = (current_app.config.get('SITE_URL') or 'https://quiz-nova-nu.vercel.app').rstrip('/')
            reset_url = f"{site_url}/reset-password/{token}"

            try:
                from services.email_service import send_html_email
                send_html_email(
                    to_email=user.email,
                    subject="Reset your QuizNova password",
                    template_name="password_reset.html",
                    context={
                        'user_name': user.full_name or user.username,
                        'reset_url': reset_url
                    },
                    notification_type="password_reset",
                    related_object_id=token
                )
            except Exception as e:
                current_app.logger.error(f"Password reset email error: {e}")

        flash("If an account with that email exists, we have sent a password reset link.", "info")
        return redirect(url_for('auth.forgot_password'))

    return render_template('auth/forgot_password.html')


@auth_bp.route('/reset-password/<string:token>', methods=['GET', 'POST'])
def reset_password(token):
    """Set new password using reset token."""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    from datetime import datetime
    user = User.query.filter_by(reset_token=token).first()
    if not user or not user.reset_token_expires or user.reset_token_expires < datetime.utcnow():
        flash("Invalid or expired password reset link.", "error")
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "error")
            return render_template('auth/reset_password.html', token=token)

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return render_template('auth/reset_password.html', token=token)

        user.set_password(password)
        user.reset_token = None
        user.reset_token_expires = None
        db.session.commit()

        flash("Your password has been reset successfully. Please log in with your new password.", "success")
        return redirect(url_for('auth.login'))

    return render_template('auth/reset_password.html', token=token)
