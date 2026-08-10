"""
QuizNova — Achievement Service
================================
Checks and awards achievements after a quiz result is saved.
"""

from models import db
from models.result import Result
from models.log import Achievement, AchievementEarned, ActivityLog
from models.quiz import QuizAttempt


def check_and_award_achievements(user_id: int, result: Result) -> None:
    """
    Check all achievement triggers after a quiz completion and award any newly earned ones.

    Args:
        user_id: The user who just completed a quiz.
        result: The newly created Result object.
    """
    already_earned = {ae.achievement_id for ae in AchievementEarned.query.filter_by(user_id=user_id).all()}
    all_achievements = Achievement.query.filter_by(is_active=True).all()

    for ach in all_achievements:
        if ach.id in already_earned:
            continue  # Already earned

        if _should_award(ach, user_id, result):
            _award(user_id, ach, result)

    db.session.commit()


def _should_award(ach: Achievement, user_id: int, result: Result) -> bool:
    """
    Evaluate whether a specific achievement's trigger condition is met.

    Args:
        ach: The Achievement to evaluate.
        user_id: Target user.
        result: Latest result context.

    Returns:
        True if the achievement should be awarded now.
    """
    trigger = ach.trigger_type
    value = ach.trigger_value

    from models.result import Result as ResultModel
    from models.certificate import Certificate

    if trigger == 'quiz_count':
        count = ResultModel.query.filter_by(user_id=user_id).count()
        return count >= (value or 1)

    elif trigger == 'score_100':
        return float(result.percentage) >= 100.0

    elif trigger == 'time_remaining_50pct':
        attempt = result.attempt
        if attempt and attempt.time_taken_seconds:
            total = attempt.subcategory.time_limit_seconds
            return attempt.time_taken_seconds <= (total * 0.5)
        return False

    elif trigger == 'streak_days':
        from services.analytics import _calculate_streak
        return _calculate_streak(user_id) >= (value or 7)

    elif trigger == 'cert_count':
        count = Certificate.query.filter_by(user_id=user_id, is_valid=True).count()
        return count >= (value or 1)

    elif trigger == 'category_count':
        from models import db
        from models.subcategory import Subcategory
        from models.category import Category
        cat_count = (db.session.query(db.func.count(db.func.distinct(Subcategory.category_id)))
                     .join(ResultModel, ResultModel.subcategory_id == Subcategory.id)
                     .filter(ResultModel.user_id == user_id)
                     .scalar() or 0)
        return cat_count >= (value or 5)

    elif trigger == 'rank_top':
        return result.rank_at_time is not None and result.rank_at_time <= (value or 10)

    return False


def _award(user_id: int, ach: Achievement, result: Result) -> None:
    """
    Create an AchievementEarned record and log the activity.

    Args:
        user_id: Target user.
        ach: Achievement being awarded.
        result: Context result.
    """
    import json
    earned = AchievementEarned(
        user_id=user_id,
        achievement_id=ach.id,
        context=json.dumps({'result_id': result.id, 'attempt_id': result.attempt_id})
    )
    db.session.add(earned)

    log = ActivityLog(
        user_id=user_id,
        event_type='achievement_earned',
        entity_type='achievement',
        entity_id=ach.id,
        description=f'Earned achievement: {ach.name}'
    )
    db.session.add(log)
