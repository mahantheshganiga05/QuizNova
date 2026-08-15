"""
QuizNova — Admin Routes Blueprint
====================================
All admin panel routes behind @admin_required.
"""

import csv, io
from datetime import datetime
from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, make_response, current_app, jsonify)
from flask_login import login_user, logout_user, current_user
from models import db
from models.user import User
from models.category import Category
from models.subcategory import Subcategory
from models.question import Question
from models.quiz import QuizAttempt, AttemptQuestion, AttemptAnswer
from models.result import Result
from models.certificate import Certificate
from models.log import Settings
from utils.decorators import admin_required
from utils.validators import (validate_question_text, validate_option_text,
                               validate_correct_option, validate_difficulty,
                               validate_csv_file, validate_slug)
from utils.helpers import slugify, paginate_query
from services.analytics import get_admin_dashboard_stats, get_analytics_charts

admin_bp = Blueprint('admin', __name__)


# =============================================================================
# Admin Auth
# =============================================================================

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        user = User.query.filter_by(email=email, role='admin').first()

        if not user or not user.check_password(password) or not user.is_active:
            flash('Invalid admin credentials.', 'error')
            return render_template('admin/login.html')

        login_user(user)
        user.record_login()
        db.session.commit()
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/login.html')


@admin_bp.route('/logout')
@admin_required
def logout():
    logout_user()
    return redirect(url_for('admin.login'))


# =============================================================================
# Admin Dashboard
# =============================================================================

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    from models.competition import Competition

    stats = get_admin_dashboard_stats()
    charts = get_analytics_charts()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    recent_attempts = (QuizAttempt.query
                       .filter_by(status='submitted')
                       .order_by(QuizAttempt.submitted_at.desc())
                       .limit(5).all())

    all_comps = Competition.query.all()
    comp_stats = {
        'total': len(all_comps),
        'upcoming': len([c for c in all_comps if c.current_status == 'upcoming']),
        'live': len([c for c in all_comps if c.current_status == 'live']),
        'completed': len([c for c in all_comps if c.current_status == 'completed']),
    }
    recent_competitions = Competition.query.order_by(Competition.created_at.desc()).limit(5).all()

    return render_template('admin/dashboard.html', stats=stats, charts=charts,
                           recent_users=recent_users, recent_attempts=recent_attempts,
                           comp_stats=comp_stats, recent_competitions=recent_competitions)


# =============================================================================
# Category Management
# =============================================================================

@admin_bp.route('/categories', methods=['GET', 'POST'])
@admin_required
def categories():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        color_hex = request.form.get('color_hex', '#7C3AED').strip()
        auto_slug = slugify(name)

        if Category.query.filter_by(slug=auto_slug).first():
            flash(f'A category with slug "{auto_slug}" already exists.', 'error')
        else:
            cat = Category(name=name, slug=auto_slug, description=description, color_hex=color_hex)
            db.session.add(cat)
            db.session.commit()
            flash(f'Category "{name}" created successfully.', 'success')

        return redirect(url_for('admin.categories'))

    cats = Category.query.order_by(Category.sort_order).all()
    return render_template('admin/categories.html', categories=cats)


@admin_bp.route('/categories/<int:cat_id>/toggle', methods=['POST'])
@admin_required
def toggle_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    cat.is_active = not cat.is_active
    db.session.commit()
    status = 'activated' if cat.is_active else 'deactivated'
    flash(f'Category "{cat.name}" {status}.', 'success')
    return redirect(url_for('admin.categories'))


# =============================================================================
# Subcategory Management
# =============================================================================

