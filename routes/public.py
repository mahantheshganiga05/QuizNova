"""QuizNova — Routes package."""
from flask import Blueprint

# public_bp is defined inside this module and imported by app.py
from flask import Blueprint, render_template, request
from models.category import Category
from models.user import User
from models.quiz import QuizAttempt

public_bp = Blueprint('public', __name__)


@public_bp.route('/')
def home():
    from models.competition import Competition
    from datetime import datetime

    categories = Category.query.filter_by(is_active=True).order_by(Category.sort_order).all()

    # Dynamic Published Competitions for Announcement Marquee
    announcement_competitions = Competition.query.filter(Competition.status.in_(['published', 'live'])).order_by(Competition.start_date.asc()).all()

    # Fallback if DB has no published competitions yet
    if not announcement_competitions:
        now = datetime.utcnow()
        announcement_competitions = [
            Competition(
                title='National Python Championship 2025',
                slug='national-python-championship-2025',
                prize_pool_text='₹50,000 Prize Pool',
                eligibility_text='All College Students & Developers',
                reg_end_date=now.replace(year=now.year + 1),
                start_date=now,
                status='published'
            ),
            Competition(
                title='Full Stack Web Development Challenge',
                slug='full-stack-web-challenge',
                prize_pool_text='₹25,000 Prize Pool',
                eligibility_text='B.Tech & BCA Students',
                reg_end_date=now.replace(year=now.year + 1),
                start_date=now,
                status='published'
            ),
            Competition(
                title='DSA & Algorithm Hackathon 2025',
                slug='dsa-algorithm-hackathon-2025',
                prize_pool_text='₹1,00,000 Prize Pool',
                eligibility_text='Open to All Coders',
                reg_end_date=now.replace(year=now.year + 1),
                start_date=now,
                status='published'
            )
        ]

    featured_categories = categories[:5]
    featured_competitions = announcement_competitions[:3]

    stats = {
        'users':        User.query.filter_by(is_active=True).count(),
        'quizzes':      QuizAttempt.query.filter_by(status='submitted').count(),
        'questions':    2400,
        'success_rate': 95,
    }
    return render_template(
        'home.html',
        categories=categories,
        featured_categories=featured_categories,
        featured_competitions=featured_competitions,
        announcement_competitions=announcement_competitions,
        stats=stats
    )



@public_bp.route('/about')
def about():
    return render_template('about.html')


@public_bp.route('/contact')
def contact():
    return render_template('contact.html')


@public_bp.route('/ai-recommendations')
@public_bp.route('/ai-recommendations/')
def ai_recommendations():
    """Dedicated AI Recommendations & Personalized Learning Page."""
    return render_template('ai_recommendations.html')


@public_bp.route('/api/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    """Handle real newsletter subscription via AJAX."""
    from app import csrf
    # Exempt endpoint dynamically if needed, or handle input
    from models.subscriber import NewsletterSubscriber
    from utils.validators import validate_email
    from flask import jsonify, request

    data = request.get_json(silent=True) or request.form or request.args
    email = (data.get('email') or '').strip().lower()

    err = validate_email(email)
    if err:
        return jsonify({'status': 'error', 'message': err}), 400

    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if existing:
        return jsonify({'status': 'info', 'message': "You're already subscribed!"}), 200

    try:
        subscriber = NewsletterSubscriber(email=email)
        from models import db
        db.session.add(subscriber)
        db.session.commit()
        return jsonify({'status': 'success', 'message': "You're subscribed! We'll keep you updated."}), 200
    except Exception as e:
        from models import db
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'An error occurred. Please try again.'}), 500


@public_bp.route('/faq')
def faq():
    return render_template('faq.html')


@public_bp.route('/pricing')
def pricing():
    return render_template('pricing.html')


@public_bp.route('/verify/<string:verification_id>')
def verify_certificate(verification_id):
    from models.certificate import Certificate
    cert = Certificate.query.filter_by(verification_id=verification_id).first()
    return render_template('certificate/verify.html', cert=cert)


# -------------------------------------------------------------------------
# Global Category Navigation Aliases & Fallback Handlers
# -------------------------------------------------------------------------
@public_bp.route('/categories', methods=['GET'])
@public_bp.route('/categories/', methods=['GET'])
@public_bp.route('/category', methods=['GET'])
@public_bp.route('/category/', methods=['GET'])
def categories_alias():
    from flask import redirect, url_for
    return redirect(url_for('quiz.categories'))


@public_bp.route('/categories/<string:category_slug>', methods=['GET'])
@public_bp.route('/categories/<string:category_slug>/', methods=['GET'])
@public_bp.route('/category/<string:category_slug>', methods=['GET'])
@public_bp.route('/category/<string:category_slug>/', methods=['GET'])
def subcategories_alias(category_slug):
    from flask import redirect, url_for
    return redirect(url_for('quiz.subcategories', category_slug=category_slug))

