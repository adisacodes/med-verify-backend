from app.extensions import db
from datetime import datetime


class Report(db.Model):
    __tablename__ = "reports"

    id = db.Column(db.Integer, primary_key=True)
    reporter_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    drug_id = db.Column(db.Integer, db.ForeignKey("drugs.id"), nullable=True)  # nullable: product might not be in our DB at all
    product_name_text = db.Column(db.String(255))  # free-text fallback if drug_id is unknown
    description = db.Column(db.Text)
    photo_url = db.Column(db.String(500))
    location = db.Column(db.String(255))
    status = db.Column(db.String(20), default="pending")  # pending / reviewed / confirmed / dismissed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    drug = db.relationship("Drug", backref="reports", lazy=True)

    def to_dict(self):
        return {
            "id": self.id,
            "reporter_id": self.reporter_id,
            "drug_id": self.drug_id,
            "product_name_text": self.product_name_text,
            "description": self.description,
            "photo_url": self.photo_url,
            "location": self.location,
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }