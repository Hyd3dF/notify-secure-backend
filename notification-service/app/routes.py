from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, User, SystemConfig, ApiKey, Notification
from sqlalchemy import desc
from .utils.security import hash_password, generate_encryption_key, encrypt_data
from .utils.firebase_manager import get_firebase_status
import os
import json
import secrets
import datetime

main = Blueprint('main', __name__)

@main.route('/')
@login_required
def index():
    return redirect(url_for('main.dashboard'))

@main.route('/register', methods=['GET', 'POST'])
def register():
    # Security: Only allow registration if no users exist
    if User.query.first():
        return redirect(url_for('main.login'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if not username or not password:
            flash('Username and password are required.')
            return redirect(url_for('main.register'))
            
        hashed_pw = hash_password(password)
        new_user = User(username=username, password_hash=hashed_pw)
        
        # Also generate/store a system encryption key if not exists
        if not SystemConfig.query.filter_by(key="ENCRYPTION_KEY").first():
            # In a real scenario, this key should be stored in env vars or a key manager, 
            # but per requirements, we store configs encrypted or manage keys here. 
            # Ideally, the MASTER key to decrypt the DB configs should be an Env Var.
            # For this setup: We assume the encryption key for other configs is stored in the DB? 
            # No, that's circular. 
            # We will use an ENV variable for the master encryption key.
            pass

        db.session.add(new_user)
        db.session.commit()
        
        login_user(new_user)
        return redirect(url_for('main.dashboard'))
        
    return render_template('register.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    # If no user exists, force redirect to register
    if not User.query.first():
        return redirect(url_for('main.register'))
        
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user)
            return redirect(url_for('main.dashboard'))
        else:
            flash('Login Failed. Check details.')
            
    return render_template('login.html')

@main.route('/dashboard')
@login_required
def dashboard():
    # Real Stats Data
    total_sent = Notification.query.count()
    failed_count = Notification.query.filter_by(status='failed').count()
    success_count = Notification.query.filter_by(status='success').count()
    
    success_rate = 0
    if total_sent > 0:
        success_rate = round((success_count / total_sent) * 100, 1)

    stats = {
        'total_sent': total_sent,
        'success_rate': success_rate,
        'failed_count': failed_count,
        'active_keys': ApiKey.query.count()
    }
    
    # Real Recent Activity
    recent_activity = Notification.query.order_by(desc(Notification.created_at)).limit(10).all()
    
    return render_template('dashboard.html', stats=stats, activity=recent_activity)

@main.route('/notification/<int:id>')
@login_required
def notification_details(id):
    notif = Notification.query.get_or_404(id)
    return json.dumps({
        'id': notif.id,
        'title': notif.title,
        'body': notif.body,
        'target': notif.target,
        'status': notif.status,
        'response': notif.response,
        'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M:%S')
    })

@main.route('/api-management')
@login_required
def api_management():
    keys = ApiKey.query.order_by(ApiKey.created_at.desc()).all()
    # Check if a new key was just created to show the report
    new_key_data = request.args.get('new_key_data') 
    if new_key_data:
        new_key_data = json.loads(new_key_data)
    
    return render_template('api.html', keys=keys, new_key_data=new_key_data, host=request.host_url)

@main.route('/api-management/create', methods=['POST'])
@login_required
def create_api_key():
    name = request.form.get('name', 'Mobile App')
    # Generate secure key
    raw_key = secrets.token_urlsafe(32)
    
    api_key = ApiKey(name=name, key=raw_key)
    db.session.add(api_key)
    db.session.commit()
    
    flash('New API Key Generated Successfully.')
    # Pass data to view for the Report
    key_data = json.dumps({'key': raw_key, 'name': name})
    return redirect(url_for('main.api_management', new_key_data=key_data))

@main.route('/api-management/revoke/<int:id>')
@login_required
def revoke_api_key(id):
    key = ApiKey.query.get(id)
    if key:
        db.session.delete(key)
        db.session.commit()
        flash('API Key Revoked.')
    return redirect(url_for('main.api_management'))

@main.route('/keys')
@login_required
def keys():
    status = get_firebase_status()
    # Check if FIREBASE_KEY env var is set
    has_key = os.environ.get('FIREBASE_KEY') is not None
    return render_template('keys.html', status=status, has_firebase_key=has_key)

# Upload route removed as we are using Environment Variables now.


@main.route('/send', methods=['GET', 'POST'])
@login_required
def send_notification():
    if request.method == 'POST':
        target = request.form.get('target')
        title = request.form.get('title')
        body = request.form.get('body')

        # logic to queue notification or send via Worker
        # Use decoupled sender utility
        from .utils.sender import process_and_send_notification
        
        success, msg = process_and_send_notification(title, body, target)
        
        if success:
            flash(f'Notification "{title}" queued successfully.')
        else:
            flash(f'Error sending notification: {msg}')
            
        return redirect(url_for('main.dashboard'))
        
    return render_template('send.html')

@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))
