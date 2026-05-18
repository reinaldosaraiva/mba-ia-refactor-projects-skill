"""Pedido orchestration. Notifications dispatched via the service interface."""
from src.errors import ValidationError
from src.models import pedido_model
from src.schemas import pedido_schema
from src.services.notification_service import NotificationService

_notifications = NotificationService()


def listar_todos():
    return pedido_model.todos()


def listar_por_usuario(usuario_id):
    return pedido_model.por_usuario(usuario_id)


def criar(dados):
    clean = pedido_schema.validate_create(dados)
    resultado = pedido_model.criar(clean["usuario_id"], clean["itens"])
    if "erro" in resultado:
        raise ValidationError(resultado["erro"])
    _notifications.pedido_criado(resultado["pedido_id"], clean["usuario_id"])
    return resultado


def atualizar_status(pedido_id, dados):
    clean = pedido_schema.validate_status_update(dados)
    pedido_model.atualizar_status(pedido_id, clean["status"])
    _notifications.pedido_status_changed(pedido_id, clean["status"])
