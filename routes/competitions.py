"""
QuizNova — Competitions Blueprint
===================================
Public and user routes for browsing, registering, starting, and viewing leaderboards
for QuizNova Coding & Quiz Competitions.
"""

from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user

from models import db
from models.category import Category
from models.subcategory import Subcategory
from models.question import Question
from models.quiz import QuizAttempt, AttemptQuestion
from models.result import Result
from models.competition import (Competition, CompetitionQuestion, CompetitionRegistration,
                                CompetitionResult, CompetitionWinner)
from utils.helpers import slugify

competitions_bp = Blueprint('competitions', __name__)


@competitions_bp.route('/')
def index():
    """Competitions listing page with Trending, Featured, Live, Upcoming, Completed."""
    now = datetime.utcnow()
    
    # Filter by query tab if provided
    tab = request.args.get('tab', 'all')
    query = Competition.query.filter(Competition.status != 'draft')
    
    if tab == 'live':
        query = query.filter(Competition.start_date <= now, Competition.end_date >= now)
    elif tab == 'upcoming':
        query = query.filter(Competition.start_date > now)
    elif tab == 'completed':
        query = query.filter(Competition.end_date < now)
    elif tab == 'featured':
        query = query.filter_by(is_featured=True)

    competitions = query.order_by(Competition.start_date.desc()).all()
    
    # Key Highlights
    live_comps = [c for c in competitions if c.current_status == 'live']
    upcoming_comps = [c for c in competitions if c.current_status == 'upcoming']
    featured_comps = [c for c in competitions if c.is_featured]
    trending_comps = [c for c in competitions if c.is_trending]
    
    user_registrations = set()
    if current_user.is_authenticated:
        user_registrations = set(
            reg.competition_id for reg in CompetitionRegistration.query.filter_by(user_id=current_user.id).all()
        )

    return render_template(
        'competitions/index.html',
        competitions=competitions,
        live_comps=live_comps,
        upcoming_comps=upcoming_comps,
        featured_comps=featured_comps,
        trending_comps=trending_comps,
        user_registrations=user_registrations,
        active_tab=tab,
        now=now
    )


@competitions_bp.route('/<string:slug>')
def detail(slug):
    """Competition details page."""
    comp = Competition.query.filter_by(slug=slug).first_or_404()
    now = datetime.utcnow()
    
    is_registered = False
    has_attempted = False
    result = None
    
    if current_user.is_authenticated:
        reg = CompetitionRegistration.query.filter_by(competition_id=comp.id, user_id=current_user.id).first()
        is_registered = bool(reg)
        
        result = CompetitionResult.query.filter_by(competition_id=comp.id, user_id=current_user.id).first()
        has_attempted = bool(result)

    return render_template(
        'competitions/detail.html',
        comp=comp,
        now=now,
        is_registered=is_registered,
        has_attempted=has_attempted,
        result=result
    )


@competitions_bp.route('/<string:slug>/register', methods=['POST'])
@login_required
def register(slug):
    """Register student for competition with full profile form."""
    comp = Competition.query.filter_by(slug=slug).first_or_404()
    now = datetime.utcnow()

    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.accept_mimetypes.accept_json

    # Check registration dates
    if comp.reg_end_date and now > comp.reg_end_date:
        msg = 'Registration for this competition has closed.'
        if is_ajax: return jsonify({'success': False, 'message': msg}), 400
        flash(msg, 'error')
        return redirect(url_for('competitions.detail', slug=slug))

    if comp.max_participants and comp.registered_count >= comp.max_participants:
        msg = 'Maximum participant limit reached for this competition.'
        if is_ajax: return jsonify({'success': False, 'message': msg}), 400
        flash(msg, 'error')
        return redirect(url_for('competitions.detail', slug=slug))

    # Duplicate registration check
    existing = CompetitionRegistration.query.filter_by(competition_id=comp.id, user_id=current_user.id).first()
    if existing:
        msg = 'You are already registered for this competition!'
        if is_ajax: return jsonify({'success': True, 'message': msg, 'already_registered': True}), 200
        flash(msg, 'info')
        return redirect(url_for('competitions.detail', slug=slug))

    # Build registration record with form data
    reg = CompetitionRegistration(
        competition_id=comp.id,
        user_id=current_user.id,
        full_name=request.form.get('full_name', current_user.display_name),
        email=request.form.get('email', current_user.email),
        phone=request.form.get('phone', ''),
        gender=request.form.get('gender', ''),
        date_of_birth=request.form.get('date_of_birth', ''),
        country=request.form.get('country', 'India'),
        state=request.form.get('state', ''),
        city=request.form.get('city', ''),
        college=request.form.get('college', ''),
        department=request.form.get('department', ''),
        course=request.form.get('course', ''),
        year_of_study=request.form.get('year_of_study', ''),
        usn_roll=request.form.get('usn_roll', ''),
        linkedin_url=request.form.get('linkedin_url', ''),
        github_url=request.form.get('github_url', ''),
    )
    db.session.add(reg)
    db.session.commit()

    # Send Competition Registration Email
    try:
        from services.email_service import send_html_email
        site_url = (current_app.config.get('SITE_URL') or 'https://quiz-nova-nu.vercel.app').rstrip('/')
        send_html_email(
            to_email=reg.email,
            subject="Competition Registration Confirmed 🏆",
            template_name="competition_registration.html",
            context={
                'participant_name': reg.full_name,
                'competition_title': comp.title,
                'start_date': comp.start_date.strftime('%d %B %Y') if comp.start_date else 'TBA',
                'reg_end_date': comp.reg_end_date.strftime('%d %B %Y') if comp.reg_end_date else 'TBA',
                'competition_url': f"{site_url}/competitions/{comp.slug}"
            },
            notification_type="competition_registration",
            related_object_id=str(reg.id)
        )
    except Exception as mail_err:
        current_app.logger.warning(f"Competition registration email warning: {mail_err}")

    msg = f'🎉 Successfully registered for {comp.title}! Your Registration ID: QN-{reg.id:05d}'
    if is_ajax:
        return jsonify({'success': True, 'message': msg, 'reg_id': f'QN-{reg.id:05d}'})
    flash(msg, 'success')
    return redirect(url_for('competitions.detail', slug=slug))




@competitions_bp.route('/<string:slug>/start', methods=['POST'])
@login_required
def start(slug):
    """Start competition attempt."""
    comp = Competition.query.filter_by(slug=slug).first_or_404()
    now = datetime.utcnow()

    # Verify registration & start time
    reg = CompetitionRegistration.query.filter_by(competition_id=comp.id, user_id=current_user.id).first()
    if not reg and not current_user.is_admin:
        flash('You must be registered to start this competition.', 'error')
        return redirect(url_for('competitions.detail', slug=slug))

    if now < comp.start_date:
        flash('Competition has not started yet. Please wait for the start time.', 'warning')
        return redirect(url_for('competitions.detail', slug=slug))

    if now > comp.end_date:
        flash('Competition has concluded.', 'info')
        return redirect(url_for('competitions.detail', slug=slug))

    # Check existing attempt
    existing_result = CompetitionResult.query.filter_by(competition_id=comp.id, user_id=current_user.id).first()
    if existing_result:
        flash('You have already completed your attempt for this competition.', 'warning')
        return redirect(url_for('competitions.detail', slug=slug))

    # Find or fallback subcategory
    sub_id = comp.subcategory_id or 1

    # Create QuizAttempt using existing subcategory engine
    attempt = QuizAttempt(
        user_id=current_user.id,
        subcategory_id=sub_id,
        status='in_progress',
        started_at=now,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string[:250] if request.user_agent else ''
    )
    db.session.add(attempt)
    db.session.flush()

    # Assign specific competition questions if mapped, or sample subcategory questions
    comp_questions = [cq.question for cq in comp.questions if cq.question]
    if not comp_questions:
        comp_questions = Question.query.filter_by(subcategory_id=sub_id, is_active=True).limit(comp.total_questions).all()

    for idx, q in enumerate(comp_questions[:comp.total_questions], start=1):
        aq = AttemptQuestion(
            attempt_id=attempt.id,
            question_id=q.id,
            question_order=idx,
            correct_shuffled_index=0
        )
        aq.options = [q.option_a, q.option_b, q.option_c, q.option_d]
        db.session.add(aq)

    db.session.commit()
    return redirect(url_for('quiz.attempt_room', attempt_id=attempt.id))


@competitions_bp.route('/<string:slug>/leaderboard')
def leaderboard(slug):
    """Competition Leaderboard and Podium Winners."""
    comp = Competition.query.filter_by(slug=slug).first_or_404()
    
    # Leaderboard entries ordered by score desc, time taken asc
    results = CompetitionResult.query.filter_by(competition_id=comp.id)\
                .order_by(CompetitionResult.score.desc(), CompetitionResult.time_taken_seconds.asc())\
                .all()

    winners = CompetitionWinner.query.filter_by(competition_id=comp.id).order_by(CompetitionWinner.rank_position.asc()).all()

    return render_template(
        'competitions/leaderboard.html',
        comp=comp,
        results=results,
        winners=winners
    )
