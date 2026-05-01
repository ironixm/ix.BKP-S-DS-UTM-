# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ Auth – V1.0.1                                  │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-11 - 12:13         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ _docs/mopgled/project_template/core/auth.py    │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.1 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝


import os

from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import login_user, logout_user
from werkzeug.security import check_password_hash, generate_password_hash

from extensions import db, login_manager
from models.user import User

bp = Blueprint("auth", __name__)


@login_manager.user_loader
def load_user(user_id: str):
    try:
        return User.query.get(int(user_id))
    except Exception:
        return None


def _ensure_default_user() -> User:
    username = os.getenv("DEFAULT_ADMIN_USER", "admin")
    password = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin")
    user = User.query.filter_by(username=username).first()
    if user:
        return user
    user = User(
        username=username,
        email=os.getenv("DEFAULT_ADMIN_EMAIL", "admin@local"),
        role="SUPERADMIN",
        password_hash=generate_password_hash(password),
    )
    db.session.add(user)
    db.session.commit()
    return user


@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("sigla", "").strip()
        password = request.form.get("senha", "").strip()
        if not username or not password:
            flash("Preencha usuario e senha.", "warning")
            return render_template("login.html")
        user = User.query.filter_by(username=username).first()
        if not user and username == os.getenv("DEFAULT_ADMIN_USER", "admin"):
            user = _ensure_default_user()
        if not user or not check_password_hash(user.password_hash, password):
            flash("Credenciais invalidas.", "danger")
            return render_template("login.html")
        login_user(user)
        return redirect(url_for("core.index"))
    return render_template("login.html")


@bp.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("auth.login"))
