from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.application import Application
from backend.app.models.review import ReviewItem
from pydantic import BaseModel
from typing import Optional

router = APIRouter()

class ReviewDecision(BaseModel):
    comment: Optional[str] = None

@router.get("/")
def get_review_items(db: Session = Depends(get_db)):
    """List all pending review items."""
    return db.query(ReviewItem).filter(ReviewItem.status == "pending").all()

@router.post("/{review_id}/approve")
def approve_item(review_id: int, decision: ReviewDecision, db: Session = Depends(get_db)):
    """Approve a review item."""
    item = db.query(ReviewItem).filter(ReviewItem.id == review_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    item.status = "resolved"
    item.admin_comment = decision.comment or "Approved by admin"
    if item.related_entity_type == "application":
        application = db.query(Application).filter(Application.id == item.related_entity_id).first()
        if application:
            application.status = "approved"
            application.approved_by = "admin"
    db.commit()
    return {"message": "Item approved"}

@router.post("/{review_id}/reject")
def reject_item(review_id: int, decision: ReviewDecision, db: Session = Depends(get_db)):
    """Reject a review item."""
    item = db.query(ReviewItem).filter(ReviewItem.id == review_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Review item not found")
    
    item.status = "dismissed"
    item.admin_comment = decision.comment or "Rejected by admin"
    if item.related_entity_type == "application":
        application = db.query(Application).filter(Application.id == item.related_entity_id).first()
        if application:
            application.status = "rejected"
    db.commit()
    return {"message": "Item rejected"}
