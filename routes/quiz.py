"""
QuizNova — Quiz Routes Blueprint
===================================
Handles quiz browsing, starting, attempt flow, results, and leaderboard.
"""

from flask import (Blueprint, render_template, request, redirect,
                   url_for, flash, abort, current_app)
from flask_login import login_required, current_user
from models import db
from models.category import Category
from models.subcategory import Subcategory
from models.quiz import QuizAttempt, AttemptQuestion, AttemptAnswer
from models.result import Result
from models.log import ActivityLog, AntiCheatLog
from models.leaderboard import LeaderboardCache
from services.randomizer import select_questions, build_attempt_questions
from services.leaderboard import refresh_leaderboard_for_user
from services.achievement_service import check_and_award_achievements
from utils.decorators import quiz_owner_required, active_user_required
from utils.helpers import calculate_percentage

quiz_bp = Blueprint('quiz', __name__)


# =============================================================================
# Category & Subcategory Browsing
# =============================================================================

@quiz_bp.route('/categories', methods=['GET'])
@quiz_bp.route('/categories/', methods=['GET'])
@quiz_bp.route('/category', methods=['GET'])
@quiz_bp.route('/category/', methods=['GET'])
def categories():
    """Public category listing page."""
    cats = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()
    return render_template('quiz/categories.html', categories=cats)


@quiz_bp.route('/categories/<string:category_slug>', methods=['GET'])
@quiz_bp.route('/categories/<string:category_slug>/', methods=['GET'])
@quiz_bp.route('/category/<string:category_slug>', methods=['GET'])
@quiz_bp.route('/category/<string:category_slug>/', methods=['GET'])
def subcategories(category_slug):
    """Subcategory listing for a given category with robust slug/name/ID matching."""
    clean_slug = (category_slug or '').strip().lower()
    
    # 1. Exact or case-insensitive slug match
    category = Category.query.filter(
        db.func.lower(Category.slug) == clean_slug,
        Category.is_active == True
    ).first()

    # 2. Name match fallback (e.g. 'programming' -> 'Programming', 'web-development' -> 'Web Development')
    if not category:
        name_search = clean_slug.replace('-', ' ')
        category = Category.query.filter(
            db.func.lower(Category.name) == name_search,
            Category.is_active == True
        ).first()

    # 3. Numeric ID match fallback
    if not category and clean_slug.isdigit():
        category = Category.query.filter_by(id=int(clean_slug), is_active=True).first()

    if not category:
        abort(404)

    subs = (Subcategory.query
            .filter_by(category_id=category.id, is_active=True)
            .order_by(Subcategory.sort_order)
            .all())
    return render_template('quiz/subcategories.html', category=category, subcategories=subs)


# =============================================================================
# Quiz Start
# =============================================================================

@quiz_bp.route('/start/<int:subcategory_id>', methods=['POST'])
@login_required
@active_user_required
def start(subcategory_id):
    """Start a new quiz attempt for the given subcategory."""
    sub = Subcategory.query.filter_by(id=subcategory_id, is_active=True).first_or_404()

    if not sub.has_enough_questions:
        flash(f'Not enough questions available for {sub.name}. Please try again later.', 'error')
        return redirect(url_for('quiz.subcategories', category_slug=sub.category.slug))

    # Create attempt record
    attempt = QuizAttempt(
        user_id=current_user.id,
        subcategory_id=sub.id,
        ip_address=request.remote_addr,
        user_agent=request.user_agent.string[:255],
    )
    db.session.add(attempt)
    db.session.flush()  # Get attempt.id

    # Randomize questions and build snapshot
    selected = select_questions(sub.id, sub.questions_per_quiz, user_id=current_user.id)
    attempt_questions = build_attempt_questions(attempt.id, selected)
    db.session.add_all(attempt_questions)

    # Log activity
    log = ActivityLog(
        user_id=current_user.id,
        event_type='quiz_started',
        entity_type='quiz_attempt',
        entity_id=attempt.id,
        description=f'Started {sub.name} quiz'
    )
    db.session.add(log)
    db.session.commit()

    return redirect(url_for('quiz.attempt', attempt_id=attempt.id))


