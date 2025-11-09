from flask import Blueprint, request, jsonify
from src.services.schedule_service import get_schedules, get_schedule, create_schedule, update_schedule, delete_schedule

schedule_bp = Blueprint('schedule', __name__)


@schedule_bp.route('', methods=['GET'])
def list_schedules():
    body, status = get_schedules()
    return (jsonify(body), status) if isinstance(body, (dict, list)) else (body, status)


@schedule_bp.route('/<int:schedule_id>', methods=['GET'])
def fetch_schedule(schedule_id):
    body, status = get_schedule(schedule_id)
    return (jsonify(body), status) if isinstance(body, (dict, list)) else (body, status)


@schedule_bp.route('', methods=['POST'])
def add_schedule():
    data = request.get_json() or {}
    body, status = create_schedule(data)
    return (jsonify(body), status) if isinstance(body, (dict, list)) else (body, status)


@schedule_bp.route('/<int:schedule_id>', methods=['PUT'])
def modify_schedule(schedule_id):
    data = request.get_json() or {}
    body, status = update_schedule(schedule_id, data)
    return (jsonify(body), status) if isinstance(body, (dict, list)) else (body, status)


@schedule_bp.route('/<int:schedule_id>', methods=['DELETE'])
def remove_schedule(schedule_id):
    body, status = delete_schedule(schedule_id)
    if status in (200, 204):
        return '', 204
    return jsonify(body), status