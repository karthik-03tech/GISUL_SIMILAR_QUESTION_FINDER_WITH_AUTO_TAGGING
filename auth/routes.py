from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app import db
from models import User

# Create the auth Blueprint
auth_bp = Blueprint("auth", __name__, url_prefix="/")


# ─────────────────────────────────────────────────────────────────────────────
# REGISTER  →  GET /register  |  POST /register
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # If already logged in, send to home/dashboard
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        confirm = request.form.get("confirm_password", "")

        # ── Validation ──────────────────────────────────────────────
        if not email or not password:
            flash("Email and password are required.", "danger")
            return render_template("register.html")

        if password != confirm:
            flash("Passwords do not match.", "danger")
            return render_template("register.html")

        if len(password) < 6:
            flash("Password must be at least 6 characters.", "danger")
            return render_template("register.html")

        if User.query.filter_by(email=email).first():
            flash("An account with that email already exists.", "warning")
            return render_template("register.html")

        # ── Create user ─────────────────────────────────────────────
        new_user = User(email=email)
        # generate_password_hash() is called inside set_password()
        # It produces:  pbkdf2:sha256:260000$<salt>$<hash>
        # The plain-text password is NEVER written to the DB.
        new_user.set_password(password)

        db.session.add(new_user)
        db.session.commit()

        flash("Account created! You can now log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")


# ─────────────────────────────────────────────────────────────────────────────
# LOGIN  →  GET /login  |  POST /login
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("auth.dashboard"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        remember = bool(request.form.get("remember"))   # "Remember Me" checkbox

        user = User.query.filter_by(email=email).first()

        # check_password_hash() is called inside user.check_password()
        # It safely compares the provided plain-text against the stored hash.
        if user is None or not user.check_password(password):
            flash("Invalid email or password.", "danger")
            return render_template("login.html")

        # Flask-Login: set the user session cookie
        login_user(user, remember=remember)
        flash(f"Welcome back, {user.email}!", "success")

        # Redirect to the page the user originally tried to visit (if any)
        next_page = request.args.get("next")
        return redirect(next_page or url_for("auth.dashboard"))

    return render_template("login.html")


# ─────────────────────────────────────────────────────────────────────────────
# LOGOUT  →  GET /logout   (login required)
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()           # Flask-Login: clears the session
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))


# ─────────────────────────────────────────────────────────────────────────────
# DASHBOARD  →  GET /   (protected example route)
# ─────────────────────────────────────────────────────────────────────────────
@auth_bp.route("/")
@login_required
def dashboard():
    return render_template("dashboard.html")
