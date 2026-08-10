"""
QuizNova — Seed Competitions Data
=====================================
Populates sample competitions, registrations, and leaderboard data.
"""

import os
from datetime import datetime, timedelta

os.environ['DATABASE_URL'] = 'sqlite:///quiznova.db'
os.environ['PYTHONPATH'] = '.'

from app import create_app
from models import db
from models.category import Category
from models.subcategory import Subcategory
from models.competition import Competition, CompetitionRegistration

app = create_app('development')

def seed_competitions():
    with app.app_context():
        db.create_all()

        # Check existing competitions
        if Competition.query.count() > 0:
            print("Competitions already seeded.")
            return

        cat = Category.query.first()
        sub = Subcategory.query.first()

        now = datetime.utcnow()

        c1 = Competition(
            title="National Python AI & ML Championship 2026",
            slug="national-python-ai-ml-championship-2026",
            short_description="High-stakes competitive Python, AI, and Machine Learning tournament with live rankings.",
            full_description="Test your depth in algorithmic Python, PyTorch, NumPy, and Machine Learning concepts. Top 3 participants receive trophies, cash prizes, and verifiable certificates.",
            category_id=cat.id if cat else None,
            subcategory_id=sub.id if sub else None,
            total_questions=20,
            duration_minutes=45,
            passing_marks=60,
            max_participants=1000,
            reg_start_date=now - timedelta(days=5),
            reg_end_date=now + timedelta(days=10),
            start_date=now - timedelta(hours=1),
            end_date=now + timedelta(days=5),
            prize_pool_text="$1,500 Prize Pool",
            prize_1st="🥇 Gold Trophy + $750 Cash Prize + Certificate of Excellence",
            prize_2nd="🥈 Silver Medal + $500 Cash Prize + Certificate of Excellence",
            prize_3rd="🥉 Bronze Medal + $250 Cash Prize + Certificate of Excellence",
            sponsor_name="QuizNova AI Labs",
            organizer_name="QuizNova Academic Team",
            is_featured=True,
            is_trending=True,
            status="published"
        )

        c2 = Competition(
            title="Global Cybersecurity & Ethical Hacking Hackathon",
            slug="global-cybersecurity-ethical-hacking-hackathon",
            short_description="Test your security knowledge across cryptography, network security, and vulnerability assessment.",
            full_description="Compete against top cybersecurity enthusiasts globally. Fast-paced quiz questions testing penetration testing concepts and defensive architecture.",
            category_id=cat.id if cat else None,
            subcategory_id=sub.id if sub else None,
            total_questions=25,
            duration_minutes=60,
            passing_marks=70,
            max_participants=500,
            reg_start_date=now - timedelta(days=2),
            reg_end_date=now + timedelta(days=15),
            start_date=now + timedelta(days=2),
            end_date=now + timedelta(days=7),
            prize_pool_text="$2,000 Prize Pool",
            prize_1st="🥇 Gold Trophy + Security Certificate + $1,000 Voucher",
            prize_2nd="🥈 Silver Medal + $600 Voucher",
            prize_3rd="🥉 Bronze Medal + $400 Voucher",
            sponsor_name="CyberShield Alliance",
            organizer_name="QuizNova Security Guild",
            is_featured=True,
            is_trending=False,
            status="published"
        )

        db.session.add_all([c1, c2])
        db.session.commit()
        print("✓ Sample competitions seeded successfully!")

if __name__ == '__main__':
    seed_competitions()
