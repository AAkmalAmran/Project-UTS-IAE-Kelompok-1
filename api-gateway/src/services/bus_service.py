from typing import Tuple, Any
from src.utils import http_client

SERVICE_KEY = 'bus_service'


def get_buses() -> Tuple[Any, int]:
    return http_client.get(SERVICE_KEY, 'buses')


def get_bus(bus_id: int) -> Tuple[Any, int]:
    return http_client.get(SERVICE_KEY, f'buses/{bus_id}')


def create_bus(data: dict) -> Tuple[Any, int]:
    return http_client.post(SERVICE_KEY, 'buses', json=data)


def update_bus(bus_id: int, data: dict) -> Tuple[Any, int]:
    return http_client.put(SERVICE_KEY, f'buses/{bus_id}', json=data)


def delete_bus(bus_id: int) -> Tuple[Any, int]:
    return http_client.delete(SERVICE_KEY, f'buses/{bus_id}')