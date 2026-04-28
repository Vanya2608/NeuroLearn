import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from models import db, User, UserProfile, ReadingHistory
from processing import process_dyslexia_text

app = Flask(__name__)
app.config['SECRET_KEY'] = 'super-secret-key-for-dyslexia-app'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///neuro_learn.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# --- Admin Setup ---
class AdminModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        return redirect(url_for('login'))

admin = Admin(app, name='Neuro_Learn Admin')
admin.add_view(AdminModelView(User, db.session))
admin.add_view(AdminModelView(UserProfile, db.session))
admin.add_view(AdminModelView(ReadingHistory, db.session))

# --- CLI Command for Admin creation ---
@app.cli.command("create-admin")
def create_admin():
    from getpass import getpass
    username = input("Enter admin username: ")
    password = getpass("Enter admin password: ")
    with app.app_context():
        if User.query.filter_by(username=username).first():
            print("User already exists.")
            return
        hashed_pw = bcrypt.generate_password_hash(password).decode('utf-8')
        admin_user = User(username=username, password_hash=hashed_pw, is_admin=True)
        db.session.add(admin_user)
        db.session.commit()
        print(f"Admin user {username} created successfully!")

# --- Routes ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/reader')
def reader():
    return render_template('reader.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('reader'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            login_user(user)
            return redirect(url_for('reader'))
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('reader'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists. Please choose a different one.', 'warning')
            return redirect(url_for('register'))
            
        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        user = User(username=username, password_hash=hashed_password)
        db.session.add(user)
        db.session.commit()
        
        # Create default profile
        profile = UserProfile(user_id=user.id)
        db.session.add(profile)
        db.session.commit()
        
        flash('Your account has been created! You are now able to log in', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    profile = current_user.profile
    if not profile:
        profile = UserProfile(user_id=current_user.id)
        db.session.add(profile)
        db.session.commit()
        
    if request.method == 'POST':
        profile.theme = request.form.get('theme', 'light')
        profile.font_size = request.form.get('font_size', 'medium')
        profile.line_spacing = request.form.get('line_spacing', 'normal')
        profile.tts_speed = float(request.form.get('tts_speed', 0.85))
        profile.tts_pitch = float(request.form.get('tts_pitch', 1.0))
        
        db.session.commit()
        flash('Your preferences have been updated!', 'success')
        return redirect(url_for('profile'))
        
    return render_template('profile.html', profile=profile)

@app.route('/api/user_preferences', methods=['GET'])
def get_preferences():
    if current_user.is_authenticated and current_user.profile:
        p = current_user.profile
        return jsonify({
            'theme': p.theme,
            'font_size': p.font_size,
            'line_spacing': p.line_spacing,
            'highlight_active': p.highlight_active,
            'tts_speed': p.tts_speed,
            'tts_pitch': p.tts_pitch
        })
    # Default for non-logged in users
    return jsonify({
        'theme': 'light',
        'font_size': 'medium', 
        'line_spacing': 'normal',
        'highlight_active': True,
        'tts_speed': 0.85,
        'tts_pitch': 1.0
    })

@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    
    if not data or 'text' not in data:
        return jsonify({'error': 'No text provided'}), 400
        
    text = data['text']
    simplify = data.get('simplify', False)
    syllables = data.get('syllables', False)
    highlight_categories = data.get('highlights', [])
    normalize = data.get('normalize', False)
    
    # Process text using our module
    processed_html = process_dyslexia_text(
        text, 
        simplify=simplify,
        syllables=syllables,
        highlight_categories=highlight_categories,
        normalize=normalize
    )
    
    # Save to history if logged in
    if current_user.is_authenticated:
        history = ReadingHistory(user_id=current_user.id, original_text=text)
        db.session.add(history)
        db.session.commit()
        
    return jsonify({
        'original': text,
        'processed_html': processed_html
    })

@app.route('/api/log_analytics', methods=['POST'])
@login_required
def log_analytics():
    data = request.get_json()
    latest = ReadingHistory.query.filter_by(user_id=current_user.id).order_by(ReadingHistory.date_processed.desc()).first()
    if latest:
        latest.duration_seconds = data.get('duration', 0)
        latest.word_count = data.get('words', 0)
        db.session.commit()
        return jsonify({'status': 'success'})
    return jsonify({'error': 'No session found'}), 404

@app.route('/dashboard')
@login_required
def dashboard():
    # Fetch user's reading history, newest first
    history = ReadingHistory.query.filter_by(user_id=current_user.id).order_by(ReadingHistory.date_processed.desc()).all()
    
    # Calculate simple stats
    total_sessions = len(history)
    
    return render_template('dashboard.html', history=history, total_sessions=total_sessions)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)