@admin_bp.route('/subcategories', methods=['GET', 'POST'])
@admin_required
def subcategories():
    if request.method == 'POST':
        cat_id = request.form.get('category_id', type=int)
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        questions_per_quiz = request.form.get('questions_per_quiz', 20, type=int)
        time_limit = request.form.get('time_limit_minutes', 30, type=int)
        pass_threshold = request.form.get('pass_threshold', 60, type=int)
        auto_slug = slugify(name)

        sub = Subcategory(
            category_id=cat_id, name=name, slug=auto_slug,
            description=description, questions_per_quiz=questions_per_quiz,
            time_limit_minutes=time_limit, pass_threshold=pass_threshold
        )
        db.session.add(sub)
        db.session.commit()
        flash(f'Subcategory "{name}" created.', 'success')
        return redirect(url_for('admin.subcategories'))

    subs = (Subcategory.query
            .join(Category)
            .order_by(Category.sort_order, Subcategory.sort_order)
            .all())
    categories = Category.query.filter_by(is_active=True).all()
    return render_template('admin/subcategories.html', subcategories=subs, categories=categories)


# =============================================================================
# Question Management
# =============================================================================

@admin_bp.route('/questions', methods=['GET'])
@admin_required
def questions():
    page = request.args.get('page', 1, type=int)
    sub_filter = request.args.get('subcategory_id', type=int)
    search = request.args.get('search', '').strip()

    query = Question.query.join(Subcategory)
    if sub_filter:
        query = query.filter(Question.subcategory_id == sub_filter)
    if search:
        query = query.filter(Question.question_text.ilike(f'%{search}%'))

    pagination = query.order_by(Question.created_at.desc()).paginate(
        page=page, per_page=current_app.config['ADMIN_QUESTIONS_PER_PAGE'], error_out=False
    )
    subcategories = Subcategory.query.filter_by(is_active=True).all()
    selected_sub = Subcategory.query.get(sub_filter) if sub_filter else None
    sub_question_count = Question.query.filter_by(subcategory_id=sub_filter).count() if sub_filter else 0
    return render_template('admin/questions.html', pagination=pagination,
                           subcategories=subcategories, search=search, sub_filter=sub_filter,
                           selected_sub=selected_sub, sub_question_count=sub_question_count)


@admin_bp.route('/questions/add', methods=['POST'])
@admin_required
def add_question():
    errors = {}
    q_text = request.form.get('question_text', '').strip()
    opt_a = request.form.get('option_a', '').strip()
    opt_b = request.form.get('option_b', '').strip()
    opt_c = request.form.get('option_c', '').strip()
    opt_d = request.form.get('option_d', '').strip()
    correct = request.form.get('correct_option', '').strip().lower()
    difficulty = request.form.get('difficulty', 'medium').strip()
    explanation = request.form.get('explanation', '').strip()
    sub_id = request.form.get('subcategory_id', type=int)

    if err := validate_question_text(q_text): errors['q'] = err
    if err := validate_option_text(opt_a, 'A'): errors['a'] = err
    if err := validate_option_text(opt_b, 'B'): errors['b'] = err
    if err := validate_option_text(opt_c, 'C'): errors['c'] = err
    if err := validate_option_text(opt_d, 'D'): errors['d'] = err
    if err := validate_correct_option(correct): errors['correct'] = err
    if err := validate_difficulty(difficulty): errors['diff'] = err

    if errors:
        for msg in errors.values():
            flash(msg, 'error')
    else:
        q = Question(
            subcategory_id=sub_id, question_text=q_text,
            option_a=opt_a, option_b=opt_b, option_c=opt_c, option_d=opt_d,
            correct_option=correct, explanation=explanation,
            difficulty=difficulty, created_by=current_user.id
        )
        db.session.add(q)
        db.session.commit()
        flash('Question added successfully.', 'success')

    return redirect(url_for('admin.questions'))


