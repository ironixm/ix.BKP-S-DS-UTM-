"""Auth do /madmode usando flask-login (sessão via cookie).

Credenciais via ENV:
    ADMIN_USER   (default: madmode)
    ADMIN_PASS   (obrigatório — sem default seguro)
    SESSION_SECRET (chave de sessão; fallback random a cada start se ausente)
"""
from __future__ import annotations

import hmac
import os
import secrets
from functools import wraps

from flask import (
    Blueprint, Response, current_app, flash, jsonify, redirect,
    render_template, request, url_for,
)
from flask_login import (
    LoginManager, UserMixin, current_user, login_required as _login_required,
    login_user, logout_user,
)

login_manager = LoginManager()
login_manager.login_view = "madmode_auth.login"
login_manager.session_protection = "strong"


class AdminUser(UserMixin):
    def __init__(self, username: str):
        self.id = username


def _expected_user() -> str:
    return os.environ.get("ADMIN_USER", "madmode")


def _expected_pass() -> str:
    return os.environ.get("ADMIN_PASS", "")


def _check_creds(user: str, pwd: str) -> bool:
    eu = _expected_user()
    ep = _expected_pass()
    if not ep:
        return False
    return (
        hmac.compare_digest(user or "", eu)
        and hmac.compare_digest(pwd or "", ep)
    )


@login_manager.user_loader
def _load_user(uid: str):
    return AdminUser(uid) if uid == _expected_user() else None


@login_manager.unauthorized_handler
def _unauth():
    # APIs respondem JSON 401; HTML redireciona pro login
    if request.path.startswith("/madmode/api/"):
        return jsonify({"error": "unauthorized"}), 401
    return redirect(url_for("madmode_auth.login", next=request.path))


def init_auth(app):
    """Inicializa LoginManager e define SECRET_KEY se ainda não setada."""
    if not app.secret_key:
        app.secret_key = (
            os.environ.get("SESSION_SECRET")
            or os.environ.get("FLASK_SECRET_KEY")
            or secrets.token_hex(32)
        )
    login_manager.init_app(app)


def require_admin(fn):
    """Compatibilidade: agora apenas envelopa @login_required, mas devolve 503
    se ADMIN_PASS não estiver configurado."""
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not _expected_pass():
            return Response("MadMode não configurado: defina ADMIN_PASS.", 503)
        return _login_required(fn)(*args, **kwargs)
    return wrapper


# Blueprint só para login/logout (montado dentro de routes.py via include)
auth_bp = Blueprint(
    "madmode_auth", __name__,
    template_folder="../../templates/madmode",
)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if not _expected_pass():
        return Response("MadMode não configurado: defina ADMIN_PASS.", 503)
    error = None
    if request.method == "POST":
        u = (request.form.get("username") or "").strip()
        p = request.form.get("password") or ""
        if _check_creds(u, p):
            login_user(AdminUser(u), remember=True)
            nxt = request.args.get("next") or url_for("madmode.dashboard")
            if not nxt.startswith("/madmode"):
                nxt = url_for("madmode.dashboard")
            return redirect(nxt)
        error = "Credenciais inválidas."
    if current_user.is_authenticated:
        return redirect(url_for("madmode.dashboard"))
    return render_template("madmode/login.html", error=error)


@auth_bp.route("/logout", methods=["GET", "POST"])
def logout():
    logout_user()
    return redirect(url_for("madmode_auth.login"))
