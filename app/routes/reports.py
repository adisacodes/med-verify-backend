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
              description: Optional text label for the place
              example: Nairobi CBD, River Road
            latitude:
              type: number
              description: Latitude of the pin (-90 to 90). Send together with longitude.
              example: -1.2864
            longitude:
              type: number
              description: Longitude of the pin (-180 to 180). Send together with latitude.
              example: 36.8172
    responses:
      201:
        description: Report submitted successfully
      400:
        description: Invalid coordinates
      401:
        description: Missing or invalid JWT
    """
    user_id = int(get_jwt_identity())
    data = request.get_json()

    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if latitude is not None or longitude is not None:
        try:
            latitude = float(latitude)
            longitude = float(longitude)
        except (TypeError, ValueError):
            return jsonify({"error": "latitude and longitude must both be valid numbers"}), 400

        if not (-90 <= latitude <= 90 and -180 <= longitude <= 180):
            return jsonify({"error": "latitude or longitude is out of range"}), 400

    report = Report(
        reporter_id=user_id,
        drug_id=data.get("drug_id"),
        product_name_text=data.get("product_name_text"),
        description=data.get("description"),
        photo_url=data.get("photo_url"),
        location=data.get("location"),
        latitude=latitude,
        longitude=longitude,
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