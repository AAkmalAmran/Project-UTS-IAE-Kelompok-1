from typing import Tuple, Any
from src.utils import http_client

SERVICE_KEY = 'schedule_service'


def get_schedules() -> Tuple[Any, int]:
    return http_client.get(SERVICE_KEY, 'schedules')


def create_schedule(data: dict) -> Tuple[Any, int]:
    return http_client.post(SERVICE_KEY, 'schedules', json=data)


def get_schedule(schedule_id: int) -> Tuple[Any, int]:
    return http_client.get(SERVICE_KEY, f'schedules/{schedule_id}')


def update_schedule(schedule_id: int, data: dict) -> Tuple[Any, int]:
    return http_client.put(SERVICE_KEY, f'schedules/{schedule_id}', json=data)


def delete_schedule(schedule_id: int) -> Tuple[Any, int]:
    return http_client.delete(SERVICE_KEY, f'schedules/{schedule_id}')