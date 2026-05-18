"""Pedido validation."""
from src.config.constants import PEDIDO_STATUS_VALIDOS
from src.errors import ValidationError


def validate_create(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    usuario_id = dados.get("usuario_id")
    itens = dados.get("itens", [])
    if not usuario_id:
        raise ValidationError("Usuario ID é obrigatório")
    if not itens or len(itens) == 0:
        raise ValidationError("Pedido deve ter pelo menos 1 item")
    return {"usuario_id": usuario_id, "itens": itens}


def validate_status_update(dados):
    if not dados:
        raise ValidationError("Dados inválidos")
    novo_status = dados.get("status", "")
    if novo_status not in PEDIDO_STATUS_VALIDOS:
        raise ValidationError("Status inválido")
    return {"status": novo_status}
