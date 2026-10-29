from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.report import Report
from app.utils.auth import admin_required
from flask_jwt_extended import jwt_required, get_jwt_identity

reports_bp = Blueprint("reports", __name__)

VALID_STATUSES = ("pending", "approved", "rejected")


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
        description: Report submitted. It starts as "pending" and is not public until an admin approves it.
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
    List approved community reports (public)
    ---
    tags:
      - Reports
    responses:
      200:
        description: Approved reports only, newest first. The reporter's identity is not included.
    """
    reports = (
        Report.query.filter_by(status="approved")
        .order_by(Report.created_at.desc())
        .limit(100)
        .all()
    )
    public = [
        {k: v for k, v in r.to_dict().items() if k != "reporter_id"}
        for r in reports
    ]
    return jsonify(public)


@reports_bp.route("/mine", methods=["GET"])
@jwt_required()
def my_reports():
    """
    List the logged-in user's own reports, with their review status
    ---
    tags:
      - Reports
    security:
      - Bearer: []
    responses:
      200:
        description: The user's own reports in any status, newest first
      401:
        description: Missing or invalid JWT
    """
    user_id = int(get_jwt_identity())
    reports = (
        Report.query.filter_by(reporter_id=user_id)
        .order_by(Report.created_at.desc())
        .all()
    )
    return jsonify([r.to_dict() for r in reports])


@reports_bp.route("/review", methods=["GET"])
@admin_required
def review_queue():
    """
    Admin: list reports waiting for review
    ---
    tags:
      - Reports (admin)
    security:
      - Bearer: []
    parameters:
      - name: status
        in: query
        type: string
        required: false
        description: pending (default), approved, or rejected
    responses:
      200:
        description: Reports with the given status, oldest first so nothing waits forever
      400:
        description: Invalid status
      401:
        description: Missing or invalid JWT
      403:
        description: Admins only
    """
    status = request.args.get("status", "pending")
    if status not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of {', '.join(VALID_STATUSES)}"}), 400

    reports = (
        Report.query.filter_by(status=status)
        .order_by(Report.created_at.asc())
        .all()
    )
    return jsonify([r.to_dict() for r in reports])


@reports_bp.route("/<int:report_id>/status", methods=["PATCH"])
@admin_required
def update_report_status(report_id):
    """
    Admin: approve or reject a report
    ---
    tags:
      - Reports (admin)
    security:
      - Bearer: []
    parameters:
      - name: report_id
        in: path
        type: integer
        required: true
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - status
          properties:
            status:
              type: string
              enum: [pending, approved, rejected]
              example: approved
    responses:
      200:
        description: Status updated
      400:
        description: Invalid status
      401:
        description: Missing or invalid JWT
      403:
        description: Admins only
      404:
        description: Report not found
    """
    data = request.get_json() or {}
    new_status = data.get("status")

    if new_status not in VALID_STATUSES:
        return jsonify({"error": f"status must be one of {', '.join(VALID_STATUSES)}"}), 400

    report = db.get_or_404(Report, report_id)
    report.status = new_status
    db.session.commit()

    return jsonify(report.to_dict())