from flask import Blueprint, request, jsonify
from src.services.route_service import get_routes, create_route, update_route, delete_route, get_route_by_id

route_bp = Blueprint('route', __name__)


@route_bp.route('', methods=['GET'])
def fetch_routes():
    body, status = get_routes()
    return (jsonify(body), status) if isinstance(body, (dict, list)) else (body, status)


@route_bp.route('', methods=['POST'])
def add_route():
    data = request.get_json() or {}
    body, status = create_route(data)
    return (jsonify(body), status) if isinstance(body, (dict, list)) else (body, status)


@route_bp.route('/<int:route_id>', methods=['GET'])
def fetch_route(route_id):
    body, status = get_route_by_id(route_id)
    if status == 200:
        return jsonify(body), 200
    return jsonify(body), status


@route_bp.route('/<int:route_id>', methods=['PUT'])
def modify_route(route_id):
    data = request.get_json() or {}
    body, status = update_route(route_id, data)
    return (jsonify(body), status) if isinstance(body, (dict, list)) else (body, status)


@route_bp.route('/<int:route_id>', methods=['DELETE'])
def remove_route(route_id):
    body, status = delete_route(route_id)
    if status in (200, 204):
        return '', 204
    return jsonify(body), status