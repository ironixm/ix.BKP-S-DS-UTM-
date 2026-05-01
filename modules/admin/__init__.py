"""Blueprint MadMode admin (rota /madmode)."""
from .auth import init_auth, auth_bp
from .routes import bp
from .scheduler import start_scheduler


def register(app):
    """Registra blueprints + LoginManager no app Flask."""
    init_auth(app)
    app.register_blueprint(bp)
    # auth_bp também é montado em /madmode (login/logout)
    app.register_blueprint(auth_bp, url_prefix="/madmode")


__all__ = ["bp", "auth_bp", "init_auth", "register", "start_scheduler"]
