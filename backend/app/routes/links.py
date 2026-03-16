"""
Link routes — Flask routing only.
No SQL, no business logic here. Delegates entirely to link_service.
"""

import logging
from flask import Blueprint, request, jsonify
from pydantic import ValidationError

from app.schemas.link_schema import SaveLinkRequest, UpdateLinkRequest
from app.services import link_service

logger = logging.getLogger(__name__)
links_bp = Blueprint("links", __name__, url_prefix="/api/links")


def _validation_error_response(e: ValidationError):
    return jsonify({"error": "Validation failed", "details": e.errors()}), 422


@links_bp.post("/")
def save_link():
    """POST /api/links/ — analyze and save a new link."""
    try:
        req = SaveLinkRequest(**request.get_json(force=True) or {})
    except ValidationError as e:
        return _validation_error_response(e)

    link = link_service.save_link(req)
    return jsonify(link.to_dict()), 201


@links_bp.get("/")
def list_links():
    """GET /api/links/?status=pending&category=job — list links with optional filters."""
    status = request.args.get("status")
    category = request.args.get("category")
    links = link_service.list_links(status=status, category=category)
    return jsonify([l.to_dict() for l in links])


@links_bp.get("/<int:link_id>")
def get_link(link_id: int):
    """GET /api/links/<id> — fetch a single link."""
    link = link_service.get_link(link_id)
    if link is None:
        return jsonify({"error": "Link not found"}), 404
    return jsonify(link.to_dict())


@links_bp.patch("/<int:link_id>")
def update_link(link_id: int):
    """PATCH /api/links/<id> — update status, notes, deadline, etc."""
    try:
        req = UpdateLinkRequest(**request.get_json(force=True) or {})
    except ValidationError as e:
        return _validation_error_response(e)

    link = link_service.update_link(link_id, req)
    if link is None:
        return jsonify({"error": "Link not found"}), 404
    return jsonify(link.to_dict())


@links_bp.delete("/<int:link_id>")
def delete_link(link_id: int):
    """DELETE /api/links/<id> — remove a link."""
    deleted = link_service.delete_link(link_id)
    if not deleted:
        return jsonify({"error": "Link not found"}), 404
    return jsonify({"deleted": True}), 200


@links_bp.post("/sync-expired")
def sync_expired():
    """POST /api/links/sync-expired — mark past-deadline links as expired."""
    count = link_service.sync_expired_links()
    return jsonify({"expired_count": count})
