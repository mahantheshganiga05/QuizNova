"""
QuizNova — Dashboard Routes Blueprint
=======================================
Authenticated user dashboard: stats, achievements, certificates, settings.
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db
from models.result import Result
from models.certificate import Certificate
from models.log import ActivityLog, AchievementEarned, Achievement
from models.leaderboard import LeaderboardCache
from models.subcategory import Subcategory
from services.analytics import get_user_stats, get_category_progress, get_recommended_quizzes, _calculate_streak
from utils.decorators import active_user_required

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
@active_user_required
def index():
    """Live production student dashboard with real DB stats, charts, competitions, leaderboard, certificates and notifications."""
    from datetime import datetime, timedelta
    from models.competition import Competition, CompetitionRegistration
    from models.user import User
    from models.category import Category
    from models.subcategory import Subcategory
    from models.quiz import QuizAttempt

    now = datetime.utcnow()
    user_id = current_user.id

    # 1. Real User Results & Stats
    results = Result.query.filter_by(user_id=user_id).order_by(Result.created_at.asc()).all()
    total_quizzes = len(results)
    avg_score = round(sum(float(r.percentage) for r in results) / total_quizzes, 1) if total_quizzes > 0 else 0.0
    total_points = sum(int(r.score) for r in results) if results else 0
    current_level = (total_points // 500) + 1

    # Real Streak
    streak_days = _calculate_streak(user_id)

    # Real Competitions Joined
    competitions_joined = CompetitionRegistration.query.filter_by(user_id=user_id).count()

    # Real Certificates Earned
    certificates_count = Certificate.query.filter_by(user_id=user_id, is_valid=True).count()
    user_certificates = (Certificate.query
                        .filter_by(user_id=user_id, is_valid=True)
                        .order_by(Certificate.created_at.desc())
                        .limit(4)
                        .all())

    # Real Global Rank
    global_rank_entry = LeaderboardCache.query.filter_by(user_id=user_id, subcategory_id=None).first()
    if global_rank_entry:
        global_rank = global_rank_entry.rank_position
    else:
        # Calculate rank based on total_points among all users
        higher_users = (db.session.query(db.func.sum(Result.score))
                        .filter(Result.user_id != user_id)
                        .group_by(Result.user_id)
                        .having(db.func.sum(Result.score) > total_points)
                        .count())
        global_rank = higher_users + 1

    # 2. Performance Analytics (Real Score History for Chart)
    chart_labels = []
    chart_scores = []
    for r in results[-10:]:
        chart_labels.append(r.created_at.strftime('%b %d') if r.created_at else 'Quiz')
        chart_scores.append(round(float(r.percentage), 1))

    # Fallback default empty state structure if 0 results
    if not chart_labels:
        chart_labels = ['No Quizzes Taken Yet']
        chart_scores = [0]

    # 3. Real Category Performance
    all_categories = Category.query.filter_by(is_active=True).all()
    cat_performance = []
    for cat in all_categories:
        # query average score for user in this category
        cat_avg = (db.session.query(db.func.avg(Result.percentage), db.func.count(Result.id))
                   .join(Subcategory, Subcategory.id == Result.subcategory_id)
                   .filter(Subcategory.category_id == cat.id, Result.user_id == user_id)
                   .first())
        avg_pct = round(float(cat_avg[0]), 1) if cat_avg and cat_avg[0] is not None else 0.0
        quiz_count = cat_avg[1] if cat_avg else 0
        cat_performance.append({
            'name': cat.name,
            'color': cat.color_hex or '#7C3AED',
            'avg_score': avg_pct,
            'count': quiz_count
        })

    # 4. Real Recent Activity
    recent_activity = (ActivityLog.query
                       .filter_by(user_id=user_id)
                       .order_by(ActivityLog.created_at.desc())
                       .limit(8)
                       .all())

    # 5. Real Recommended Quizzes (Subcategories)
    recommended_subs = (Subcategory.query
                        .filter_by(is_active=True)
                        .limit(6)
                        .all())

    # 6. Real Upcoming Competitions from DB
    upcoming_competitions = (Competition.query
                            .filter(Competition.status.in_(['published', 'live']))
                            .order_by(Competition.start_date.asc())
                            .limit(3)
                            .all())

    # 7. Real Leaderboard Preview Top 5 Users
    top_leaderboard_users = (db.session.query(
                                User,
                                db.func.coalesce(db.func.sum(Result.score), 0).label('user_xp'),
                                db.func.coalesce(db.func.avg(Result.percentage), 0).label('user_avg')
                             )
                             .outerjoin(Result, Result.user_id == User.id)
                             .filter(User.is_active == True)
                             .group_by(User.id)
                             .order_by(db.func.coalesce(db.func.sum(Result.score), 0).desc())
                             .limit(5)
                             .all())

    # 8. Real Notifications from User Activity & System
    real_notifications = []
    # Add competition registration notifications
    comp_regs = CompetitionRegistration.query.filter_by(user_id=user_id).order_by(CompetitionRegistration.registered_at.desc()).limit(3).all()
    for reg in comp_regs:
        real_notifications.append({
            'title': f'Registration Confirmed: {reg.competition.title}',
            'time': reg.registered_at.strftime('%b %d, %H:%M') if reg.registered_at else 'Recently',
            'type': 'competition'
        })
    # Add certificate generated notifications
    for cert in user_certificates[:2]:
        sub_name = (cert.result.attempt.subcategory.name if cert.result and cert.result.attempt and cert.result.attempt.subcategory else "Quiz")
        real_notifications.append({
            'title': f'Certificate Generated: {sub_name}',
            'time': cert.created_at.strftime('%b %d, %H:%M') if cert.created_at else 'Recently',
            'type': 'certificate'
        })
    # Add latest result notification
    if results:
        latest = results[-1]
        sub_obj = Subcategory.query.get(latest.subcategory_id) if latest.subcategory_id else None
        real_notifications.append({
            'title': f'Quiz Result: Scored {latest.percentage}% on {sub_obj.name if sub_obj else "Quiz"}',
            'time': latest.created_at.strftime('%b %d, %H:%M') if latest.created_at else 'Recently',
            'type': 'result'
        })

    stats_summary = {
        'total_quizzes': total_quizzes,
        'avg_score': avg_score,
        'global_rank': global_rank,
        'competitions_joined': competitions_joined,
        'certificates_earned': certificates_count,
        'current_streak_days': streak_days,
        'total_points': total_points,
        'current_level': current_level,
        'xp_points': total_points,
    }

    return render_template(
        'dashboard/index.html',
        now=now,
        stats=stats_summary,
        chart_labels=chart_labels,
        chart_scores=chart_scores,
        cat_performance=cat_performance,
        recent_activity=recent_activity,
        recommended_subs=recommended_subs,
        upcoming_competitions=upcoming_competitions,
        top_leaderboard_users=top_leaderboard_users,
        user_certificates=user_certificates,
        real_notifications=real_notifications,
    )




@dashboard_bp.route('/achievements')
@login_required
def achievements():
    """Achievements page: earned and locked badges."""
    earned = (AchievementEarned.query
              .filter_by(user_id=current_user.id)
              .join(Achievement)
              .order_by(AchievementEarned.earned_at.desc())
              .all())
    earned_ids = {e.achievement_id for e in earned}
    locked = Achievement.query.filter(
        Achievement.is_active == True,
        Achievement.id.notin_(earned_ids)
    ).all()
    all_achievements = Achievement.query.filter_by(is_active=True).all()

    # Safe points sum — AchievementEarned has no .points; points lives on Achievement
    total_points = sum(
        getattr(e.achievement, 'points', 0) for e in earned if e.achievement
    )

    return render_template(
        'dashboard/achievements.html',
        earned=earned,
        locked=locked,
        all_achievements=all_achievements,
        total_points=total_points,
    )


@dashboard_bp.route('/certificates')
@login_required
def certificates():
    """User's earned certificates gallery."""
    certs = (Certificate.query
             .filter_by(user_id=current_user.id, is_valid=True)
             .order_by(Certificate.created_at.desc())
             .all())
    return render_template('dashboard/certificates.html', certificates=certs)


@dashboard_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    """Account settings: display name, bio, password change."""
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            full_name = request.form.get('full_name', '').strip()
            bio = request.form.get('bio', '').strip()
            current_user.full_name = full_name[:100] if full_name else None
            current_user.bio = bio[:500] if bio else None
            db.session.commit()
            flash('Profile updated successfully.', 'success')

        elif action == 'change_password':
            current_password = request.form.get('current_password', '')
            new_password = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            from utils.validators import validate_password, validate_password_match
            if not current_user.check_password(current_password):
                flash('Current password is incorrect.', 'error')
            elif err := validate_password(new_password):
                flash(err, 'error')
            elif err := validate_password_match(new_password, confirm_password):
                flash(err, 'error')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Password changed successfully.', 'success')

        return redirect(url_for('dashboard.settings'))

    return render_template('dashboard/settings.html')
