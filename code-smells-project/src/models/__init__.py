"""Per-request SQLite connection plus DDL and idempotent seed.

Replaces the module-level singleton `db_connection` with a Flask-`g` pattern.
DDL and seed run once during app initialisation via `init_db(app)`.
"""
import sqlite3
from flask import g

from src.config import settings


def _connect():
    conn = sqlite3.connect(settings.DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_db():
    """Return the current request's connection, opening it on demand."""
    if "db" not in g:
        g.db = _connect()
    return g.db


def close_db(_exc=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_db(app):
    """Register teardown, create schema, and seed the database once."""
    app.teardown_appcontext(close_db)
    with app.app_context():
        conn = _connect()
        cursor = conn.cursor()
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS produtos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                descricao TEXT,
                preco REAL,
                estoque INTEGER,
                categoria TEXT,
                ativo INTEGER DEFAULT 1,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT,
                email TEXT,
                senha TEXT,
                tipo TEXT DEFAULT 'cliente',
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS pedidos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER,
                status TEXT DEFAULT 'pendente',
                total REAL,
                criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS itens_pedido (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pedido_id INTEGER,
                produto_id INTEGER,
                quantidade INTEGER,
                preco_unitario REAL
            );
            """
        )
        conn.commit()
        cursor.execute("SELECT COUNT(*) FROM produtos")
        if cursor.fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO produtos (nome, descricao, preco, estoque, categoria) VALUES (?, ?, ?, ?, ?)",
                [
                    ("Notebook Gamer", "Notebook potente para jogos", 5999.99, 10, "informatica"),
                    ("Mouse Wireless", "Mouse sem fio ergonômico", 89.90, 50, "informatica"),
                    ("Teclado Mecânico", "Teclado mecânico RGB", 299.90, 30, "informatica"),
                    ("Monitor 27''", "Monitor 27 polegadas 144hz", 1899.90, 15, "informatica"),
                    ("Headset Gamer", "Headset com microfone", 199.90, 25, "informatica"),
                    ("Cadeira Gamer", "Cadeira ergonômica", 1299.90, 8, "moveis"),
                    ("Webcam HD", "Webcam 1080p", 249.90, 20, "informatica"),
                    ("Hub USB", "Hub USB 3.0 7 portas", 79.90, 40, "informatica"),
                    ("SSD 1TB", "SSD NVMe 1TB", 449.90, 35, "informatica"),
                    ("Camiseta Dev", "Camiseta estampa código", 59.90, 100, "vestuario"),
                ],
            )
            cursor.executemany(
                "INSERT INTO usuarios (nome, email, senha, tipo) VALUES (?, ?, ?, ?)",
                [
                    ("Admin", "admin@loja.com", "admin123", "admin"),
                    ("João Silva", "joao@email.com", "123456", "cliente"),
                    ("Maria Santos", "maria@email.com", "senha123", "cliente"),
                ],
            )
            conn.commit()
        conn.close()
