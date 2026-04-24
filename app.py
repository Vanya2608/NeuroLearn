import os
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_bcrypt import Bcrypt
from models import db, User, UserProfile, ReadingHistory
from processing import process_dyslexia_text
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'neuro-ai-secret-key-999'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///neuro_learn.db'
db.init_app(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
@login_manager.user_loader
def load_user(user_id):
 return User.query.get(int(user_id))
# --- ROUTES ---
@app.route('/')
def index():
 return render_template('index.html')
@app.route('/login', methods=['GET', 'POST'])
def login():
 if request.method == 'POST':
  user = User.query.filter_by(username=request.form.get('username')).first()
  if user and check_password_hash(user.password_hash, request.form.get('password')):
   login_user(user)
   return redirect(url_for('dashboard'))
 return render_template('login.html')
@app.route('/register', methods=['GET', 'POST'])
def register():
 if request.method == 'POST':
  hashed_pw = generate_password_hash(request.form.get('password'), method='pbkdf2:sha256')
  new_user = User(username=request.form.get('username'), password_hash=hashed_pw)
  db.session.add(new_user)
  db.session.commit()
  db.session.add(UserProfile(user_id=new_user.id))
  db.session.commit()
  return redirect(url_for('login'))
 return render_template('register.html')
@app.route('/logout')
def logout():
 logout_user()
 return redirect(url_for('index'))
@app.route('/process', methods=['POST'])
def process():
    data = request.get_json()
    processed_html = process_dyslexia_text(
        data['text'],
        syllables=data.get('syllables'),
        highlight_categories=data.get('highlights'),
        normalize=data.get('normalize')
    )
    if current_user.is_authenticated:
        db.session.add(ReadingHistory(user_id=current_user.id, original_text=data['text']))
        db.session.commit()
    return jsonify({'processed_html': processed_html})
@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    p = current_user.profile
    if request.method == 'POST':
        p.theme = request.form.get('theme')
        p.font_size = request.form.get('font_size')
        p.tts_speed = float(request.form.get('tts_speed', 0.85))
        db.session.commit()
        return redirect(url_for('profile'))
    return render_template('profile.html', profile=p)
@app.route('/dashboard')
@login_required
def dashboard():
    history = ReadingHistory.query.filter_by(user_id=current_user.id).order_by(ReadingHistory.date_processed.desc()).all()
    return render_template('dashboard.html', history=history, total_sessions=len(history))

@app.route('/about')
def about():  # <--- This "about" is the endpoint Flask is looking for
    return render_template('about.html')

@app.route('/api/user_preferences')
def get_prefs():
    p = current_user.profile if current_user.is_authenticated else None
    return jsonify({
        'theme': p.theme if p else 'light',
        'font_size': p.font_size if p else 'medium',
        'tts_speed': p.tts_speed if p else 0.85
    })
if __name__ == '__main__':
  with app.app_context():
   db.create_all()
app.run(debug=True)