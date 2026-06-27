from typing import Any, Optional

from sqlalchemy.orm import Session

from backend.app.models.notification import Notification


class NotificationAgent:
    @staticmethod
    def notify(
        db: Session,
        title: str,
        message: str,
        level: str = "info",
        category: str = "system",
        data: Optional[Any] = None,
    ) -> Notification | None:
        try:
            notification = Notification(
                title=title,
                message=message,
                level=level,
                category=category,
                data=data,
            )
            db.add(notification)
            db.commit()
            return notification
        except Exception:
            db.rollback()
            return None
