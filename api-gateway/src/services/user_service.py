from typing import Tuple, Any
from src.utils import http_client

SERVICE_KEY = 'user_service'


def get_users() -> Tuple[Any, int]:
    return http_client.get(SERVICE_KEY, 'users')


def get_user(user_id: int) -> Tuple[Any, int]:
    return http_client.get(SERVICE_KEY, f'users/{user_id}')


def create_user(payload: dict) -> Tuple[Any, int]:
    return http_client.post(SERVICE_KEY, 'users', json=payload)


def update_user(user_id: int, payload: dict) -> Tuple[Any, int]:
    return http_client.put(SERVICE_KEY, f'users/{user_id}', json=payload)


def delete_user(user_id: int) -> Tuple[Any, int]:
    return http_client.delete(SERVICE_KEY, f'users/{user_id}')