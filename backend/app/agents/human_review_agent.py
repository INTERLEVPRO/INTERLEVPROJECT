from backend.app.models.review import ReviewItem
from sqlalchemy.orm import Session
from typing import Optional

class HumanReviewAgent:
    def create_review_item(
        self, 
        db: Session, 
        item_type: str, 
        related_entity_type: str, 
        related_entity_id: int, 
        reason: str
    ) -> ReviewItem:
        """
        Creates a review item for the admin dashboard.
        Triggers: low confidence, missing fields, low match score, etc.
        """
        review_item = ReviewItem(
            item_type=item_type,
            related_entity_type=related_entity_type,
            related_entity_id=related_entity_id,
            reason=reason,
            status="pending"
        )
        db.add(review_item)
        db.commit()
        db.refresh(review_item)
        return review_item

    def resolve_review_item(self, db: Session, review_id: int, comment: Optional[str] = None):
        review_item = db.query(ReviewItem).filter(ReviewItem.id == review_id).first()
        if review_item:
            review_item.status = "resolved"
            review_item.admin_comment = comment
            db.commit()
        return review_item
