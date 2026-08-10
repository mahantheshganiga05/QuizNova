"""
QuizNova — REST API Blueprint
================================
JSON API endpoints consumed by JavaScript for quiz interaction,
dashboard data, and admin operations.
"""

from flask import Blueprint, jsonify, request, current_app, send_file
from flask_login import login_required, current_user
from models import db
from models.quiz import QuizAttempt, AttemptQuestion, AttemptAnswer
from models.result import Result
from models.certificate import Certificate
from models.log import AntiCheatLog, ActivityLog
from models.leaderboard import LeaderboardCache
from models.category import Category
from services.randomizer import serialize_attempt_questions_for_client
from services.leaderboard import refresh_leaderboard_for_user
from services.analytics import get_user_stats, get_category_progress, get_user_activity
from utils.decorators import quiz_owner_required, admin_required

api_bp = Blueprint('api', __name__)


def success(data=None, message=None, status=200):
    """Standardized success JSON response."""
    resp = {'success': True}
    if data is not None:
        resp['data'] = data
    if message:
        resp['message'] = message
    return jsonify(resp), status


def error(code, message, details=None, status=400):
    """Standardized error JSON response."""
    resp = {'success': False, 'error': {'code': code, 'message': message}}
    if details:
        resp['error']['details'] = details
    return jsonify(resp), status


# =============================================================================
# Quiz API
# =============================================================================

@api_bp.route('/quiz/<int:attempt_id>/state', methods=['GET'])
@login_required
@quiz_owner_required
def quiz_state(attempt_id):
    """Return full quiz state for page-refresh recovery."""
    attempt = QuizAttempt.query.get_or_404(attempt_id)

    if not attempt.is_in_progress:
        return error('QUIZ_NOT_IN_PROGRESS', 'This quiz attempt is no longer in progress.', status=400)

    from datetime import datetime
    elapsed = int((datetime.utcnow() - attempt.started_at).total_seconds())
    time_limit = attempt.subcategory.time_limit_seconds
    seconds_remaining = max(0, time_limit - elapsed)

    existing_answers = {}
    bookmarks = []
    for aq in attempt.attempt_questions:
        if aq.answer and aq.answer.selected_index is not None:
            existing_answers[aq.id] = aq.answer.selected_index
        if aq.is_bookmarked:
            bookmarks.append(aq.id)

    return success({
        'attempt_id': attempt_id,
        'status': attempt.status,
        'seconds_remaining': seconds_remaining,
        'violation_count': attempt.violation_count,
        'answers': existing_answers,
        'bookmarks': bookmarks,
    })


@api_bp.route('/quiz/<int:attempt_id>/save-answer', methods=['POST'])
@login_required
@quiz_owner_required
def save_answer(attempt_id):
    """Save or update a single answer during the quiz."""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    if not attempt.is_in_progress:
        return error('QUIZ_NOT_IN_PROGRESS', 'Quiz is not in progress.', status=400)

    data = request.get_json(force=True) or {}
    aq_id = data.get('attempt_question_id')
    selected_index = data.get('selected_index')  # int 0-3 or null

    aq = AttemptQuestion.query.filter_by(id=aq_id, attempt_id=attempt_id).first()
    if not aq:
        return error('NOT_FOUND', 'Question not found in this attempt.', status=404)

    if selected_index is not None and selected_index not in (0, 1, 2, 3):
        return error('VALIDATION_ERROR', 'selected_index must be 0, 1, 2, or 3, or null.')

    ans = AttemptAnswer.query.filter_by(attempt_id=attempt_id, attempt_question_id=aq_id).first()
    if ans:
        ans.selected_index = selected_index
        from datetime import datetime
        ans.answered_at = datetime.utcnow()
    else:
        from datetime import datetime
        ans = AttemptAnswer(
            attempt_id=attempt_id,
            attempt_question_id=aq_id,
            selected_index=selected_index,
            answered_at=datetime.utcnow()
        )
        db.session.add(ans)

    db.session.commit()
    return success(message='Answer saved.')


