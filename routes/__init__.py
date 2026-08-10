"""
QuizNova — Public Routes Blueprint
====================================
Handles all public-facing pages that don't require authentication.
"""

from flask import Blueprint, render_template
from models.category import Category
from models.user import User
from models.quiz import QuizAttempt
from models.result import Result

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def home():
    """Landing page with stats, categories, features."""
    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).limit(6).all()
    stats = {
        'users': User.query.filter_by(is_active=True).count(),
        'quizzes': QuizAttempt.query.filter_by(status='submitted').count(),
        'questions': 1200,   # Or query from DB
        'success_rate': 95,
    }
    return render_template('home.html', categories=categories, stats=stats)


@public_bp.route('/about')
def about():
    return render_template('about.html')


@public_bp.route('/contact')
def contact():
    return render_template('contact.html')


@public_bp.route('/faq')
def faq():
    return render_template('faq.html')


@public_bp.route('/pricing')
def pricing():
    return render_template('pricing.html')


@public_bp.route('/verify/<string:verification_id>')
def verify_certificate(verification_id):
    """Public certificate verification page — no auth required."""
    from models.certificate import Certificate
    cert = Certificate.query.filter_by(verification_id=verification_id).first()
    return render_template('certificate/verify.html', cert=cert)
