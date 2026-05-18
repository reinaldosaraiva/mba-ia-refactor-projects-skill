"""Produto validation. One source of truth for create and update."""
from src.config.constants import (
    PRODUTO_NOME_MIN_LEN,
    PRODUTO_NOME_MAX_LEN,
    CATEGORIAS_VALIDAS,
    CATEGORIA_DEFAULT,
)
from src.errors import ValidationError


def _validate_common(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    if "nome" not in dados:
        raise ValidationError("Nome é obrigatório")
    if "preco" not in dados:
        raise ValidationError("Preço é obrigatório")
    if "estoque" not in dados:
        raise ValidationError("Estoque é obrigatório")
    nome = dados["nome"]
    preco = dados["preco"]
    estoque = dados["estoque"]
    categoria = dados.get("categoria", CATEGORIA_DEFAULT)
    if preco < 0:
        raise ValidationError("Preço não pode ser negativo")
    if estoque < 0:
        raise ValidationError("Estoque não pode ser negativo")
    if len(nome) < PRODUTO_NOME_MIN_LEN:
        raise ValidationError("Nome muito curto")
    if len(nome) > PRODUTO_NOME_MAX_LEN:
        raise ValidationError("Nome muito longo")
    if categoria not in CATEGORIAS_VALIDAS:
        raise ValidationError(f"Categoria inválida. Válidas: {list(CATEGORIAS_VALIDAS)}")
    return {
        "nome": nome,
        "descricao": dados.get("descricao", ""),
        "preco": preco,
        "estoque": estoque,
        "categoria": categoria,
    }


def validate_create(dados):
    return _validate_common(dados)


def validate_update(dados):
    return _validate_common(dados)
