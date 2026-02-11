from flask import (
    flash, Blueprint, request, redirect, url_for,
    session, render_template, current_app
)
from werkzeug.security import generate_password_hash, check_password_hash
from flights.config import get_db_connection
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from flask_mail import Message
import re

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]

        errors = []

        if len(password) < 8:
            errors.append("at least 8 characters")
        if not re.search(r"[A-Za-z]", password):
            errors.append("at least one letter")
        if not re.search(r"\d", password):
            errors.append("at least one number")
        if not re.search(r"[@$!%*?&]", password):
            errors.append("at least one special character (@$!%*?&)")

        if errors:
            return render_template(
                "signup.html",
                errors=errors,
                name=name,
                email=email
            )

        hashed_password = generate_password_hash(password)
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
            (name, email, hashed_password),
        )
        conn.commit()
        cur.close()
        conn.close()

        flash("Signup successful! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("signup.html")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT user_id, password, name FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()
        conn.close()

        if user and check_password_hash(user[1], password):
            session["user_id"] = user[0]
            session["username"] = user[2]

            next_url = request.args.get("next")
            tickets = request.args.get("tickets")
            if next_url:
                if tickets:
                    return redirect(f"{next_url}?tickets={tickets}")
                return redirect(next_url)

            return redirect(url_for("flights.search_flights"))
        else:
            return "Invalid credentials"

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("auth.login"))


def get_serializer():
    """Helper to create serializer using current_app.secret_key"""
    return URLSafeTimedSerializer(current_app.secret_key)


@auth_bp.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        email = request.form["email"]

        # generate secure token
        s = get_serializer()
        token = s.dumps(email, salt="password-reset-salt")
        reset_url = url_for("auth.reset_password", token=token, _external=True)

        # prepare email
        msg = Message("Password Reset Request", recipients=[email])
        msg.body = f"""
        Hello,

        Click the link below to reset your password:
        {reset_url}

        This link is valid for 1 hour.
        """

        # ✅ send using current_app
        from flask import current_app
        mail = current_app.extensions.get("mail")
        mail.send(msg)

        flash("Check your email for password reset instructions!", "info")
        return redirect(url_for("auth.login"))

    return render_template("forgot_password.html")


@auth_bp.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    s = get_serializer()
    try:
        email = s.loads(token, salt="password-reset-salt", max_age=3600)
    except (SignatureExpired, BadSignature):
        return "Invalid or expired reset link."

    if request.method == "POST":
        new_password = request.form["password"]
        hashed_pw = generate_password_hash(new_password)

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password=%s WHERE email=%s", (hashed_pw, email))
        conn.commit()
        cur.close()
        conn.close()

        flash("Password updated successfully! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html")