# =============================================================================
# Quiz Attempt Interface
# =============================================================================

@quiz_bp.route('/attempt/<int:attempt_id>')
@login_required
@quiz_owner_required
def attempt(attempt_id):
    """Quiz taking interface — fullscreen with anti-cheat."""
    quiz_attempt = QuizAttempt.query.get_or_404(attempt_id)

    if not quiz_attempt.is_in_progress:
        if quiz_attempt.is_submitted:
            return redirect(url_for('quiz.result', attempt_id=attempt_id))
        abort(400)

    # Collect current answers for state recovery
    existing_answers = {}
    for ans in quiz_attempt.attempt_answers:
        existing_answers[ans.attempt_question_id] = ans.selected_index

    questions = (AttemptQuestion.query
                 .filter_by(attempt_id=attempt_id)
                 .order_by(AttemptQuestion.question_order)
                 .all())

    sub = quiz_attempt.subcategory
    max_violations = current_app.config['QUIZ_MAX_VIOLATIONS']

    return render_template(
        'quiz/attempt.html',
        attempt=quiz_attempt,
        questions=questions,
        existing_answers=existing_answers,
        subcategory=sub,
        time_limit_seconds=sub.time_limit_seconds,
        max_violations=max_violations,
    )


# =============================================================================
# Quiz Submission
# =============================================================================

@quiz_bp.route('/submit/<int:attempt_id>', methods=['POST'])
@login_required
@quiz_owner_required
def submit(attempt_id):
    """Process manual quiz submission."""
    quiz_attempt = QuizAttempt.query.get_or_404(attempt_id)

    if not quiz_attempt.is_in_progress:
        flash('This quiz has already been submitted.', 'warning')
        return redirect(url_for('quiz.result', attempt_id=attempt_id))

    auto_submitted = request.form.get('auto_submitted', 'false').lower() == 'true'
    _process_submission(quiz_attempt, auto_submitted=auto_submitted)

    return redirect(url_for('quiz.result', attempt_id=attempt_id))


def _process_submission(quiz_attempt: QuizAttempt, auto_submitted: bool = False) -> Result:
    """
    Internal function: score the attempt, create Result, update leaderboard.
    Wrapped in a DB transaction.

    Args:
        quiz_attempt: The QuizAttempt to finalize.
        auto_submitted: True if triggered by timer or anti-cheat.

    Returns:
        The created Result object.
    """
    quiz_attempt.submit(auto=auto_submitted)

    aq_list = (AttemptQuestion.query
               .filter_by(attempt_id=quiz_attempt.id)
               .order_by(AttemptQuestion.question_order)
               .all())

    correct = wrong = skipped = 0
    total = len(aq_list)

    for aq in aq_list:
        ans = AttemptAnswer.query.filter_by(
            attempt_id=quiz_attempt.id,
            attempt_question_id=aq.id
        ).first()

        if ans is None:
            # No answer recorded — count as skipped
            skipped += 1
            ans = AttemptAnswer(
                attempt_id=quiz_attempt.id,
                attempt_question_id=aq.id,
                selected_index=None,
                is_correct=False,
            )
            db.session.add(ans)
        else:
            ans.evaluate(aq.correct_shuffled_index)
            if ans.is_correct:
                correct += 1
            elif ans.selected_index is None:
                skipped += 1
            else:
                wrong += 1

    percentage = calculate_percentage(correct, total)
    sub = quiz_attempt.subcategory
    is_passed = percentage >= sub.pass_threshold

    result = Result(
        attempt_id=quiz_attempt.id,
        user_id=quiz_attempt.user_id,
        subcategory_id=quiz_attempt.subcategory_id,
        total_questions=total,
        correct_count=correct,
        wrong_count=wrong,
        skipped_count=skipped,
        score=correct,
        max_score=total,
        percentage=percentage,
        is_passed=is_passed,
    )
    db.session.add(result)
    db.session.flush()

    # Update leaderboard cache
    refresh_leaderboard_for_user(quiz_attempt.user_id, quiz_attempt.subcategory_id)

    # Log activity
    log = ActivityLog(
        user_id=quiz_attempt.user_id,
        event_type='quiz_completed',
        entity_type='quiz_attempt',
        entity_id=quiz_attempt.id,
        description=f'Completed {sub.name} — {percentage:.1f}% | {"Passed" if is_passed else "Failed"}'
    )
    db.session.add(log)
    db.session.commit()

    # Check achievements (after commit so counts are accurate)
    check_and_award_achievements(quiz_attempt.user_id, result)

    # Auto-generate certificate if passed
    if is_passed:
        from services.certificate_service import generate_certificate
        try:
            generate_certificate(result.id)
        except Exception as e:
            current_app.logger.error(f'Certificate generation failed for result {result.id}: {e}')

    return result


