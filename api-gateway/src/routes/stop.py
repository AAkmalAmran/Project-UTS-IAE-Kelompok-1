from flask import Blueprint, request, jsonify
from src.services.stop_service import get_stops, create_stop, update_stop, delete_stop, get_stop

stop_bp = Blueprint('stop', __name__)


@stop_bp.route('', methods=['GET'])
def fetch_stops():
    body, status = get_stops()
    return (jsonify(body), status) if isinstance(body, (dict, list)) else (body, status)


@stop_bp.route('', methods=['POST'])
def add_stop():
    data = request.get_json() or {}
    body, status = create_stop(data)
    return (jsonify(body), status) if isinstance(body, (dict, list)) else (body, status)


@stop_bp.route('/<int:stop_id>', methods=['GET'])
def fetch_stop(stop_id):
    body, status = get_stop(stop_id)
    return (jsonify(body), status) if isinstance(body, (dict, list)) else (body, status)


@stop_bp.route('/<int:stop_id>', methods=['PUT'])
def modify_stop(stop_id):
    data = request.get_json() or {}
    body, status = update_stop(stop_id, data)
    return (jsonify(body), status) if isinstance(body, (dict, list)) else (body, status)


@stop_bp.route('/<int:stop_id>', methods=['DELETE'])
def remove_stop(stop_id):
    body, status = delete_stop(stop_id)
    if status in (200, 204):
        return '', 204
    return jsonify(body), status