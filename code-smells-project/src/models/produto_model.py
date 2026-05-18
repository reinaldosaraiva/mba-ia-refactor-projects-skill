"""Produto data access — parameterised queries only."""
from src.models import get_db

FIELDS = ("id", "nome", "descricao", "preco", "estoque", "categoria", "ativo", "criado_em")


def _row_to_dict(row):
    return {f: row[f] for f in FIELDS}


def todos():
    cur = get_db().cursor()
    cur.execute("SELECT * FROM produtos")
    return [_row_to_dict(r) for r in cur.fetchall()]


def por_id(produto_id):
    cur = get_db().cursor()
    cur.execute("SELECT * FROM produtos WHERE id = ?", (produto_id,))
    row = cur.fetchone()
    return _row_to_dict(row) if row else None


def criar(nome, descricao, preco, estoque, categoria):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
        (nome, descricao, preco, estoque, categoria),
    )
    db.commit()
    return cur.lastrowid


def atualizar(produto_id, nome, descricao, preco, estoque, categoria):
    db = get_db()
    cur = db.cursor()
    cur.execute(
        "UPDATE produtos SET nome = ?, descricao = ?, preco = ?, estoque = ?, categoria = ? WHERE id = ?",
        (nome, descricao, preco, estoque, categoria, produto_id),
    )
    db.commit()


def deletar(produto_id):
    db = get_db()
    cur = db.cursor()
    cur.execute("DELETE FROM produtos WHERE id = ?", (produto_id,))
    db.commit()


def buscar(termo=None, categoria=None, preco_min=None, preco_max=None):
    """Dynamic WHERE built from whitelisted clauses; values are parameterised."""
    clauses = ["1=1"]
    params = []
    if termo:
        clauses.append("(nome LIKE ? OR descricao LIKE ?)")
        like = f"%{termo}%"
        params.extend([like, like])
    if categoria:
        clauses.append("categoria = ?")
        params.append(categoria)
    if preco_min is not None:
        clauses.append("preco >= ?")
        params.append(preco_min)
    if preco_max is not None:
        clauses.append("preco <= ?")
        params.append(preco_max)
    sql = "SELECT * FROM produtos WHERE " + " AND ".join(clauses)
    cur = get_db().cursor()
    cur.execute(sql, params)
    return [_row_to_dict(r) for r in cur.fetchall()]
