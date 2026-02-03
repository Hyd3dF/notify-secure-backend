from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from .utils.security import verify_password
import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(500), nullable=False)
    
    def check_password(self, password):
        return verify_password(self.password_hash, password)

class SystemConfig(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=False) # Encrypted value
    updated_at = db.Column(db.DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    @staticmethod
    def get_value(key):
        config = SystemConfig.query.filter_by(key=key).first()
        return config.value if config else None

class ApiKey(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    key = db.Column(db.String(64), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    target = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(20), default='pending') # success, failed
    response = db.Column(db.Text, nullable=True) # JSON response from provider
    created_at = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    
    # Optional: Link to API Key if sent via API
    api_key_id = db.Column(db.Integer, db.ForeignKey('api_key.id'), nullable=True)
    api_key = db.relationship('ApiKey', backref=db.backref('notifications', lazy=True))
