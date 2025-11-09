from flask import Blueprint, request, jsonify
from src.services.bus_service import get_buses, get_bus, create_bus, update_bus, delete_bus

bus_bp = Blueprint('bus', __name__)


@bus_bp.route('', methods=['GET'])
def list_buses():
    body, status = get_buses()
    return (jsonify(body), status) if isinstance(body, (dict, list)) else (body, status)


@bus_bp.route('/<int:bus_id>', methods=['GET'])
def fetch_bus(bus_id):
    body, status = get_bus(bus_id)
    return (jsonify(body), status) if isinstance(body, (dict, list)) else (body, status)


@bus_bp.route('', methods=['POST'])
def add_bus():
    data = request.get_json() or {}
    body, status = create_bus(data)
    return (jsonify(body), status) if isinstance(body, (dict, list)) else (body, status)


@bus_bp.route('/<int:bus_id>', methods=['PUT'])
def modify_bus(bus_id):
    data = request.get_json() or {}
    body, status = update_bus(bus_id, data)
    return (jsonify(body), status) if isinstance(body, (dict, list)) else (body, status)


@bus_bp.route('/<int:bus_id>', methods=['DELETE'])
def remove_bus(bus_id):
    body, status = delete_bus(bus_id)
    if status in (200, 204):
        return '', 204
    return jsonify(body), status