@admin_bp.route('/questions/import', methods=['POST'])
@admin_required
def import_questions_csv():
    """Bulk import questions from CSV upload."""
    file = request.files.get('csv_file')
    if not file or not file.filename:
        flash('Please select a CSV file to upload.', 'error')
        return redirect(url_for('admin.questions'))

    err = validate_csv_file(file.filename)
    if err:
        flash(err, 'error')
        return redirect(url_for('admin.questions'))

    content = file.read().decode('utf-8-sig')
    reader = csv.DictReader(io.StringIO(content))

    REQUIRED_COLS = {'subcategory_id', 'question_text', 'option_a', 'option_b',
                     'option_c', 'option_d', 'correct_option', 'difficulty'}
    if not REQUIRED_COLS.issubset(set(reader.fieldnames or [])):
        flash(f'CSV is missing required columns: {REQUIRED_COLS - set(reader.fieldnames or [])}', 'error')
        return redirect(url_for('admin.questions'))

    imported = 0
    row_errors = []

    for row_num, row in enumerate(reader, start=2):
        row_errs = []

        try:
            sub_id = int(row.get('subcategory_id', 0))
        except ValueError:
            row_errs.append('subcategory_id must be an integer')
            row_errors.append({'row': row_num, 'errors': row_errs})
            continue

        if not Subcategory.query.get(sub_id):
            row_errs.append(f'subcategory_id {sub_id} does not exist')

        if err := validate_question_text(row.get('question_text', '')): row_errs.append(err)
        if err := validate_correct_option(row.get('correct_option', '').lower()): row_errs.append(err)
        if err := validate_difficulty(row.get('difficulty', '')): row_errs.append(err)

        if row_errs:
            row_errors.append({'row': row_num, 'errors': row_errs})
            continue

        q = Question(
            subcategory_id=sub_id,
            question_text=row['question_text'].strip(),
            option_a=row['option_a'].strip(),
            option_b=row['option_b'].strip(),
            option_c=row['option_c'].strip(),
            option_d=row['option_d'].strip(),
            correct_option=row['correct_option'].strip().lower(),
            difficulty=row['difficulty'].strip().lower(),
            explanation=row.get('explanation', '').strip() or None,
            tags=row.get('tags', '').strip() or None,
            created_by=current_user.id
        )
        db.session.add(q)
        imported += 1

    if row_errors:
        db.session.rollback()
        error_summary = '; '.join([f"Row {e['row']}: {', '.join(e['errors'])}" for e in row_errors[:5]])
        flash(f'Import failed. Fix {len(row_errors)} row(s). First errors: {error_summary}', 'error')
    else:
        db.session.commit()
        flash(f'Successfully imported {imported} questions from CSV.', 'success')

    return redirect(url_for('admin.questions'))


@admin_bp.route('/questions/import-json', methods=['POST'])
@admin_required
def import_questions_json():
    """Bulk import questions from JSON upload."""
    import json
    file = request.files.get('json_file')
    if not file or not file.filename:
        flash('Please select a JSON file to upload.', 'error')
        return redirect(url_for('admin.questions'))

    try:
        data = json.load(file)
        if not isinstance(data, list):
            flash('JSON root must be a list of question objects.', 'error')
            return redirect(url_for('admin.questions'))
        
        imported = 0
        for item in data:
            q = Question(
                subcategory_id=int(item.get('subcategory_id', 1)),
                question_text=str(item.get('question_text', '')).strip(),
                option_a=str(item.get('option_a', '')).strip(),
                option_b=str(item.get('option_b', '')).strip(),
                option_c=str(item.get('option_c', '')).strip(),
                option_d=str(item.get('option_d', '')).strip(),
                correct_option=str(item.get('correct_option', 'a')).strip().lower(),
                difficulty=str(item.get('difficulty', 'medium')).strip().lower(),
                explanation=str(item.get('explanation', '')).strip() or None,
                created_by=current_user.id
            )
            db.session.add(q)
            imported += 1
        
        db.session.commit()
        flash(f'Successfully imported {imported} questions from JSON.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Failed to parse JSON file: {str(e)}', 'error')

    return redirect(url_for('admin.questions'))


