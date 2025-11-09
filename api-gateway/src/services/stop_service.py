from typing import Tuple, Any
from src.utils import http_client

SERVICE_KEY = 'stop_service'


def get_stops() -> Tuple[Any, int]:
    return http_client.get(SERVICE_KEY, 'stops')


def get_stop(stop_id: int) -> Tuple[Any, int]:
    return http_client.get(SERVICE_KEY, f'stops/{stop_id}')


def create_stop(data: dict) -> Tuple[Any, int]:
    return http_client.post(SERVICE_KEY, 'stops', json=data)


def update_stop(stop_id: int, data: dict) -> Tuple[Any, int]:
    return http_client.put(SERVICE_KEY, f'stops/{stop_id}', json=data)


def delete_stop(stop_id: int) -> Tuple[Any, int]:
    return http_client.delete(SERVICE_KEY, f'stops/{stop_id}')