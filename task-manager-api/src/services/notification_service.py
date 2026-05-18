import logging
import smtplib

from src.config import settings
from src.utils.helpers import now_utc

logger = logging.getLogger("task-manager-api.notifications")


class NotificationService:
    def __init__(self, host=None, port=None, user=None, password=None):
        self.host = host if host is not None else settings.SMTP_HOST
        self.port = port if port is not None else settings.SMTP_PORT
        self.user = user if user is not None else settings.SMTP_USER
        self.password = password if password is not None else settings.SMTP_PASSWORD
        self.notifications = []

    def _enabled(self):
        return bool(self.host and self.user and self.password)

    def send_email(self, to, subject, body):
        if not self._enabled():
            logger.info("SMTP disabled — skip email to=%s subject=%s", to, subject)
            return False
        try:
            server = smtplib.SMTP(self.host, self.port)
            server.starttls()
            server.login(self.user, self.password)
            server.sendmail(self.user, to, f"Subject: {subject}\n\n{body}")
            server.quit()
            logger.info("Email enviado para %s", to)
            return True
        except smtplib.SMTPException:
            logger.exception("SMTP failure for %s", to)
            return False

    def notify_task_assigned(self, user, task):
        self.send_email(
            user.email,
            f"Nova task atribuída: {task.title}",
            f"Olá {user.name},\n\nA task '{task.title}' foi atribuída a você.\n"
            f"Prioridade: {task.priority}\nStatus: {task.status}",
        )
        self.notifications.append({
            "type": "task_assigned",
            "user_id": user.id,
            "task_id": task.id,
            "timestamp": now_utc(),
        })

    def notify_task_overdue(self, user, task):
        self.send_email(
            user.email,
            f"Task atrasada: {task.title}",
            f"Olá {user.name},\n\nA task '{task.title}' está atrasada!\n"
            f"Data limite: {task.due_date}",
        )

    def get_notifications(self, user_id):
        return [n for n in self.notifications if n["user_id"] == user_id]
