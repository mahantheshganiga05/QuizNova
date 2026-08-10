"""
QuizNova — Database Seeder
============================
Populates the database with:
  - Admin and demo student users
  - 12 categories, 4 subcategories each (48 total)
  - 25 questions per subcategory (1200 total)
  - 10 achievements
  - Platform settings

Run: python database/seed.py

WARNING: This script wipes all existing seed data before re-seeding.
         Use only in development/staging environments.
"""

import sys
import os
import random

# Ensure the project root is in Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db
from models.user import User
from models.category import Category
from models.subcategory import Subcategory
from models.question import Question
from models.log import Achievement, Settings


# =============================================================================
# CATEGORY & SUBCATEGORY DATA
# =============================================================================

CATEGORIES = [
    {
        "name": "Programming",
        "slug": "programming",
        "description": "Core programming concepts across popular languages.",
        "color_hex": "#7C3AED",
        "icon": "programming.svg",
        "subcategories": [
            {"name": "Python",          "slug": "python",       "pass_threshold": 60},
            {"name": "Java",            "slug": "java",         "pass_threshold": 60},
            {"name": "JavaScript",      "slug": "javascript",   "pass_threshold": 60},
            {"name": "C++",             "slug": "cpp",          "pass_threshold": 60},
        ]
    },
    {
        "name": "Data Structures & Algorithms",
        "slug": "dsa",
        "description": "Mastery of DSA concepts essential for technical interviews.",
        "color_hex": "#2563EB",
        "icon": "dsa.svg",
        "subcategories": [
            {"name": "Arrays & Strings",    "slug": "arrays-strings",  "pass_threshold": 60},
            {"name": "Trees & Graphs",      "slug": "trees-graphs",    "pass_threshold": 60},
            {"name": "Dynamic Programming", "slug": "dynamic-programming", "pass_threshold": 65},
            {"name": "Sorting & Searching", "slug": "sorting-searching",   "pass_threshold": 60},
        ]
    },
    {
        "name": "Databases",
        "slug": "databases",
        "description": "SQL, NoSQL, database design, and query optimization.",
        "color_hex": "#059669",
        "icon": "databases.svg",
        "subcategories": [
            {"name": "SQL Fundamentals",  "slug": "sql-fundamentals",   "pass_threshold": 60},
            {"name": "Advanced SQL",      "slug": "advanced-sql",        "pass_threshold": 65},
            {"name": "MySQL",             "slug": "mysql",               "pass_threshold": 60},
            {"name": "NoSQL & MongoDB",   "slug": "nosql-mongodb",       "pass_threshold": 60},
        ]
    },
    {
        "name": "Computer Science",
        "slug": "computer-science",
        "description": "Operating systems, networking, and computer architecture fundamentals.",
        "color_hex": "#DC2626",
        "icon": "cs.svg",
        "subcategories": [
            {"name": "Operating Systems", "slug": "operating-systems", "pass_threshold": 60},
            {"name": "Computer Networks", "slug": "computer-networks",  "pass_threshold": 60},
            {"name": "Computer Architecture", "slug": "computer-architecture", "pass_threshold": 60},
            {"name": "Theory of Computation", "slug": "theory-computation",    "pass_threshold": 65},
        ]
    },
    {
        "name": "Artificial Intelligence",
        "slug": "artificial-intelligence",
        "description": "Machine learning, deep learning, and AI fundamentals.",
        "color_hex": "#7C3AED",
        "icon": "ai.svg",
        "subcategories": [
            {"name": "Machine Learning Basics", "slug": "ml-basics",       "pass_threshold": 60},
            {"name": "Deep Learning",           "slug": "deep-learning",   "pass_threshold": 65},
            {"name": "NLP Fundamentals",        "slug": "nlp",             "pass_threshold": 60},
            {"name": "AI Ethics",               "slug": "ai-ethics",       "pass_threshold": 60},
        ]
    },
    {
        "name": "Web Development",
        "slug": "web-development",
        "description": "Frontend, backend, and full-stack web development concepts.",
        "color_hex": "#D97706",
        "icon": "web.svg",
        "subcategories": [
            {"name": "HTML & CSS",        "slug": "html-css",      "pass_threshold": 60},
            {"name": "JavaScript DOM",    "slug": "js-dom",         "pass_threshold": 60},
            {"name": "REST APIs",         "slug": "rest-apis",      "pass_threshold": 60},
            {"name": "Flask & Django",    "slug": "flask-django",   "pass_threshold": 60},
        ]
    },
    {
        "name": "Mathematics",
        "slug": "mathematics",
        "description": "Discrete math, probability, and statistics for engineers.",
        "color_hex": "#0891B2",
        "icon": "math.svg",
        "subcategories": [
            {"name": "Discrete Mathematics", "slug": "discrete-math",  "pass_threshold": 60},
            {"name": "Probability",          "slug": "probability",     "pass_threshold": 60},
            {"name": "Statistics",           "slug": "statistics",      "pass_threshold": 60},
            {"name": "Linear Algebra",       "slug": "linear-algebra",  "pass_threshold": 60},
        ]
    },
    {
        "name": "Aptitude",
        "slug": "aptitude",
        "description": "Quantitative aptitude for placement and competitive exams.",
        "color_hex": "#BE185D",
        "icon": "aptitude.svg",
        "subcategories": [
            {"name": "Quantitative",        "slug": "quantitative",     "pass_threshold": 60},
            {"name": "Logical Reasoning",   "slug": "logical-reasoning","pass_threshold": 60},
            {"name": "Verbal Ability",      "slug": "verbal-ability",   "pass_threshold": 60},
            {"name": "Data Interpretation", "slug": "data-interpretation","pass_threshold": 60},
        ]
    },
    {
        "name": "Competitive Exams",
        "slug": "competitive-exams",
        "description": "GATE, GRE, CAT, and other competitive exam preparation.",
        "color_hex": "#9333EA",
        "icon": "competitive.svg",
        "subcategories": [
            {"name": "GATE CS",       "slug": "gate-cs",    "pass_threshold": 65},
            {"name": "GRE Quant",     "slug": "gre-quant",  "pass_threshold": 60},
            {"name": "CAT Quant",     "slug": "cat-quant",  "pass_threshold": 60},
            {"name": "Campus Placement", "slug": "campus-placement", "pass_threshold": 60},
        ]
    },
    {
        "name": "Cloud Computing",
        "slug": "cloud-computing",
        "description": "AWS, Azure, GCP fundamentals and cloud architecture.",
        "color_hex": "#0369A1",
        "icon": "cloud.svg",
        "subcategories": [
            {"name": "AWS Fundamentals",     "slug": "aws",      "pass_threshold": 60},
            {"name": "Cloud Architecture",   "slug": "cloud-arch","pass_threshold": 65},
            {"name": "DevOps & CI/CD",       "slug": "devops",   "pass_threshold": 60},
            {"name": "Docker & Kubernetes",  "slug": "docker-k8s","pass_threshold": 65},
        ]
    },
    {
        "name": "Cybersecurity",
        "slug": "cybersecurity",
        "description": "Network security, ethical hacking, and data protection.",
        "color_hex": "#DC2626",
        "icon": "security.svg",
        "subcategories": [
            {"name": "Network Security",    "slug": "network-security", "pass_threshold": 60},
            {"name": "Web Security (OWASP)","slug": "web-security",     "pass_threshold": 65},
            {"name": "Cryptography",        "slug": "cryptography",     "pass_threshold": 60},
            {"name": "Ethical Hacking",     "slug": "ethical-hacking",  "pass_threshold": 65},
        ]
    },
    {
        "name": "Soft Skills",
        "slug": "soft-skills",
        "description": "Communication, leadership, and professional development.",
        "color_hex": "#059669",
        "icon": "softskills.svg",
        "subcategories": [
            {"name": "English Grammar",    "slug": "english-grammar",  "pass_threshold": 60},
            {"name": "Communication",      "slug": "communication",    "pass_threshold": 60},
            {"name": "Leadership",         "slug": "leadership",       "pass_threshold": 60},
            {"name": "Critical Thinking",  "slug": "critical-thinking","pass_threshold": 60},
        ]
    },
]