@admin_bp.route('/questions/import-api', methods=['POST'])
@admin_required
def import_questions_api():
    """Import questions from REST API endpoint."""
    import json, urllib.request
    api_url = request.form.get('api_url', '').strip()
    if not api_url:
        flash('Please provide a valid REST API URL.', 'error')
        return redirect(url_for('admin.questions'))

    try:
        req = urllib.request.Request(api_url, headers={'User-Agent': 'QuizNova/2.0'})
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode('utf-8'))
            
            # Handle dictionary wrapper if questions are nested under a key
            if isinstance(data, dict):
                data = data.get('questions') or data.get('results') or data.get('data') or []
                
            if not isinstance(data, list):
                flash('API response must return a list of questions.', 'error')
                return redirect(url_for('admin.questions'))

            imported = 0
            for item in data:
                q = Question(
                    subcategory_id=int(item.get('subcategory_id', 1)),
                    question_text=str(item.get('question_text', item.get('question', ''))).strip(),
                    option_a=str(item.get('option_a', '')).strip(),
                    option_b=str(item.get('option_b', '')).strip(),
                    option_c=str(item.get('option_c', '')).strip(),
                    option_d=str(item.get('option_d', '')).strip(),
                    correct_option=str(item.get('correct_option', 'a')).strip().lower(),
                    difficulty=str(item.get('difficulty', 'medium')).strip().lower(),
                    explanation=str(item.get('explanation', '')).strip() or None,
                    created_by=current_user.id
                )
                db.session.add(q)
                imported += 1

            db.session.commit()
            flash(f'Successfully fetched and imported {imported} questions from API!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'API import failed: {str(e)}', 'error')

    return redirect(url_for('admin.questions'))


@admin_bp.route('/questions/<int:question_id>/delete', methods=['POST', 'DELETE'])
@admin_required
def delete_question(question_id):
    """Safely delete a single question from the question bank with explicit dependency cleanup."""
    is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
              request.is_json or 
              request.content_type == 'application/json')
    
    q = Question.query.get(question_id)
    if not q:
        if is_ajax:
            return jsonify({'success': False, 'message': 'Question not found'}), 404
        flash('Question not found.', 'error')
        return redirect(url_for('admin.questions'))

    try:
        # Step 1: Find matching AttemptQuestion records
        matching_aqs = AttemptQuestion.query.filter_by(question_id=q.id).all()
        aq_ids = [aq.id for aq in matching_aqs]

        if aq_ids:
            # Step 2: Delete dependent AttemptAnswer records
            AttemptAnswer.query.filter(AttemptAnswer.attempt_question_id.in_(aq_ids)).delete(synchronize_session=False)
            # Step 3: Delete dependent AttemptQuestion records
            AttemptQuestion.query.filter(AttemptQuestion.id.in_(aq_ids)).delete(synchronize_session=False)

        # Step 4: Delete the Question itself
        sub_id = q.subcategory_id
        db.session.delete(q)
        db.session.commit()

        if is_ajax:
            return jsonify({'success': True, 'message': 'Question deleted successfully'})

        flash('Question deleted successfully.', 'success')
        return redirect(url_for('admin.questions', subcategory_id=sub_id if sub_id else ''))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting question {question_id}: {e}', exc_info=True)
        if is_ajax:
            return jsonify({'success': False, 'message': f'Failed to delete question: {str(e)}'}), 500
        flash(f'Failed to delete question: {str(e)}', 'error')
        return redirect(url_for('admin.questions'))


