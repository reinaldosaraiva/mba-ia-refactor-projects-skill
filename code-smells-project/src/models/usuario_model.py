"""Usuario data access — parameterised queries only.

NOTE: Passwords remain stored in plaintext in this refactor (functional
preservation of the original schema and seed). Migrating to bcrypt is
recorded as a residual in the audit Validation block; it is a follow-up
session, not part of v1 of this skill.
"""
from src.models import get_db
from src.config.constants import USUARIO_TIPO_DEFAULT

PUBLIC_FIELDS = ("id", "nome", "email", "tipo", "criado_em")


def _row_to_public_dict(row):
    return {f: row[f] for f in PUBLIC_FIELDS}


def todos():
    cur = get_db().cursor()
    cur.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios")
    return [_row_to_public_dict(r) for r in cur.fetchall()]


def por_id(usuario_id):
    cur = get_db().cursor()
    cur.execute("SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE id = ?", (usuario_id,))
    row = cur.fetchone()
    return _row_to_public_dict(row) if row else None


def autenticar(email, senha):
    """Return the public user dict on credential match, else None."""
    cur = get_db().cursor()
    cur.execute(
        "SELECT id, nome, email, tipo, criado_em FROM usuarios WHERE email = ? AND senha = ?",
        (email, senha),
    )
    row = cur.fetchone()
    return _row_to_public_dict(row) if row else None


def criar(nome, email, senha, tipo=USUARIO_TIPO_DEFAULT):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
        (nome, email, senha, tipo),
    )
    db.commit()
    return cur.lastrowid
