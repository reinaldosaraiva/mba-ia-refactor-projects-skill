"""Pedido data access — parameterised queries plus JOIN-based N+1 fix."""
from collections import defaultdict

from src.models import get_db


def _query_pedidos_with_itens(where_clause, params):
    """Single JOIN that produces one row per item; grouped in Python."""
    sql = f"""
        SELECT
            p.id AS pedido_id,
            p.usuario_id,
            p.status,
            p.total,
            p.criado_em,
            ip.produto_id,
            ip.quantidade,
            ip.preco_unitario,
            pr.nome AS produto_nome
        FROM pedidos p
        LEFT JOIN itens_pedido ip ON ip.pedido_id = p.id
        LEFT JOIN produtos pr ON pr.id = ip.produto_id
        {where_clause}
        ORDER BY p.id, ip.id
    """
    cur = get_db().cursor()
    cur.execute(sql, params)
    grouped = {}
    order = []
    for row in cur.fetchall():
        pid = row["pedido_id"]
        if pid not in grouped:
            grouped[pid] = {
                "id": pid,
                "usuario_id": row["usuario_id"],
                "status": row["status"],
                "total": row["total"],
                "criado_em": row["criado_em"],
                "itens": [],
            }
            order.append(pid)
        if row["produto_id"] is not None:
            grouped[pid]["itens"].append({
                "produto_id": row["produto_id"],
                "produto_nome": row["produto_nome"] or "Desconhecido",
                "quantidade": row["quantidade"],
                "preco_unitario": row["preco_unitario"],
            })
    return [grouped[pid] for pid in order]


def por_usuario(usuario_id):
    return _query_pedidos_with_itens("WHERE p.usuario_id = ?", (usuario_id,))


def todos():
    return _query_pedidos_with_itens("", ())


def criar(usuario_id, itens):
    """Validate stock, compute total, INSERT pedido + itens + UPDATE estoque atomically."""
    db = get_db()
    cur = db.cursor()
    total = 0.0
    for item in itens:
        cur.execute("SELECT * FROM produtos WHERE id = ?", (item["produto_id"],))
        produto = cur.fetchone()
        if produto is None:
            return {"erro": f"Produto {item['produto_id']} não encontrado"}
        if produto["estoque"] < item["quantidade"]:
            return {"erro": f"Estoque insuficiente para {produto['nome']}"}
        total += produto["preco"] * item["quantidade"]

    cur.execute(
        "INSERT INTO pedidos (usuario_id, status, total) VALUES (?, 'pendente', ?)",
        (usuario_id, total),
    )
    pedido_id = cur.lastrowid

    for item in itens:
        cur.execute("SELECT preco FROM produtos WHERE id = ?", (item["produto_id"],))
        preco = cur.fetchone()["preco"]
        cur.execute(
            "INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario) VALUES (?, ?, ?, ?)",
            (pedido_id, item["produto_id"], item["quantidade"], preco),
        )
        cur.execute(
            "UPDATE produtos SET estoque = estoque - ? WHERE id = ?",
            (item["quantidade"], item["produto_id"]),
        )

    db.commit()
    return {"pedido_id": pedido_id, "total": total}


def atualizar_status(pedido_id, novo_status):
    db = get_db()
    cur = db.cursor()
    cur.execute("UPDATE pedidos SET status = ? WHERE id = ?", (novo_status, pedido_id))
    db.commit()


def aggregate_for_report():
    """Single aggregate query replacing the 5 separate COUNT/SUM queries."""
    cur = get_db().cursor()
    cur.execute(
        """
        SELECT
            COUNT(*) AS total_pedidos,
            COALESCE(SUM(total), 0) AS faturamento,
            SUM(CASE WHEN status = 'pendente' THEN 1 ELSE 0 END) AS pendentes,
            SUM(CASE WHEN status = 'aprovado' THEN 1 ELSE 0 END) AS aprovados,
            SUM(CASE WHEN status = 'cancelado' THEN 1 ELSE 0 END) AS cancelados
        FROM pedidos
        """
    )
    row = cur.fetchone()
    return {
        "total_pedidos": row["total_pedidos"],
        "faturamento": row["faturamento"],
        "pendentes": row["pendentes"] or 0,
        "aprovados": row["aprovados"] or 0,
        "cancelados": row["cancelados"] or 0,
    }