@api_bp.route('/quiz/<int:attempt_id>/bookmark', methods=['POST'])
@login_required
@quiz_owner_required
def toggle_bookmark(attempt_id):
    """Toggle the bookmark flag on an attempt question."""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    if not attempt.is_in_progress:
        return error('QUIZ_NOT_IN_PROGRESS', 'Quiz is not in progress.', status=400)

    data = request.get_json(force=True) or {}
    aq_id = data.get('attempt_question_id')
    is_bookmarked = bool(data.get('is_bookmarked', False))

    aq = AttemptQuestion.query.filter_by(id=aq_id, attempt_id=attempt_id).first()
    if not aq:
        return error('NOT_FOUND', 'Question not found in this attempt.', status=404)

    aq.is_bookmarked = is_bookmarked
    db.session.commit()
    return success({'is_bookmarked': is_bookmarked})


@api_bp.route('/quiz/<int:attempt_id>/report-violation', methods=['POST'])
@login_required
@quiz_owner_required
def report_violation(attempt_id):
    """Log an anti-cheat violation. Auto-submit if threshold reached."""
    attempt = QuizAttempt.query.get_or_404(attempt_id)
    if not attempt.is_in_progress:
        return success({'violation_count': attempt.violation_count,
                        'max_violations': current_app.config['QUIZ_MAX_VIOLATIONS'],
                        'auto_submit': False})

    data = request.get_json(force=True) or {}
    event_type = data.get('event_type', 'tab_switch')
    valid_types = AntiCheatLog.EVENT_TYPES
    if event_type not in valid_types:
        event_type = 'tab_switch'

    import json
    log = AntiCheatLog(
        attempt_id=attempt_id,
        event_type=event_type,
        meta=json.dumps(data.get('meta', {}))
    )
    db.session.add(log)

    new_count = attempt.increment_violation()
    db.session.commit()

    max_v = current_app.config['QUIZ_MAX_VIOLATIONS']
    should_auto_submit = new_count >= max_v

    if should_auto_submit:
        from routes.quiz import _process_submission
        _process_submission(attempt, auto_submitted=True)

    return success({
        'violation_count': new_count,
        'max_violations': max_v,
        'auto_submit': should_auto_submit,
        'redirect_url': f'/quiz/result/{attempt_id}' if should_auto_submit else None,
    })


# =============================================================================
# Result API
# =============================================================================

@api_bp.route('/result/<int:attempt_id>', methods=['GET'])
@login_required
@quiz_owner_required
def get_result(attempt_id):
    """Get full result data for a completed attempt."""
    result = Result.query.filter_by(attempt_id=attempt_id).first()
    if not result:
        return error('NOT_FOUND', 'Result not found for this attempt.', status=404)

    return success({
        'result': {
            'id': result.id,
            'total_questions': result.total_questions,
            'correct_count': result.correct_count,
            'wrong_count': result.wrong_count,
            'skipped_count': result.skipped_count,
            'score': result.score,
            'max_score': result.max_score,
            'percentage': float(result.percentage),
            'rank': result.rank_at_time,
            'is_passed': result.is_passed,
            'grade': result.grade,
            'performance_level': result.performance_level,
        },
        'certificate_available': result.is_passed,
        'certificate_id': result.certificate.id if result.has_certificate else None,
    })


# =============================================================================
# Certificate API
# =============================================================================

