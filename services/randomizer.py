"""
QuizNova — Quiz Randomizer Service
=====================================
Handles question selection and option shuffling for quiz attempts.
This is the core fairness engine: ensures every attempt gets a unique
question set in a unique option order.
"""

import random
import json
from typing import List, Tuple, Dict, Any

from models.question import Question
from models.quiz import AttemptQuestion


def select_questions(subcategory_id: int, count: int, user_id: int = None) -> List[Question]:
    """
    Randomly select questions from the active manual question pool.
    Uses Python's random.sample — no repeats within the same quiz attempt.
    Optionally prioritizes questions unattempted by the current user.

    Args:
        subcategory_id: ID of the subcategory to pull questions from.
        count: Target number of questions to select.
        user_id: Optional ID of the user starting the quiz attempt.

    Returns:
        List of Question objects in random order.
    """
    from models import db
    from models.quiz import QuizAttempt, AttemptQuestion

    pool = Question.query.filter_by(
        subcategory_id=subcategory_id,
        is_active=True
    ).all()

    if not pool:
        raise ValueError(f"No active questions available in this subcategory.")

    sample_size = min(count, len(pool))

    # Prioritize unattempted questions if user_id is provided
    if user_id and len(pool) > sample_size:
        attempted_q_ids = (db.session.query(AttemptQuestion.question_id)
                           .join(QuizAttempt)
                           .filter(QuizAttempt.user_id == user_id,
                                   QuizAttempt.subcategory_id == subcategory_id)
                           .distinct()
                           .all())
        attempted_set = set(r[0] for r in attempted_q_ids)

        unattempted = [q for q in pool if q.id not in attempted_set]
        if len(unattempted) >= sample_size:
            return random.sample(unattempted, sample_size)
        else:
            attempted = [q for q in pool if q.id in attempted_set]
            needed = sample_size - len(unattempted)
            random.shuffle(unattempted)
            return unattempted + random.sample(attempted, min(needed, len(attempted)))

    return random.sample(pool, sample_size)


def shuffle_options(question: Question) -> Tuple[List[str], int]:
    """
    Shuffle the four options of a question and return the new correct index.

    Algorithm:
      1. Build ordered list [option_a, option_b, option_c, option_d]
      2. Record the correct option's text
      3. Shuffle the list in-place (Fisher-Yates via random.shuffle)
      4. Find the new index of the correct option text

    Args:
        question: A Question model instance.

    Returns:
        Tuple of (shuffled_options_list, new_correct_index_0based)
    """
    options = list(question.options_list)  # Copy: [A, B, C, D]
    correct_text = question.correct_option_text

    random.shuffle(options)

    new_correct_index = options.index(correct_text)

    return options, new_correct_index


def build_attempt_questions(
    attempt_id: int,
    selected_questions: List[Question]
) -> List[AttemptQuestion]:
    """
    Create AttemptQuestion records for all selected questions.
    Each record stores the shuffled options and the new correct index.
    Questions are assigned an order (1-based) in the shuffled sequence.

    Args:
        attempt_id: The ID of the QuizAttempt these questions belong to.
        selected_questions: List of Question objects (already randomized order).

    Returns:
        List of AttemptQuestion objects (not yet committed to DB).
    """
    attempt_questions = []

    for order, question in enumerate(selected_questions, start=1):
        shuffled_options, correct_shuffled_index = shuffle_options(question)

        aq = AttemptQuestion(
            attempt_id=attempt_id,
            question_id=question.id,
            question_order=order,
            correct_shuffled_index=correct_shuffled_index,
        )
        aq.options = shuffled_options  # Uses the JSON setter on AttemptQuestion

        attempt_questions.append(aq)

    return attempt_questions


def serialize_attempt_questions_for_client(
    attempt_questions: List[AttemptQuestion],
    existing_answers: Dict[int, int] = None
) -> List[Dict[str, Any]]:
    """
    Serialize AttemptQuestion records into a JSON-safe format for the frontend.
    IMPORTANT: correct_shuffled_index is deliberately EXCLUDED from the output
    to prevent client-side cheating.

    Args:
        attempt_questions: List of AttemptQuestion objects ordered by question_order.
        existing_answers: Dict mapping attempt_question_id → selected_index
                          (for state recovery on page refresh).

    Returns:
        List of dicts safe to send to the browser.
    """
    if existing_answers is None:
        existing_answers = {}

    result = []
    for aq in attempt_questions:
        result.append({
            'attempt_question_id': aq.id,
            'question_order': aq.question_order,
            'question_text': aq.question.question_text,
            'options': aq.options,  # Shuffled list
            'is_bookmarked': aq.is_bookmarked,
            'selected_index': existing_answers.get(aq.id),  # None if not answered
            # DO NOT include: correct_shuffled_index, question.correct_option
        })

    return result
