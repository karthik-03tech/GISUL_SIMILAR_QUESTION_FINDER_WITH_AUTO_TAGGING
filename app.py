import os
from dotenv import load_dotenv
from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import json
import numpy as np
from embedding_model import get_embedding, assign_tag
from qdrant_store import init_collection, store_vector, search_similar

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY']                  = os.environ.get('SECRET_KEY', 'dev-fallback-key')
app.config['SQLALCHEMY_DATABASE_URI']     = os.environ.get('DATABASE_URL', 'sqlite:///database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ─── MODELS ───────────────────────────────────────────────

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id       = db.Column(db.Integer, primary_key=True)
    email    = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Question(db.Model):
    __tablename__ = 'questions'

    id            = db.Column(db.Integer, primary_key=True)
    user_id       = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_text = db.Column(db.Text, nullable=False)
    topic_tag     = db.Column(db.String(100))
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

class History(db.Model):
    __tablename__ = 'history'

    id                = db.Column(db.Integer, primary_key=True)
    user_id           = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    question_id       = db.Column(db.Integer, db.ForeignKey('questions.id'), nullable=False)
    similar_questions = db.Column(db.Text)  # stored as JSON string

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ─── AUTH ROUTES ──────────────────────────────────────────

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']

        if User.query.filter_by(email=email).first():
            return render_template('register.html', error='Email already exists')

        hashed = generate_password_hash(password)
        user   = User(email=email, password=hashed)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email    = request.form['email']
        password = request.form['password']
        user     = User.query.filter_by(email=email).first()

        if not user or not check_password_hash(user.password, password):
            return render_template('login.html', error='Invalid email or password')

        login_user(user)
        return redirect(url_for('dashboard'))

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ─── MAIN ROUTES ──────────────────────────────────────────

@app.route('/')
@login_required
def dashboard():
    return render_template('dashboard.html')

@app.route('/ask', methods=['POST'])
@login_required
def ask():
    question_text = request.form.get('question')
    if not question_text:
        return redirect(url_for('dashboard'))

    # 1. Generate embedding
    new_embedding = get_embedding(question_text)

    # 2. Assign topic tag
    topic_tag = assign_tag(question_text)

    # 3. Search Qdrant for similar questions (before saving so we don't match itself)
    similar = search_similar(
        user_id   = current_user.id,
        embedding = new_embedding,
    )

    # 4. Save question to SQLite
    q = Question(
        user_id       = current_user.id,
        question_text = question_text,
        topic_tag     = topic_tag,
    )
    db.session.add(q)
    db.session.commit()

    # 5. Store embedding in Qdrant (point id = SQLite question id)
    store_vector(
        question_id = q.id,
        user_id     = current_user.id,
        embedding   = new_embedding,
        text        = question_text,
        tag         = topic_tag,
    )

    # 6. Save history record
    h = History(
        user_id           = current_user.id,
        question_id       = q.id,
        similar_questions = json.dumps(similar)
    )
    db.session.add(h)
    db.session.commit()

    return render_template('dashboard.html',
                           question=question_text,
                           tag=topic_tag,
                           similar=similar)

@app.route('/history')
@login_required
def history():
    tag_filter = request.args.get('tag')

    query = Question.query.filter_by(user_id=current_user.id)
    if tag_filter:
        query = query.filter_by(topic_tag=tag_filter)

    questions = query.order_by(Question.created_at.desc()).all()
    all_tags  = db.session.query(Question.topic_tag)\
                          .filter_by(user_id=current_user.id)\
                          .distinct().all()
    all_tags  = [t[0] for t in all_tags if t[0]]

    return render_template('history.html',
                           questions=questions,
                           all_tags=all_tags,
                           selected_tag=tag_filter)

# AI helpers are now in embedding_model.py (assign_tag, find_similar, get_embedding)

# ─── STARTUP ──────────────────────────────────────────────
with app.app_context():
    db.create_all()          # SQLite tables
init_collection()            # Qdrant collection

# ─── RUN ──────────────────────────────────────────────────

if __name__ == '__main__':
    app.run(debug=True)
