from flask import Flask, redirect, url_for
from flask_login import LoginManager
from .models import db, User
import os

login_manager = LoginManager()
login_manager.login_view = 'main.login'

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'default-dev-secret-key')
    app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///site.db')
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Initialize Extensions
    db.init_app(app)
    login_manager.init_app(app)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Blueprint Registration
    from .routes import main as main_blueprint
    app.register_blueprint(main_blueprint)

    # Database Creation (First run logic context)
    with app.app_context():
        db.create_all()
        
    # Initialize Firebase from Env Var
    from .utils.firebase_manager import init_firebase
    init_firebase()

    return app
