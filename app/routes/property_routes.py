from flask import Blueprint, request, jsonify, current_app
from app.services.offer_service import OfferService
from app.services.valuation_service import ValuationService
from app.repositories.property_repository import PropertyRepository

property_bp = Blueprint("properties", __name__)

def get_services():
    db = current_app.db
    redis_client = current_app.redis
    offer_svc = OfferService(db, redis_client)
    valuation_svc = ValuationService(db, redis_client)
    property_repo = PropertyRepository(db)
    return offer_svc, valuation_svc, property_repo


@property_bp.route("/", methods=["GET"])
def list_properties():
    _, _, property_repo = get_services()
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 20))
    properties = property_repo.list_properties(page=page, per_page=per_page)
    return jsonify({"properties": properties, "page": page, "per_page": per_page})



@property_bp.route("/<property_id>/offers", methods=["POST"])
def submit_offer(property_id):
    offer_svc, _, _ = get_services()
    data = request.get_json()
    if not data:
        return jsonify({"error": "request body required"}), 400

    buyer_id = data.get("buyer_id")
    amount = data.get("amount")

    if not buyer_id or not amount:
        return jsonify({"error": "buyer_id and amount are required"}), 400

    try:
        offer = offer_svc.submit_offer(
            property_id=property_id,
            buyer_id=buyer_id,
            amount=amount,
        )
        return jsonify(offer), 201
    except ValueError as e:
        return jsonify({"error": str(e)}), 409
    except Exception as e:
        current_app.logger.exception("Unexpected error in submit_offer")
        return jsonify({"error": "internal server error"}), 500


@property_bp.route("/<property_id>/offers", methods=["GET"])
def list_offers(property_id):
    offer_svc, _, _ = get_services()
    offers = offer_svc.get_offers(property_id)
    return jsonify({"offers": offers})

@property_bp.route("/<property_id>/valuation", methods=["GET"])
def get_valuation(property_id):
    _, valuation_svc, _ = get_services()
    result = valuation_svc.get_valuation(property_id)
    return jsonify(result)
