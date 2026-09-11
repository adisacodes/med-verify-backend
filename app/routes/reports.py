from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.report import Report
from flask_jwt_extended import jwt_required, get_jwt_identity

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("", methods=["POST"])
@jwt_required()
def create_report():
    """Submitting a report requires login (prevents spam, allows follow-up)."""
    user_id = get_jwt_identity()
    data = request.get_json()

    report = Report(
        reporter_id=user_id,
        drug_id=data.get("drug_id"),
        product_name_text=data.get("product_name_text"),
        description=data.get("description"),
        photo_url=data.get("photo_url"),
        location=data.get("location"),
    )
    db.session.add(report)
    db.session.commit()

    return jsonify(report.to_dict()), 201


@reports_bp.route("", methods=["GET"])
def list_reports():
    """Public - anyone can see the community report feed (transparency)."""
    reports = Report.query.order_by(Report.created_at.desc()).limit(100).all()
    return jsonify([r.to_dict() for r in reports])