@admin_bp.route('/subcategories/<int:subcategory_id>/questions/delete-all', methods=['POST', 'DELETE'])
@admin_required
def delete_all_subcategory_questions(subcategory_id):
    """Safely delete all questions belonging to a specific subcategory with explicit dependency cleanup."""
    is_ajax = (request.headers.get('X-Requested-With') == 'XMLHttpRequest' or 
              request.is_json or 
              request.content_type == 'application/json')

    sub = Subcategory.query.get(subcategory_id)
    if not sub:
        if is_ajax:
            return jsonify({'success': False, 'message': 'Subcategory not found'}), 404
        flash('Subcategory not found.', 'error')
        return redirect(url_for('admin.questions'))

    try:
        sub_questions = Question.query.filter_by(subcategory_id=sub.id).all()
        q_ids = [q.id for q in sub_questions]
        deleted_count = len(q_ids)

        if deleted_count == 0:
            if is_ajax:
                return jsonify({
                    'success': True,
                    'message': 'No questions found in this subcategory',
                    'deleted_count': 0
                })
            flash('No questions found in this subcategory.', 'info')
            return redirect(url_for('admin.questions', subcategory_id=sub.id))

        # Step 1: Find matching AttemptQuestion records for all questions in this subcategory
        matching_aqs = AttemptQuestion.query.filter(AttemptQuestion.question_id.in_(q_ids)).all()
        aq_ids = [aq.id for aq in matching_aqs]

        if aq_ids:
            # Step 2: Delete dependent AttemptAnswer records
            AttemptAnswer.query.filter(AttemptAnswer.attempt_question_id.in_(aq_ids)).delete(synchronize_session=False)
            # Step 3: Delete dependent AttemptQuestion records
            AttemptQuestion.query.filter(AttemptQuestion.id.in_(aq_ids)).delete(synchronize_session=False)

        # Step 4: Delete ONLY Questions belonging to this subcategory
        Question.query.filter(Question.id.in_(q_ids)).delete(synchronize_session=False)
        db.session.commit()

        msg = f'All {deleted_count} questions from {sub.name} deleted successfully.'
        if is_ajax:
            return jsonify({
                'success': True,
                'message': msg,
                'deleted_count': deleted_count
            })

        flash(msg, 'success')
        return redirect(url_for('admin.questions', subcategory_id=sub.id))

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f'Error deleting all questions for subcategory {subcategory_id}: {e}', exc_info=True)
        if is_ajax:
            return jsonify({'success': False, 'message': f'Failed to delete questions: {str(e)}'}), 500
        flash(f'Failed to delete questions: {str(e)}', 'error')
        return redirect(url_for('admin.questions', subcategory_id=subcategory_id))


# =============================================================================
# User Management
# =============================================================================

@admin_bp.route('/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    role_filter = request.args.get('role', '')

    query = User.query
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) | (User.email.ilike(f'%{search}%'))
        )
    if role_filter in ('student', 'admin'):
        query = query.filter_by(role=role_filter)

    pagination = query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=current_app.config['ADMIN_USERS_PER_PAGE'], error_out=False
    )
    return render_template('admin/users.html', pagination=pagination,
                           search=search, role_filter=role_filter)


@admin_bp.route('/users/<int:user_id>/toggle-ban', methods=['POST'])
@admin_required
def toggle_ban(user_id):
    user = User.query.get_or_404(user_id)
    if user.is_admin:
        flash('Cannot ban an admin account.', 'error')
    else:
        user.is_active = not user.is_active
        db.session.commit()
        action = 'unbanned' if user.is_active else 'banned'
        flash(f'User {user.username} has been {action}.', 'success')
    return redirect(url_for('admin.users'))


# =============================================================================
# Certificate Management
# =============================================================================

@admin_bp.route('/certificates')
@admin_required
def certificates():
    page = request.args.get('page', 1, type=int)
    certs = Certificate.query.order_by(Certificate.created_at.desc()).paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('admin/certificates.html', pagination=certs)


@admin_bp.route('/certificates/<int:cert_id>/revoke', methods=['POST'])
@admin_required
def revoke_certificate(cert_id):
    cert = Certificate.query.get_or_404(cert_id)
    reason = request.form.get('reason', '').strip()
    cert.revoke(reason=reason)
    db.session.commit()
    flash(f'Certificate {cert.verification_id} has been revoked.', 'success')
    return redirect(url_for('admin.certificates'))


# =============================================================================
# Analytics
# =============================================================================

@admin_bp.route('/analytics')
@admin_required
def analytics():
    charts = get_analytics_charts()
    return render_template('admin/analytics.html', charts=charts)


# =============================================================================
# Data Export
# =============================================================================

