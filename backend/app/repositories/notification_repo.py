"""Notification Repository."""

from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from sqlalchemy import select, update
from app.models.notification import Notification
from app.repositories.base import BaseRepository


class NotificationRepository(BaseRepository[Notification]):
    """Data access repository for user notifications."""

    def __init__(self, db: Session):
        super().__init__(Notification, db)

    def list_by_user(self, user_id: str, limit: int = 50) -> List[Notification]:
        """Fetch notifications for a user."""
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.created_at.desc())
            .limit(limit)
        )
        return list(self.db.scalars(stmt).all())

    def list_unread_by_user(self, user_id: str) -> List[Notification]:
        """Fetch unread notifications for a user."""
        stmt = (
            select(Notification)
            .where(Notification.user_id == user_id, Notification.is_read.is_(False))
            .order_by(Notification.created_at.desc())
        )
        return list(self.db.scalars(stmt).all())

    def mark_as_read(self, notification_id: str) -> bool:
        """Mark single notification as read."""
        notif = self.get(notification_id)
        if notif and not notif.is_read:
            notif.is_read = True
            notif.read_at = datetime.utcnow()
            self.db.commit()
            return True
        return False
