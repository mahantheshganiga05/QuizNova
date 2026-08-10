"""
QuizNova Models — Package Init
================================
Initializes the SQLAlchemy db instance shared across all model modules.
Import db from here in all model files to avoid circular imports.
"""

from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