@admin_bp.route('/export/<string:resource>')
@admin_required
def export_data(resource):
    """Export resource as a CSV download."""
    output = io.StringIO()
    writer = csv.writer(output)

    if resource == 'users':
        writer.writerow(['id', 'username', 'email', 'role', 'is_active', 'created_at'])
        for u in User.query.all():
            writer.writerow([u.id, u.username, u.email, u.role, u.is_active, u.created_at])
        filename = 'quiznova_users.csv'

    elif resource == 'results':
        writer.writerow(['id', 'user_id', 'subcategory_id', 'score', 'percentage',
                         'is_passed', 'created_at'])
        for r in Result.query.all():
            writer.writerow([r.id, r.user_id, r.subcategory_id, r.score,
                             r.percentage, r.is_passed, r.created_at])
        filename = 'quiznova_results.csv'

    elif resource == 'certificates':
        writer.writerow(['id', 'verification_id', 'user_id', 'issue_date', 'is_valid'])
        for c in Certificate.query.all():
            writer.writerow([c.id, c.verification_id, c.user_id, c.issue_date, c.is_valid])
        filename = 'quiznova_certificates.csv'

    else:
        flash('Unknown export resource.', 'error')
        return redirect(url_for('admin.dashboard'))

    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = f'attachment; filename={filename}'
    response.headers['Content-Type'] = 'text/csv'
    return response


# =============================================================================
# Competitions Management
# =============================================================================

@admin_bp.route('/competitions')
@admin_required
def competitions():
    """List all competitions for Admin."""
    from models.competition import Competition
    status_filter = request.args.get('status', 'all')
    
    query = Competition.query
    if status_filter in ('draft', 'published', 'live', 'completed'):
        query = query.filter_by(status=status_filter)
        
    competitions_list = query.order_by(Competition.created_at.desc()).all()
    categories = Category.query.filter_by(is_active=True).all()
    subcategories = Subcategory.query.filter_by(is_active=True).all()
    
    return render_template(
        'admin/competitions/list.html',
        competitions=competitions_list,
        categories=categories,
        subcategories=subcategories,
        status_filter=status_filter
    )