# =============================================================================
# ACHIEVEMENTS SEED DATA
# =============================================================================

ACHIEVEMENTS = [
    {"code": "FIRST_QUIZ",      "name": "First Step",         "description": "Complete your first quiz.",
     "icon": "first-step.svg",  "points": 10, "trigger_type": "quiz_count",     "trigger_value": 1},
    {"code": "QUIZ_10",         "name": "Quiz Enthusiast",    "description": "Complete 10 quizzes.",
     "icon": "enthusiast.svg",  "points": 25, "trigger_type": "quiz_count",     "trigger_value": 10},
    {"code": "QUIZ_50",         "name": "Quiz Master",        "description": "Complete 50 quizzes.",
     "icon": "master.svg",      "points": 100,"trigger_type": "quiz_count",     "trigger_value": 50},
    {"code": "PERFECT_SCORE",   "name": "Perfect Score",      "description": "Score 100% on any quiz.",
     "icon": "perfect.svg",     "points": 50, "trigger_type": "score_100",      "trigger_value": None},
    {"code": "SPEED_DEMON",     "name": "Speed Demon",        "description": "Complete a quiz in under 50% of the time limit.",
     "icon": "speed.svg",       "points": 30, "trigger_type": "time_remaining_50pct", "trigger_value": None},
    {"code": "STREAK_7",        "name": "7-Day Streak",       "description": "Practice for 7 consecutive days.",
     "icon": "streak.svg",      "points": 35, "trigger_type": "streak_days",   "trigger_value": 7},
    {"code": "FIRST_CERT",      "name": "Certificate Earner", "description": "Earn your first certificate.",
     "icon": "cert.svg",        "points": 20, "trigger_type": "cert_count",    "trigger_value": 1},
    {"code": "CERT_5",          "name": "Certified Pro",      "description": "Earn 5 certificates.",
     "icon": "pro-cert.svg",    "points": 75, "trigger_type": "cert_count",    "trigger_value": 5},
    {"code": "MULTI_DOMAIN",    "name": "Multi-Domain Expert","description": "Attempt quizzes in 5+ different categories.",
     "icon": "domain.svg",      "points": 40, "trigger_type": "category_count","trigger_value": 5},
    {"code": "TOP_10",          "name": "Top Ranker",         "description": "Enter the top 10 of any leaderboard.",
     "icon": "top10.svg",       "points": 60, "trigger_type": "rank_top",      "trigger_value": 10},
]


