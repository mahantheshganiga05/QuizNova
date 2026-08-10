"""
QuizNova — Flask Application Factory
=====================================
Entry point for the QuizNova quiz platform.
Creates and configures the Flask app with all blueprints, extensions, and error handlers.
"""

from flask import Flask, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from models import db
from config import config


# =============================================================================
# Extensions (initialized without app — applied in create_app)
# =============================================================================
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(config_name: str = 'default') -> Flask:
    """
    Flask application factory.

    Args:
        config_name: Configuration profile key ('development', 'production', 'testing').
                     Defaults to 'default' which maps to DevelopmentConfig.

    Returns:
        Configured Flask application instance.
    """
    app = Flask(__name__)

    # -------------------------------------------------------------------------
    # Load Configuration
    # -------------------------------------------------------------------------
    app.config.from_object(config[config_name])

    # -------------------------------------------------------------------------
    # Initialize Extensions
    # -------------------------------------------------------------------------
    db.init_app(app)
    csrf.init_app(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    # -------------------------------------------------------------------------
    # User Loader (Flask-Login)
    # -------------------------------------------------------------------------
    from models.user import User

    @login_manager.user_loader
    def load_user(user_id: str):
        return User.query.get(int(user_id))

    # -------------------------------------------------------------------------
    # Register Blueprints
    # -------------------------------------------------------------------------
    from routes.auth import auth_bp
    from routes.quiz import quiz_bp
    from routes.dashboard import dashboard_bp
    from routes.admin import admin_bp
    from routes.api import api_bp
    from routes.competitions import competitions_bp

    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(quiz_bp, url_prefix='/quiz')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(competitions_bp, url_prefix='/competitions')

    # -------------------------------------------------------------------------
    # Public / Landing Routes (registered directly on app)
    # -------------------------------------------------------------------------
    from routes.public import public_bp
    app.register_blueprint(public_bp)

    # -------------------------------------------------------------------------
    # Template Filters & Context Processors
    # -------------------------------------------------------------------------
    from utils.template_filters import register_template_filters, register_context_processors
    register_template_filters(app)
    register_context_processors(app)

    # -------------------------------------------------------------------------
    # Error Handlers
    # -------------------------------------------------------------------------
    @app.errorhandler(404)
    def not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403

    @app.errorhandler(500)
    def internal_error(e):
        db.session.rollback()  # Rollback any failed transactions
        return render_template('errors/500.html'), 500

    # -------------------------------------------------------------------------
    # Shell Context (for `flask shell`)
    # -------------------------------------------------------------------------
    @app.shell_context_processor
    def make_shell_context():
        from models.user import User
        from models.category import Category
        from models.subcategory import Subcategory
        from models.question import Question
        from models.quiz import QuizAttempt
        from models.result import Result
        from models.certificate import Certificate
        return {
            'db': db,
            'User': User,
            'Category': Category,
            'Subcategory': Subcategory,
            'Question': Question,
            'QuizAttempt': QuizAttempt,
            'Result': Result,
            'Certificate': Certificate,
        }

    return app


# =============================================================================
# Direct Execution (development only)
# =============================================================================
if __name__ == '__main__':
    import os
    env = os.getenv('FLASK_ENV', 'development')
    application = create_app(env)
    application.run(
        host='0.0.0.0',
        port=5000,
        debug=(env == 'development'),
        use_reloader=False
    )