@api_bp.route('/certificate/<int:cert_id>/download', methods=['GET'])
@login_required
def download_certificate(cert_id):
    """Download a certificate PDF. Validates ownership."""
    cert = Certificate.query.get_or_404(cert_id)

    if cert.user_id != current_user.id and not current_user.is_admin:
        from flask import abort
        abort(403)

    if not cert.is_valid:
        return error('CERTIFICATE_REVOKED', 'This certificate has been revoked.', status=400)

    import os
    file_path = os.path.join(current_app.root_path, cert.file_path or '')
    if not cert.file_path or not os.path.exists(file_path):
        return error('NOT_FOUND', 'Certificate file not found. Please regenerate.', status=404)

    cert.record_download()
    log = ActivityLog(
        user_id=current_user.id,
        event_type='certificate_downloaded',
        entity_type='certificate',
        entity_id=cert.id,
        description=f'Downloaded certificate {cert.verification_id}'
    )
    db.session.add(log)
    db.session.commit()

    return send_file(
        file_path,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'QuizNova_Certificate_{cert.verification_id}.pdf'
    )


# =============================================================================
# Dashboard API
# =============================================================================

@api_bp.route('/dashboard/stats', methods=['GET'])
@login_required
def dashboard_stats():
    stats = get_user_stats(current_user.id)
    return success(stats)


@api_bp.route('/dashboard/progress', methods=['GET'])
@login_required
def dashboard_progress():
    progress = get_category_progress(current_user.id)
    return success({'progress': progress})


@api_bp.route('/dashboard/activity', methods=['GET'])
@login_required
def dashboard_activity():
    limit = request.args.get('limit', 10, type=int)
    activities = get_user_activity(current_user.id, limit=limit)
    return success({'activities': activities})


# =============================================================================
# Leaderboard API
# =============================================================================

@api_bp.route('/leaderboard', methods=['GET'])
def leaderboard_data():
    subcategory_id = request.args.get('subcategory_id', type=int)
    page = request.args.get('page', 1, type=int)

    query = (LeaderboardCache.query
             .filter_by(subcategory_id=subcategory_id)
             .order_by(LeaderboardCache.total_score.desc()))

    pagination = query.paginate(page=page, per_page=50, error_out=False)

    entries = []
    for entry in pagination.items:
        entries.append({
            'rank': entry.rank_position,
            'user_id': entry.user_id,
            'username': entry.user.username,
            'full_name': entry.user.full_name,
            'profile_photo_url': entry.user.profile_photo_url,
            'total_score': entry.total_score,
            'quiz_count': entry.quiz_count,
            'best_percentage': float(entry.best_percentage),
        })

    return success({
        'leaderboard': entries,
        'total': pagination.total,
        'page': page,
        'has_next': pagination.has_next,
    })


# =============================================================================
# AI Stub Endpoints (v1 — returns 501 Not Implemented)
# =============================================================================

@api_bp.route('/ai/generate-question', methods=['POST'])
@login_required
def ai_generate_question():
    """AI question generation stub — Gemini API integration (v2)."""
    return jsonify({
        'success': False,
        'error': {
            'code': 'NOT_IMPLEMENTED',
            'message': 'AI question generation is coming soon. Powered by Google Gemini.',
            'eta': 'Q3 2026'
        }
    }), 501


@api_bp.route('/ai/explain', methods=['POST'])
@login_required
def ai_explain():
    """AI explanation stub — (v2)."""
    return jsonify({
        'success': False,
        'error': {'code': 'NOT_IMPLEMENTED', 'message': 'AI explanations coming soon.', 'eta': 'Q3 2026'}
    }), 501


@api_bp.route('/ai/skill-gap', methods=['POST'])
@login_required
def ai_skill_gap():
    """AI skill gap analysis stub — (v2)."""
    return jsonify({
        'success': False,
        'error': {'code': 'NOT_IMPLEMENTED', 'message': 'AI skill gap analysis coming soon.', 'eta': 'Q3 2026'}
    }), 501


@api_bp.route('/ai/roadmap', methods=['POST'])
@login_required
def ai_roadmap():
    """AI study roadmap stub — (v2)."""
    return jsonify({
        'success': False,
        'error': {'code': 'NOT_IMPLEMENTED', 'message': 'AI study roadmap coming soon.', 'eta': 'Q3 2026'}
    }), 501