# =============================================================================
# QUESTION GENERATOR
# =============================================================================

def generate_questions(subcategory_id: int, sub_name: str, count: int = 25):
    """
    Generate `count` clean technical MCQ questions for a subcategory.
    """
    topics = [
        ("Core Concepts", "Standard syntax and declaration rules"),
        ("Architecture", "Internal execution lifecycle and memory model"),
        ("Optimization", "Algorithmic time complexity and caching"),
        ("Validation", "Data sanitization and exception handling bounds"),
        ("Best Practices", "Decoupled component architecture and modular design"),
    ]
    difficulties = ['easy', 'easy', 'medium', 'medium', 'medium', 'hard']
    questions = []

    for i in range(1, count + 1):
        diff = difficulties[i % len(difficulties)]
        t_name, t_desc = topics[i % len(topics)]
        
        q = Question(
            subcategory_id=subcategory_id,
            question_text=f'In {sub_name} ({t_name}), which statement correctly describes key requirement #{i}?',
            option_a=f'Adhering to standard {sub_name} principles ensures {t_desc.lower()}.',
            option_b=f'Directly mutating unallocated memory references.',
            option_c=f'Disabling runtime bounds checking to bypass compiler optimizations.',
            option_d=f'Ignoring asynchronous callback resolution errors.',
            correct_option='a',
            explanation=f'Following standard {sub_name} rules ensures that {t_desc.lower()} functions reliably.',
            difficulty=diff,
            tags=f"{sub_name.lower().replace(' ', '-')},{diff}",
            is_active=True,
        )
        questions.append(q)

    return questions


# =============================================================================
# SETTINGS SEED DATA
# =============================================================================

DEFAULT_SETTINGS = [
    ("site_name",            "QuizNova",                   "Platform display name"),
    ("maintenance_mode",     "0",                          "Set to 1 to enable maintenance mode"),
    ("max_login_attempts",   "5",                          "Max failed login attempts before lockout"),
    ("quiz_max_violations",  "3",                          "Max anti-cheat violations before auto-submit"),
    ("cert_pass_threshold",  "60",                         "Default pass percentage for certificates"),
    ("questions_per_quiz",   "20",                         "Default questions per quiz"),
    ("time_limit_minutes",   "30",                         "Default time limit per quiz in minutes"),
    ("leaderboard_public",   "1",                          "Allow unauthenticated users to view leaderboard"),
    ("registration_enabled", "1",                          "Allow new user registrations"),
    ("ai_features_enabled",  "0",                          "Enable AI features (v2)"),
]


# =============================================================================
# MAIN SEEDER
# =============================================================================

