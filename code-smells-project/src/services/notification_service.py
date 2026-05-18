"""Side-effect dispatch for pedido lifecycle notifications.

Replaces the inline `print("ENVIANDO EMAIL/SMS/PUSH")` calls scattered through
the old controllers.py. The real implementation would talk to an email/SMS
provider; this stub logs so the refactor is functionally observable.
"""
import logging


class NotificationService:
    def __init__(self, logger=None):
        self._log = logger or logging.getLogger("notifications")

    def pedido_criado(self, pedido_id, usuario_id):
        self._log.info("pedido_criado pedido_id=%s usuario_id=%s", pedido_id, usuario_id)

    def pedido_status_changed(self, pedido_id, novo_status):
        self._log.info("pedido_status_changed pedido_id=%s status=%s", pedido_id, novo_status)
