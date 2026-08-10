"""
QuizNova — Jinja2 Template Filters & Context Processors
=========================================================
Registered in app factory to make utility functions available in all templates.
"""

from datetime import datetime
from utils.helpers import time_ago, format_seconds, truncate


def register_template_filters(app):
    """Register all custom Jinja2 filters with the Flask app."""

    @app.template_filter('timesince')
    def timesince_filter(dt):
        """{{ log.created_at | timesince }} → "5 minutes ago" """
        if not dt:
            return ''
        return time_ago(dt)

    @app.template_filter('time_ago')
    def time_ago_filter(dt):
        """{{ log.created_at | time_ago }} → "5 minutes ago" """
        if not dt:
            return ''
        return time_ago(dt)

    @app.template_filter('duration')
    def duration_filter(seconds):
        """{{ attempt.time_taken_seconds | duration }} → "26:36" """
        return format_seconds(seconds or 0)

    @app.template_filter('truncate_text')
    def truncate_text_filter(text, length=100):
        """{{ cat.description | truncate_text(80) }}"""
        return truncate(text or '', length)

    @app.template_filter('percentage')
    def percentage_filter(value):
        """{{ result.percentage | percentage }} → "87.5%" """
        try:
            return f'{float(value):.1f}%'
        except (TypeError, ValueError):
            return '0%'

    @app.template_filter('comma_number')
    def comma_number_filter(value):
        """{{ 1200 | comma_number }} → "1,200" """
        try:
            return f'{int(value):,}'
        except (TypeError, ValueError):
            return str(value)


def register_context_processors(app):
    """Register Jinja2 context processors for values available in all templates."""

    @app.context_processor
    def inject_globals():
        return {
            'now': datetime.utcnow(),
            'site_name': app.config.get('SITE_NAME', 'QuizNova'),
            'site_tagline': app.config.get('SITE_TAGLINE', 'Test Your Knowledge.'),
        }
