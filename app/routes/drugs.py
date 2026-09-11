from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.drug import Drug

drugs_bp = Blueprint("drugs", __name__)


@drugs_bp.route("/search", methods=["GET"])
def search_drugs():
    """
    Public search - no login required.
    Query params: ?q=<search term>
    Searches trade_name, active_ingredient, and registration_number.
    """
    query = request.args.get("q", "").strip()

    if not query:
        return jsonify({"error": "Please provide a search term with ?q="}), 400

    search_pattern = f"%{query}%"
    results = Drug.query.filter(
        db.or_(
            Drug.trade_name.ilike(search_pattern),
            Drug.active_ingredient.ilike(search_pattern),
            Drug.registration_number.ilike(search_pattern),
        )
    ).limit(50).all()

    return jsonify({
        "count": len(results),
        "results": [drug.to_dict() for drug in results],
    })


@drugs_bp.route("/verify/<registration_number>", methods=["GET"])
def verify_by_registration(registration_number):
    """
    Exact-match verification by registration number.
    This is the 'is this real?' endpoint.
    """
    drug = Drug.query.filter_by(registration_number=registration_number).first()

    if drug:
        return jsonify({
            "verified": True,
            "drug": drug.to_dict(),
        })

    return jsonify({
        "verified": False,
        "message": "No matching registration found in the PPB register. This doesn't automatically mean it's counterfeit - it may be unregistered or the number may be mistyped. Exercise caution.",
    }), 404


@drugs_bp.route("/<int:drug_id>", methods=["GET"])
def get_drug(drug_id):
    drug = Drug.query.get_or_404(drug_id)
    return jsonify(drug.to_dict())