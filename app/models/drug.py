from app.extensions import db
from datetime import datetime


class Drug(db.Model):
    __tablename__ = "drugs"

    id = db.Column(db.Integer, primary_key=True)
    registration_number = db.Column(db.String(100), unique=True, nullable=False, index=True)
    trade_name = db.Column(db.String(255), nullable=False, index=True)
    active_ingredient = db.Column(db.String(255))
    dosage_form = db.Column(db.String(100))
    country_of_origin = db.Column(db.String(100))
    manufacturer = db.Column(db.String(255))
    registration_expiry = db.Column(db.String(50))  # kept as string - PPB dates come in inconsistent formats
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            "id": self.id,
            "registration_number": self.registration_number,
            "trade_name": self.trade_name,
            "active_ingredient": self.active_ingredient,
            "dosage_form": self.dosage_form,
            "country_of_origin": self.country_of_origin,
            "manufacturer": self.manufacturer,
            "registration_expiry": self.registration_expiry,
        }