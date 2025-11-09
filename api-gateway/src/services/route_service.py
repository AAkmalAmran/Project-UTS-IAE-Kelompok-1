from typing import Tuple, Any
from src.utils import http_client

SERVICE_KEY = 'route_service'


def get_routes() -> Tuple[Any, int]:
    return http_client.get(SERVICE_KEY, 'routes')


def create_route(data: dict) -> Tuple[Any, int]:
    return http_client.post(SERVICE_KEY, 'routes', json=data)


def update_route(route_id: int, data: dict) -> Tuple[Any, int]:
    return http_client.put(SERVICE_KEY, f'routes/{route_id}', json=data)


def delete_route(route_id: int) -> Tuple[Any, int]:
    return http_client.delete(SERVICE_KEY, f'routes/{route_id}')


def get_route_by_id(route_id: int) -> Tuple[Any, int]:
    return http_client.get(SERVICE_KEY, f'routes/{route_id}')