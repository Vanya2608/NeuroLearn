from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime


# Initialize the database object
db = SQLAlchemy()

class User(db.Model, UserMixin):
    """Stores user account credentials."""
    # Indented 4 spaces
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)

    # Relationships to profile and history
    profile = db.relationship('UserProfile', backref='user', uselist=False, cascade='all, delete-orphan')
    history = db.relationship('ReadingHistory', backref='user', lazy=True)

class UserProfile(db.Model):
    """Stores UI preference settings for personalization."""
    # Indented 4 spaces
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # UI Preferences
    theme = db.Column(db.String(50), default='light')
    font_size = db.Column(db.String(50), default='medium')
    line_spacing = db.Column(db.String(50), default='normal')
    highlight_active = db.Column(db.Boolean, default=True)

    # Accessibility Voice Settings
    tts_speed = db.Column(db.Float, default=0.85)
    tts_pitch = db.Column(db.Float, default=1.0)

class ReadingHistory(db.Model):
    """Logs the text processed by the user for analytics."""
    # Indented 4 spaces
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    original_text = db.Column(db.Text, nullable=False)
    date_processed = db.Column(db.DateTime, default=datetime.utcnow)