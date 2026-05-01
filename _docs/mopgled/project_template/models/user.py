# ╔═════════════════════════════════════════════════════════════════╗
# ║    ▄▄███▄▄    ┌────────────────────────────────────────────────┐║
# ║  ▄█▛▘‾ ‾▝▜█▄  │ User – V1.0.1                                  │║
# ║ ██▘       ▝██ │                                                │║
# ║ ██▖       ▗██ ├────────────────────────────────────────────────┤║
# ║ ███▄_   _▄███ │ By Ir.On                                       │║
# ║ █████████████ │ Agent: Copilot | Sessao: branch:main           │║
# ║ ██ ▀ ████████ │ Ultima modificacao: 2026-02-11 - 12:13         │║
# ║ ██ ● ██▀██▀██ │ ironix.com.br                                  │║
# ║ ▜▛   ██ ▜▛ ██ ├────────────────────────────────────────────────┤║
# ║      ██    ▜▛ │ Caminho:                                       │║
# ║      ▜▛       │ _docs/mopgled/project_template/models/user.py  │║
# ║               ├────────────────────────────────────────────────┤║
# ║               │ Detalhes:                                      │║
# ║               │ * V1.0.1 - [sem detalhes]                      │║
# ║               │                                                │║
# ║               └────────────────────────────────────────────────┘║
# ╚═════════════════════════════════════════════════════════════════╝


from flask_login import UserMixin

from extensions import db


class User(db.Model, UserMixin):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(120), nullable=False, unique=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(40), nullable=False, default="USER")
    created_at = db.Column(db.DateTime, server_default=db.func.now())

    def __repr__(self):
        return f"<User {self.username}>"
