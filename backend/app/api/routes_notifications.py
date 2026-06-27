from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.app.agents.notification_agent import NotificationAgent
from backend.app.database import get_db
from backend.app.models.notification import Notification


router = APIRouter()


class NotificationCreate(BaseModel):
    title: str
    message: str
    level: str = "info"
    category: str = "system"
    data: Optional[Dict[str, Any]] = None


@router.get("/")
def get_notifications(unread_only: bool = False, db: Session = Depends(get_db)):
    query = db.query(Notification)
    if unread_only:
        query = query.filter(Notification.is_read == False)  # noqa: E712
    return query.order_by(Notification.created_at.desc()).all()


@router.post("/")
def create_notification(payload: NotificationCreate, db: Session = Depends(get_db)):
    notification = NotificationAgent.notify(
        db,
        payload.title,
        payload.message,
        payload.level,
        payload.category,
        payload.data,
    )
    if not notification:
        raise HTTPException(status_code=500, detail="Notification could not be created")
    return notification


@router.patch("/{notification_id}/read")
def mark_notification_read(notification_id: int, db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(Notification.id == notification_id).first()
    if not notification:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification
