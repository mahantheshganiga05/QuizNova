"""
QuizNova — Leaderboard Service
================================
Handles rank computation and cache refresh after quiz submission.
"""

from models import db
from models.result import Result
from models.leaderboard import LeaderboardCache


def refresh_leaderboard_for_user(user_id: int, subcategory_id: int) -> None:
    """
    Update leaderboard_cache for both subcategory-specific and global entries
    after a quiz submission.

    Args:
        user_id: The user who just submitted.
        subcategory_id: The subcategory quiz that was just completed.
    """
    _update_entry(user_id, subcategory_id)
    _update_entry(user_id, None)  # Global leaderboard
    _recalculate_ranks(subcategory_id)
    _recalculate_ranks(None)


def _update_entry(user_id: int, subcategory_id) -> None:
    """
    Recompute and upsert a single leaderboard_cache row.

    Args:
        user_id: Target user.
        subcategory_id: Target subcategory (None = global).
    """
    query = Result.query.filter_by(user_id=user_id)
    if subcategory_id is not None:
        query = query.filter_by(subcategory_id=subcategory_id)

    results = query.all()

    if not results:
        return

    total_score = sum(r.correct_count for r in results)
    quiz_count = len(results)
    best_percentage = max(float(r.percentage) for r in results)

    entry = LeaderboardCache.query.filter_by(
        user_id=user_id, subcategory_id=subcategory_id
    ).first()

    if entry:
        entry.total_score = total_score
        entry.quiz_count = quiz_count
        entry.best_percentage = best_percentage
    else:
        entry = LeaderboardCache(
            user_id=user_id,
            subcategory_id=subcategory_id,
            total_score=total_score,
            quiz_count=quiz_count,
            best_percentage=best_percentage,
        )
        db.session.add(entry)

    db.session.commit()


def _recalculate_ranks(subcategory_id) -> None:
    """
    Recalculate rank_position for all entries in a leaderboard scope.
    Uses SQL window function approach via Python ordering.

    Args:
        subcategory_id: None for global, or specific subcategory ID.
    """
    entries = (LeaderboardCache.query
               .filter_by(subcategory_id=subcategory_id)
               .order_by(LeaderboardCache.total_score.desc())
               .all())

    for rank, entry in enumerate(entries, start=1):
        entry.rank_position = rank

    db.session.commit()


def get_global_rank(user_id: int) -> int | None:
    """
    Get a user's current global leaderboard rank.

    Args:
        user_id: Target user ID.

    Returns:
        Integer rank or None if user has no leaderboard entry.
    """
    entry = LeaderboardCache.query.filter_by(
        user_id=user_id, subcategory_id=None
    ).first()
    return entry.rank_position if entry else None
