"""Health check — does not leak secrets."""
from src.models import get_db


def check():
    cur = get_db().cursor()
    cur.execute("SELECT 1")
    cur.execute("SELECT COUNT(*) FROM produtos")
    produtos = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM usuarios")
    usuarios = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM pedidos")
    pedidos = cur.fetchone()[0]
    return {
        "status": "ok",
        "database": "connected",
        "counts": {"produtos": produtos, "usuarios": usuarios, "pedidos": pedidos},
        "versao": "2.0.0",
    }
