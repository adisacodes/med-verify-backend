from flask import Blueprint, request, jsonify
from app.extensions import db
from app.models.drug import Drug

drugs_bp = Blueprint("drugs", __name__)


@drugs_bp.route("/search", methods=["GET"])
def search_drugs():
    """
    Search registered drugs
    ---
    tags:
      - Drugs
    parameters:
      - name: q
        in: query
        type: string
        required: true
        description: Search term (matches trade name, active ingredient, or registration number)
    responses:
      200:
        description: List of matching drugs
      400:
        description: Missing search term
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


@drugs_bp.route("/verify", methods=["GET"])
def verify_by_registration():
    """
    Verify a drug by registration number
    ---
    tags:
      - Drugs
    parameters:
      - name: registration_number
        in: query
        type: string
        required: true
        description: The exact PPB registration number to check (e.g. H2015/00123/001)
    responses:
      200:
        description: Match found - drug is registered
      400:
        description: Missing registration number
      404:
        description: No matching registration found
    """
    registration_number = request.args.get("registration_number", "").strip()

    if not registration_number:
        return jsonify({"error": "Please provide a registration_number query parameter"}), 400

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
    """
    Get a single drug by internal ID
    ---
    tags:
      - Drugs
    parameters:
      - name: drug_id
        in: path
        type: integer
        required: true
        description: The internal database ID of the drug
    responses:
      200:
        description: Drug details
      404:
        description: Drug not found
    """
    drug = Drug.query.get_or_404(drug_id)
    return jsonify(drug.to_dict())