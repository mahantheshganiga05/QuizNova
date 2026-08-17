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


@public_bp.route('/leaderboard')
@public_bp.route('/leaderboard/')
def leaderboard():
    """Global Leaderboard route alias."""
    from routes.quiz import leaderboard as quiz_leaderboard
    return quiz_leaderboard()


@public_bp.route('/api/newsletter/subscribe', methods=['POST'])
def newsletter_subscribe():
    """Handle real newsletter subscription via AJAX and send confirmation email."""
    from models.subscriber import NewsletterSubscriber
    from models.user import User
    from utils.validators import validate_email
    from flask import jsonify, request, current_app

    data = request.get_json(silent=True) or request.form or request.args
    email = (data.get('email') or '').strip().lower()

    err = validate_email(email)
    if err:
        return jsonify({'status': 'error', 'message': err}), 400

    from models import db

    existing = NewsletterSubscriber.query.filter_by(email=email).first()
    if existing and existing.is_active:
        return jsonify({'status': 'info', 'message': "You're already subscribed!"}), 200

    try:
        user = User.query.filter_by(email=email).first()
        if existing:
            existing.is_active = True
            existing.unsubscribed_at = None
            subscriber = existing
        else:
            subscriber = NewsletterSubscriber(email=email, user_id=user.id if user else None)
            db.session.add(subscriber)
        
        db.session.commit()

        # Send confirmation email
        try:
            from services.email_service import send_html_email
            send_html_email(
                to_email=email,
                subject="You're now subscribed to QuizNova updates 📢",
                template_name="stay_updated_confirmation.html",
                context={},
                notification_type="stay_updated",
                related_object_id=str(subscriber.id),
                show_unsubscribe=True,
                unsubscribe_token=subscriber.unsubscribe_token
            )
        except Exception as mail_err:
            current_app.logger.warning(f"Newsletter confirmation email notice: {mail_err}")

        return jsonify({'status': 'success', 'message': "You're subscribed! We'll keep you updated."}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({'status': 'error', 'message': 'An error occurred. Please try again.'}), 500


@public_bp.route('/email/unsubscribe/<string:token>', methods=['GET', 'POST'])
@public_bp.route('/email/unsubscribe', methods=['GET', 'POST'])
def email_unsubscribe(token=None):
    """Handle 1-click unsubscribe requests for marketing/informational emails."""
    from models.subscriber import NewsletterSubscriber
    from models.user import User
    from models import db
    from flask import render_template, request, flash

    unsub_email = "User"
    subscriber = None

    if token:
        subscriber = NewsletterSubscriber.query.filter_by(unsubscribe_token=token).first()
    
    req_email = request.args.get('email') or request.form.get('email')
    if not subscriber and req_email:
        clean_email = req_email.strip().lower()
        subscriber = NewsletterSubscriber.query.filter_by(email=clean_email).first()

    if subscriber:
        unsub_email = subscriber.email
        subscriber.is_active = False
        from datetime import datetime
        subscriber.unsubscribed_at = datetime.utcnow()

        # Also update user marketing preference if user exists
        user = User.query.filter_by(email=subscriber.email).first()
        if user:
            user.notify_marketing = False
            user.notify_competitions = False
            user.notify_announcements = False

        db.session.commit()

    return render_template('email_unsubscribe.html', email=unsub_email)


@public_bp.route('/faq')
def faq():
    return render_template('faq.html')


@public_bp.route('/forgot-password', methods=['GET', 'POST'])
def forgot_password_alias():
    from routes.auth import forgot_password
    return forgot_password()


@public_bp.route('/reset-password/<string:token>', methods=['GET', 'POST'])
def reset_password_alias(token):
    from routes.auth import reset_password
    return reset_password(token)


@public_bp.route('/pricing')
def pricing():
    return render_template('pricing.html')


@public_bp.route('/verify/<string:verification_id>')
@public_bp.route('/certificate/verify/<string:verification_id>')
def verify_certificate(verification_id):
    from models.certificate import Certificate
    cert = Certificate.query.filter_by(verification_id=verification_id).first()
    return render_template('certificate/verify.html', cert=cert)


@public_bp.route('/certificate/<string:verification_id>')
def view_certificate(verification_id):
    from models.certificate import Certificate
    cert = Certificate.query.filter_by(verification_id=verification_id).first_or_404()
    return render_template('certificate/view.html', cert=cert)


@public_bp.route('/certificate/<string:verification_id>/download/pdf')
def download_certificate_pdf(verification_id):
    from flask import send_file, abort
    from models.certificate import Certificate
    from services.certificate_service import generate_certificate_pdf_bytes
    from models import db

    cert = Certificate.query.filter_by(verification_id=verification_id).first_or_404()
    if not cert.is_valid:
        abort(400, 'Certificate has been revoked.')

    pdf_buffer = generate_certificate_pdf_bytes(cert)

    cert.record_download()
    db.session.commit()

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=f'QuizNova_Certificate_{cert.verification_id}.pdf'
    )


@public_bp.route('/certificate/<string:verification_id>/email', methods=['GET', 'POST'])
def email_certificate_route(verification_id):
    from flask import flash, redirect, url_for
    from models.certificate import Certificate
    from services.certificate_service import send_certificate_email
    cert = Certificate.query.filter_by(verification_id=verification_id).first_or_404()
    success = send_certificate_email(cert, cert.user)
    if success:
        flash(f'🎉 Certificate email notification sent to {cert.user.email}!', 'success')
    else:
        flash('Failed to send certificate email.', 'error')
    return redirect(url_for('public.view_certificate', verification_id=verification_id))


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

