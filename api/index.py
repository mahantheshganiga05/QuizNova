"""
QuizNova — Vercel Serverless Entry Point
==========================================
WSGI bridge that exposes Flask application factory to Vercel Serverless Functions.
"""

import os
import sys

# Ensure root project directory is in Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

# Instantiate Flask application for Vercel production runtime
env = os.environ.get('FLASK_ENV', 'production')
app = create_app(env)

if __name__ == '__main__':
    app.run()
