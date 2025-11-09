import requests
from requests.adapters import HTTPAdapter, Retry
from flask import current_app
from urllib.parse import urljoin


def _session_with_retries(retries=2, backoff_factor=0.3, status_forcelist=(500, 502, 504)):
    session = requests.Session()
    retry = Retry(total=retries, backoff_factor=backoff_factor,
                  status_forcelist=status_forcelist,
                  allowed_methods=frozenset(['GET', 'POST', 'PUT', 'DELETE', 'PATCH']))
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session


def _get_base_url(service_key: str):
    # service_key expected like 'user_service' matching Config.SERVICE_URLS keys
    service_urls = current_app.config.get('SERVICE_URLS') or {}
    return service_urls.get(service_key)


def build_service_url(service_key: str, endpoint: str):
    base = _get_base_url(service_key)
    if not base:
        raise RuntimeError(f"Unknown service key: {service_key}")
    # ensure endpoint does not start with /
    endpoint = endpoint.lstrip('/')
    return urljoin(base.rstrip('/') + '/', endpoint)


def request(method: str, service_key: str, endpoint: str, **kwargs):
    url = build_service_url(service_key, endpoint)
    sess = _session_with_retries()
    timeout = kwargs.pop('timeout', 5)
    try:
        resp = sess.request(method, url, timeout=timeout, **kwargs)
        # try to return JSON when possible, otherwise text
        try:
            body = resp.json()
        except ValueError:
            body = resp.text
        return body, resp.status_code
    except requests.RequestException as e:
        # propagate a standardized error
        raise


def get(service_key: str, endpoint: str, params=None, **kwargs):
    return request('GET', service_key, endpoint, params=params, **kwargs)


def post(service_key: str, endpoint: str, json=None, **kwargs):
    return request('POST', service_key, endpoint, json=json, **kwargs)


def put(service_key: str, endpoint: str, json=None, **kwargs):
    return request('PUT', service_key, endpoint, json=json, **kwargs)


def delete(service_key: str, endpoint: str, **kwargs):
    return request('DELETE', service_key, endpoint, **kwargs)