# =============================================================================
# Result Page
# =============================================================================

@quiz_bp.route('/result/<int:attempt_id>')
@login_required
@quiz_owner_required
def result(attempt_id):
    """Result page after quiz submission."""
    quiz_attempt = QuizAttempt.query.get_or_404(attempt_id)

    if not quiz_attempt.is_submitted:
        return redirect(url_for('quiz.attempt', attempt_id=attempt_id))

    result = Result.query.filter_by(attempt_id=attempt_id).first_or_404()
    return render_template('quiz/result.html', attempt=quiz_attempt, result=result)


# =============================================================================
# Review Page
# =============================================================================

@quiz_bp.route('/review/<int:attempt_id>')
@login_required
@quiz_owner_required
def review(attempt_id):
    """Question-by-question review with explanations."""
    quiz_attempt = QuizAttempt.query.get_or_404(attempt_id)

    if not quiz_attempt.is_submitted:
        flash('Please complete the quiz before reviewing.', 'warning')
        return redirect(url_for('quiz.attempt', attempt_id=attempt_id))

    aq_list = (AttemptQuestion.query
               .filter_by(attempt_id=attempt_id)
               .order_by(AttemptQuestion.question_order)
               .all())

    questions_review = []
    for aq in aq_list:
        ans = AttemptAnswer.query.filter_by(
            attempt_id=attempt_id,
            attempt_question_id=aq.id
        ).first()
        selected_index = ans.selected_index if ans and ans.selected_index is not None else -1
        is_correct = ans.is_correct if ans else False
        questions_review.append({
            'question_text': aq.question.question_text if aq.question else '',
            'options': aq.options,
            'correct_index': aq.correct_shuffled_index,
            'selected_index': selected_index,
            'is_correct': is_correct,
            'explanation': (aq.question.explanation if aq.question else '') or 'No explanation provided.',
        })

    result = Result.query.filter_by(attempt_id=attempt_id).first_or_404()
    return render_template('quiz/review.html',
                           attempt=quiz_attempt,
                           result=result,
                           questions_review=questions_review)


# =============================================================================
# Leaderboard
# =============================================================================

@quiz_bp.route('/leaderboard')
def leaderboard():
    """Global and category-specific leaderboard."""
    scope = request.args.get('scope', 'global')
    subcategory_id = request.args.get('subcategory_id', type=int)
    page = request.args.get('page', 1, type=int)

    query = (LeaderboardCache.query
             .filter_by(subcategory_id=subcategory_id)
             .order_by(LeaderboardCache.total_score.desc()))

    pagination = query.paginate(page=page, per_page=50, error_out=False)
    categories = Category.query.filter_by(is_active=True).all()

    current_rank = None
    if current_user.is_authenticated:
        entry = LeaderboardCache.query.filter_by(
            user_id=current_user.id,
            subcategory_id=subcategory_id
        ).first()
        current_rank = entry.rank_position if entry else None

    return render_template(
        'quiz/leaderboard.html',
        pagination=pagination,
        categories=categories,
        current_rank=current_rank,
        scope=scope,
        subcategory_id=subcategory_id,
    )
