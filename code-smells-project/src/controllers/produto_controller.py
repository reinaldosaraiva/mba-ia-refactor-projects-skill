"""Produto orchestration: validate → model → return data."""
from src.errors import NotFoundError
from src.models import produto_model
from src.schemas import produto_schema


def listar():
    return produto_model.todos()


def buscar(termo=None, categoria=None, preco_min=None, preco_max=None):
    if preco_min is not None:
        preco_min = float(preco_min)
    if preco_max is not None:
        preco_max = float(preco_max)
    return produto_model.buscar(termo, categoria, preco_min, preco_max)


def detalhar(produto_id):
    produto = produto_model.por_id(produto_id)
    if not produto:
        raise NotFoundError("Produto não encontrado")
    return produto


def criar(dados):
    clean = produto_schema.validate_create(dados)
    produto_id = produto_model.criar(**clean)
    return {"id": produto_id}


def atualizar(produto_id, dados):
    existente = produto_model.por_id(produto_id)
    if not existente:
        raise NotFoundError("Produto não encontrado")
    clean = produto_schema.validate_update(dados)
    produto_model.atualizar(produto_id, **clean)


def deletar(produto_id):
    existente = produto_model.por_id(produto_id)
    if not existente:
        raise NotFoundError("Produto não encontrado")
    produto_model.deletar(produto_id)
