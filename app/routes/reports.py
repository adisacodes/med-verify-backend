from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.report import Report
from flask_jwt_extended import jwt_required, get_jwt_identity

reports_bp = Blueprint("reports", __name__)


@reports_bp.route("", methods=["POST"])
@jwt_required()
def create_report():
    """
    Submit a counterfeit/suspicious product report
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            drug_id:
              type: integer
              description: Internal ID if the product exists in our database (optional)
              example: 1
            product_name_text:
              type: string
              description: Free-text product name if drug_id is unknown
              example: Panadol Extra
            description:
              type: string
              example: Packaging looked off, blister pack seal was broken
            photo_url:
              type: string
              example: https://example.com/photo.jpg
            location:
              type: string
              example: Nairobi CBD, River Road
    responses:
      201:
        description: Report submitted successfully
      401:
        description: Missing or invalid JWT
    """
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
    """
    List recent community reports
    ---
    tags:
      - Reports
    responses:
      200:
        description: List of the most recent reports, newest first
    """
    reports = Report.query.order_by(Report.created_at.desc()).limit(100).all()
    return jsonify([r.to_dict() for r in reports])