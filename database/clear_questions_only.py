"""
QuizNova — Safe Question Bank Purge Script
===========================================
Safely clears ONLY question-related data and quiz attempt histories.
Preserves Users, Admin accounts, 12 Categories, 48 Subcategories,
Settings, Achievements, and database schema.
"""

import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db
from models.user import User
from models.category import Category
from models.subcategory import Subcategory
from models.question import Question
from models.quiz import QuizAttempt, AttemptQuestion, AttemptAnswer
from models.result import Result
from models.log import ActivityLog, AntiCheatLog
from models.leaderboard import LeaderboardCache


def purge_questions_only():
    app = create_app('development')
    with app.app_context():
        print("==================================================")
        print("PURGING QUESTION BANK AND ATTEMPT HISTORIES ONLY")
        print("==================================================")

        # 1. Clear child dependent records in order of FK constraints
        print(" [1/7] Clearing Attempt Answers...")
        ans_count = AttemptAnswer.query.delete()

        print(" [2/7] Clearing Attempt Questions...")
        aq_count = AttemptQuestion.query.delete()

        print(" [3/7] Clearing Anti-Cheat Logs...")
        ac_count = AntiCheatLog.query.delete()

        print(" [4/7] Clearing Quiz Attempts...")
        attempt_count = QuizAttempt.query.delete()

        print(" [5/7] Clearing Results...")
        res_count = Result.query.delete()

        print(" [6/7] Clearing Leaderboard Cache...")
        lb_count = LeaderboardCache.query.delete()

        print(" [7/7] Clearing Question Bank...")
        q_count = Question.query.delete()

        db.session.commit()

        print("\n==================================================")
        print("VERIFYING POST-PURGE DATABASE STATE")
        print("==================================================")
        print(f"  Questions:     {Question.query.count()} (Target: 0)")
        print(f"  Attempts:      {QuizAttempt.query.count()} (Target: 0)")
        print(f"  Results:       {Result.query.count()} (Target: 0)")
        print(f"  Categories:    {Category.query.count()} (Target: 12)")
        print(f"  Subcategories: {Subcategory.query.count()} (Target: 48)")
        print(f"  Users:          {User.query.count()} (Preserved)")
        print("==================================================")

        if Question.query.count() == 0 and Category.query.count() == 12 and Subcategory.query.count() == 48:
            print("SUCCESS: Question bank cleared to 0. All 12 categories, 48 subcategories, and users preserved!")
        else:
            print("WARNING: Unexpected entity count post-purge.")


if __name__ == '__main__':
    purge_questions_only()