def seed():
    app = create_app('development')

    with app.app_context():
        db.create_all()
        print("=" * 60)
        print("QuizNova Database Seeder")
        print("=" * 60)

        # ---------------------------------------------------------------
        # ADMIN USER
        # ---------------------------------------------------------------
        print("\n[1/6] Seeding admin user...")
        if not User.query.filter_by(email='admin@quiznova.com').first():
            admin = User(
                username='admin',
                email='admin@quiznova.com',
                full_name='QuizNova Admin',
                role='admin',
                is_active=True,
                email_verified=True,
            )
            admin.set_password('Admin@QuizNova1')
            db.session.add(admin)
            db.session.commit()
            print("   [OK] Admin created: admin@quiznova.com / Admin@QuizNova1")
        else:
            print("   [OK] Admin already exists — skipped.")

        # ---------------------------------------------------------------
        # DEMO STUDENT
        # ---------------------------------------------------------------
        print("\n[2/6] Seeding demo student user...")
        if not User.query.filter_by(email='demo@quiznova.com').first():
            student = User(
                username='demo_student',
                email='demo@quiznova.com',
                full_name='Demo Student',
                role='student',
                is_active=True,
            )
            student.set_password('Demo@Student1')
            db.session.add(student)
            db.session.commit()
            print("   [OK] Demo student created: demo@quiznova.com / Demo@Student1")
        else:
            print("   [OK] Demo student already exists — skipped.")

        # ---------------------------------------------------------------
        # CATEGORIES & SUBCATEGORIES & QUESTIONS
        # ---------------------------------------------------------------
        print("\n[3/6] Seeding categories, subcategories, and questions...")
        total_questions = 0

        for sort_idx, cat_data in enumerate(CATEGORIES):
            cat = Category.query.filter((Category.slug == cat_data['slug']) | (Category.name == cat_data['name'])).first()
            if not cat:
                cat = Category(
                    name=cat_data['name'],
                    slug=cat_data['slug'],
                    description=cat_data['description'],
                    color_hex=cat_data['color_hex'],
                    icon=cat_data['icon'],
                    sort_order=sort_idx,
                    is_active=True,
                )
                db.session.add(cat)
                db.session.flush()

            for sub_idx, sub_data in enumerate(cat_data['subcategories']):
                sub = Subcategory.query.filter(
                    Subcategory.category_id == cat.id,
                    (Subcategory.slug == sub_data['slug']) | (Subcategory.name == sub_data['name'])
                ).first()

                if not sub:
                    sub = Subcategory(
                        category_id=cat.id,
                        name=sub_data['name'],
                        slug=sub_data['slug'],
                        questions_per_quiz=20,
                        time_limit_minutes=30,
                        pass_threshold=sub_data['pass_threshold'],
                        sort_order=sub_idx,
                        is_active=True,
                    )
                    db.session.add(sub)
                    db.session.flush()

                    # Seed questions only for new subcategories
                    q_count = Question.query.filter_by(subcategory_id=sub.id).count()
                    if q_count < 25:
                        questions = generate_questions(sub.id, sub_data['name'], 25)
                        db.session.add_all(questions)
                        total_questions += 25

            db.session.commit()
            print(f"   [OK] {cat_data['name']} ({len(cat_data['subcategories'])} subcategories)")

        print(f"   [OK] Total questions seeded: {total_questions}")

        # ---------------------------------------------------------------
        # ACHIEVEMENTS
        # ---------------------------------------------------------------
        print("\n[4/6] Seeding achievements...")
        for ach_data in ACHIEVEMENTS:
            if not Achievement.query.filter_by(code=ach_data['code']).first():
                ach = Achievement(**ach_data)
                db.session.add(ach)
        db.session.commit()
        print(f"   [OK] {len(ACHIEVEMENTS)} achievements seeded.")

        # ---------------------------------------------------------------
        # SETTINGS
        # ---------------------------------------------------------------
        print("\n[5/6] Seeding platform settings...")
        from models.log import Settings
        for key, value, desc in DEFAULT_SETTINGS:
            Settings.set(key, value, desc)
        db.session.commit()
        print(f"   [OK] {len(DEFAULT_SETTINGS)} settings seeded.")

        # ---------------------------------------------------------------
        # SUMMARY
        # ---------------------------------------------------------------
        print("\n[6/6] Seed complete!")
        print("-" * 60)
        print(f"  Categories:     {Category.query.count()}")
        print(f"  Subcategories:  {Subcategory.query.count()}")
        print(f"  Questions:      {Question.query.count()}")
        print(f"  Users:          {User.query.count()}")
        print(f"  Achievements:   {Achievement.query.count()}")
        print("-" * 60)
        print("\n✅ QuizNova is ready! Run: flask run")
        print("   Admin: http://localhost:5000/admin")
        print("   App:   http://localhost:5000")
        print("=" * 60)


if __name__ == '__main__':
    seed()
