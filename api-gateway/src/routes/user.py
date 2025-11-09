from flask import Blueprint, request, jsonify, current_app
from src.services.user_service import get_user, create_user, update_user, delete_user

user_bp = Blueprint('user', __name__)


@user_bp.route('', methods=['GET'])
def get_user_route_root():
    # list users
    from src.services.user_service import get_users
    body, status = get_users()
    return (jsonify(body), status) if isinstance(body, (dict, list)) else (body, status)


@user_bp.route('/<int:user_id>', methods=['GET'])
def get_user_route(user_id):
    body, status = get_user(user_id)
    if status == 200:
        return jsonify(body), 200
    if status == 404:
        return jsonify({'message': 'User not found'}), 404
    return jsonify(body), status


@user_bp.route('', methods=['POST'])
def create_user_route():
    data = request.get_json() or {}
    body, status = create_user(data)
    return (jsonify(body), status) if isinstance(body, (dict, list)) else (body, status)


@user_bp.route('/<int:user_id>', methods=['PUT'])
def update_user_route(user_id):
    data = request.get_json() or {}
    body, status = update_user(user_id, data)
    if status == 200:
        return jsonify(body), 200
    if status == 404:
        return jsonify({'message': 'User not found'}), 404
    return jsonify(body), status


@user_bp.route('/<int:user_id>', methods=['DELETE'])
def delete_user_route(user_id):
    body, status = delete_user(user_id)
    if status in (200, 204):
        return '', 204
    if status == 404:
        return jsonify({'message': 'User not found'}), 404
    return jsonify(body), status