@admin_bp.route('/competitions/create', methods=['GET', 'POST'])
@admin_required
def create_competition():
    """Create a new Competition."""
    from models.competition import Competition, CompetitionQuestion

    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        if not title:
            flash('Competition title is required.', 'error')
            categories = Category.query.filter_by(is_active=True).all()
            return render_template('admin/competitions/create.html', categories=categories)

        short_desc = request.form.get('short_description', '').strip()
        full_desc = request.form.get('full_description', '').strip()
        cat_id = request.form.get('category_id', type=int) or None
        sub_id = request.form.get('subcategory_id', type=int) or None

        total_q = request.form.get('total_questions', 20, type=int)
        duration = request.form.get('duration_minutes', 45, type=int)
        passing = request.form.get('passing_marks', 60, type=int)
        max_p = request.form.get('max_participants', 1000, type=int)

        comp_type = request.form.get('comp_type', 'quiz')
        difficulty = request.form.get('difficulty', 'intermediate')

        prize_pool = request.form.get('prize_pool_text', u'\u20b91,00,000 Prize Pool').strip()
        prize_1st = request.form.get('prize_1st', u'🥇 Gold Trophy + \u20b950,000 + Certificate').strip()
        prize_2nd = request.form.get('prize_2nd', u'🥈 Silver Medal + \u20b930,000 + Certificate').strip()
        prize_3rd = request.form.get('prize_3rd', u'🥉 Bronze Medal + \u20b920,000 + Certificate').strip()
        sponsor = request.form.get('sponsor_name', 'QuizNova AI').strip()
        organizer = request.form.get('organizer_name', 'QuizNova Team').strip()
        rules_text = request.form.get('rules_text', '').strip()
        eligibility_text = request.form.get('eligibility_text', '').strip()
        banner_url = request.form.get('banner_url', '').strip() or None

        status = request.form.get('status', 'published')
        is_featured = bool(request.form.get('is_featured'))
        is_trending = bool(request.form.get('is_trending'))
        cert_enabled = bool(request.form.get('cert_enabled'))
        leaderboard_enabled = bool(request.form.get('leaderboard_enabled'))

        def parse_dt(field):
            val = request.form.get(field, '').strip()
            if val:
                try:
                    return datetime.strptime(val, '%Y-%m-%dT%H:%M')
                except ValueError:
                    pass
            return None

        reg_start = parse_dt('reg_start_date')
        reg_end = parse_dt('reg_end_date')
        start_dt = parse_dt('start_date') or datetime.utcnow()
        end_dt = parse_dt('end_date') or datetime(datetime.utcnow().year + 1, 12, 31)

        auto_slug = slugify(title)
        if Competition.query.filter_by(slug=auto_slug).first():
            auto_slug = f"{auto_slug}-{int(datetime.utcnow().timestamp())}"

        comp = Competition(
            title=title,
            slug=auto_slug,
            short_description=short_desc,
            full_description=full_desc,
            category_id=cat_id,
            subcategory_id=sub_id,
            total_questions=total_q,
            duration_minutes=duration,
            passing_marks=passing,
            max_participants=max_p,
            comp_type=comp_type,
            difficulty=difficulty,
            reg_start_date=reg_start,
            reg_end_date=reg_end,
            start_date=start_dt,
            end_date=end_dt,
            prize_pool_text=prize_pool,
            prize_1st=prize_1st,
            prize_2nd=prize_2nd,
            prize_3rd=prize_3rd,
            sponsor_name=sponsor,
            organizer_name=organizer,
            rules_text=rules_text,
            eligibility_text=eligibility_text,
            banner_url=banner_url,
            is_featured=is_featured,
            is_trending=is_trending,
            cert_enabled=cert_enabled,
            leaderboard_enabled=leaderboard_enabled,
            status=status
        )
        db.session.add(comp)
        db.session.commit()

        flash(f'Competition "{title}" created successfully! It is now {status}.', 'success')
        return redirect(url_for('admin.competitions'))

    categories = Category.query.filter_by(is_active=True).all()
    subcategories = Subcategory.query.filter_by(is_active=True).all()
    return render_template('admin/competitions/create.html', categories=categories, subcategories=subcategories)




@admin_bp.route('/competitions/<int:comp_id>/delete', methods=['POST'])
@admin_required
def delete_competition(comp_id):
    """Delete a Competition."""
    from models.competition import Competition
    comp = Competition.query.get_or_404(comp_id)
    db.session.delete(comp)
    db.session.commit()
    flash(f'Competition "{comp.title}" deleted.', 'success')
    return redirect(url_for('admin.competitions'))


# =============================================================================
# Competition — Edit
# =============================================================================

@admin_bp.route('/competitions/<int:comp_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_competition(comp_id):
    """Edit an existing Competition."""
    from models.competition import Competition
    comp = Competition.query.get_or_404(comp_id)
    categories = Category.query.filter_by(is_active=True).all()
    subcategories = Subcategory.query.filter_by(is_active=True).all()

    if request.method == 'POST':
        f = request.form

        comp.title             = f.get('title', comp.title).strip()
        comp.short_description = f.get('short_description', '').strip() or None
        comp.full_description  = f.get('full_description', '').strip() or None
        comp.rules_text        = f.get('rules_text', '').strip() or None
        comp.eligibility_text  = f.get('eligibility_text', '').strip() or None
        comp.prize_pool_text   = f.get('prize_pool_text', '').strip() or None
        comp.sponsor_name      = f.get('sponsor_name', '').strip() or None
        comp.organizer_name    = f.get('organizer_name', '').strip() or None
        comp.status            = f.get('status', comp.status)
        comp.is_featured       = bool(f.get('is_featured'))
        comp.is_trending       = bool(f.get('is_trending'))

        # Integer fields
        for attr, field in [
            ('category_id',      'category_id'),
            ('subcategory_id',   'subcategory_id'),
            ('total_questions',  'total_questions'),
            ('duration_minutes', 'duration_minutes'),
            ('passing_marks',    'passing_marks'),
            ('max_participants', 'max_participants'),
            ('prize_1st',        'prize_1st'),
            ('prize_2nd',        'prize_2nd'),
            ('prize_3rd',        'prize_3rd'),
        ]:
            raw = f.get(field, '').strip()
            if raw:
                try:
                    setattr(comp, attr, int(raw))
                except ValueError:
                    pass

        # Datetime-local fields (format: YYYY-MM-DDTHH:MM)
        for attr, field in [
            ('reg_start_date', 'reg_start_date'),
            ('reg_end_date',   'reg_end_date'),
            ('start_date',     'start_date'),
            ('end_date',       'end_date'),
        ]:
            raw = f.get(field, '').strip()
            if raw:
                try:
                    setattr(comp, attr, datetime.strptime(raw, '%Y-%m-%dT%H:%M'))
                except ValueError:
                    pass

        db.session.commit()
        flash(f'Competition "{comp.title}" updated successfully.', 'success')
        return redirect(url_for('admin.competitions'))

    return render_template('admin/competitions/edit.html',
                           comp=comp,
                           categories=categories,
                           subcategories=subcategories)


# =============================================================================
# Competition — Publish / Unpublish Toggle
# =============================================================================

@admin_bp.route('/competitions/<int:comp_id>/publish', methods=['POST'])
@admin_required
def publish_competition(comp_id):
    """Toggle a Competition between 'draft' and 'published' status."""
    from models.competition import Competition
    comp = Competition.query.get_or_404(comp_id)
    if comp.status == 'draft':
        comp.status = 'published'
        msg = f'Competition "{comp.title}" has been published.'
    else:
        comp.status = 'draft'
        msg = f'Competition "{comp.title}" moved back to draft.'
    db.session.commit()
    flash(msg, 'success')
    return redirect(url_for('admin.competitions'))


# =============================================================================
# Competition — Registrations View
# =============================================================================

@admin_bp.route('/competitions/<int:comp_id>/registrations')
@admin_required
def competition_registrations(comp_id):
    """View all students registered for a Competition."""
    from models.competition import Competition, CompetitionRegistration
    comp = Competition.query.get_or_404(comp_id)
    registrations = (
        CompetitionRegistration.query
        .filter_by(competition_id=comp_id)
        .all()
    )
    return render_template('admin/competitions/registrations.html',
                           comp=comp,
                           registrations=registrations)


# =============================================================================
# Competition — Export Registrations as CSV
# =============================================================================

@admin_bp.route('/competitions/<int:comp_id>/export')
@admin_required
def export_competition_registrations(comp_id):
    """Export all registrations for a Competition as a downloadable CSV."""
    from models.competition import Competition, CompetitionRegistration
    comp = Competition.query.get_or_404(comp_id)
    registrations = (
        CompetitionRegistration.query
        .filter_by(competition_id=comp_id)
        .all()
    )

    output = io.StringIO()
    writer = csv.writer(output)

    # Header row
    writer.writerow([
        'id', 'user_id', 'full_name', 'email',
        'phone', 'college', 'course', 'year',
        'state', 'city', 'registered_at',
    ])

    for reg in registrations:
        user = reg.user
        writer.writerow([
            reg.id,
            reg.user_id,
            getattr(user, 'full_name', '') or '',
            getattr(user, 'email', '') or '',
            getattr(user, 'phone', '') or '',
            getattr(user, 'college', '') or '',
            getattr(user, 'course', '') or '',
            getattr(user, 'year', '') or '',
            getattr(user, 'state', '') or '',
            getattr(user, 'city', '') or '',
            reg.registered_at.strftime('%Y-%m-%d %H:%M:%S') if reg.registered_at else '',
        ])

    csv_data = output.getvalue()
    output.close()

    safe_title = comp.title.replace(' ', '_').lower()
    filename = f'registrations_{safe_title}_{comp_id}.csv'

    response = make_response(csv_data)
    response.headers['Content-Type'] = 'text/csv; charset=utf-8'
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response
