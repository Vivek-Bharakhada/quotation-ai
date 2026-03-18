import mimetypes
import os
from urllib.parse import quote

import httpx


SUPABASE_URL = str(os.getenv("SUPABASE_URL", "")).strip().rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = str(os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")).strip()
SUPABASE_REQUEST_TIMEOUT = float(os.getenv("SUPABASE_REQUEST_TIMEOUT", "60"))
USE_SUPABASE_STORAGE = str(os.getenv("USE_SUPABASE_STORAGE", "true")).strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}

CATALOGS_BUCKET = str(os.getenv("SUPABASE_CATALOGS_BUCKET", "catalogs")).strip() or "catalogs"
QUOTE_HISTORY_BUCKET = str(os.getenv("SUPABASE_QUOTE_HISTORY_BUCKET", "quote-history")).strip() or "quote-history"
QUOTES_BUCKET = str(os.getenv("SUPABASE_QUOTES_BUCKET", "quotes")).strip() or "quotes"
PRODUCT_IMAGES_BUCKET = str(os.getenv("SUPABASE_PRODUCT_IMAGES_BUCKET", "product-images")).strip() or "product-images"
SYSTEM_BUCKET = str(os.getenv("SUPABASE_SYSTEM_BUCKET", "system")).strip() or "system"


def is_enabled() -> bool:
    has_valid_url = SUPABASE_URL.startswith("http://") or SUPABASE_URL.startswith("https://")
    return USE_SUPABASE_STORAGE and has_valid_url and bool(SUPABASE_SERVICE_ROLE_KEY)


def is_absolute_url(value: str) -> bool:
    raw = str(value or "").strip().lower()
    return raw.startswith("http://") or raw.startswith("https://")


def normalize_object_path(path: str) -> str:
    return str(path or "").replace("\\", "/").strip("/")


def guess_content_type(path: str, fallback: str = "application/octet-stream") -> str:
    guessed, _ = mimetypes.guess_type(str(path or ""))
    return guessed or fallback


def public_url(bucket: str, object_path: str) -> str:
    encoded_path = quote(normalize_object_path(object_path), safe="/-_.~")
    return f"{SUPABASE_URL}/storage/v1/object/public/{bucket}/{encoded_path}"


def _auth_headers(extra=None):
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
    }
    if extra:
        headers.update(extra)
    return headers


def upload_bytes(bucket: str, object_path: str, content: bytes, content_type: str = None) -> str:
    if not is_enabled():
        raise RuntimeError("Supabase storage is not configured")

    path = normalize_object_path(object_path)
    encoded_path = quote(path, safe="/-_.~")
    endpoint = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{encoded_path}"
    headers = _auth_headers(
        {
            "Content-Type": content_type or guess_content_type(path),
            "x-upsert": "true",
        }
    )

    with httpx.Client(timeout=SUPABASE_REQUEST_TIMEOUT) as client:
        response = client.post(endpoint, headers=headers, content=content)

    if response.status_code not in {200, 201}:
        raise RuntimeError(f"Supabase upload failed ({response.status_code}): {response.text}")

    return public_url(bucket, path)


def upload_file(bucket: str, object_path: str, local_path: str, content_type: str = None) -> str:
    with open(local_path, "rb") as handle:
        return upload_bytes(bucket, object_path, handle.read(), content_type or guess_content_type(local_path))


def download_bytes(bucket: str, object_path: str):
    if not is_enabled():
        return None

    path = normalize_object_path(object_path)
    encoded_path = quote(path, safe="/-_.~")
    endpoint = f"{SUPABASE_URL}/storage/v1/object/{bucket}/{encoded_path}"

    with httpx.Client(timeout=SUPABASE_REQUEST_TIMEOUT) as client:
        response = client.get(endpoint, headers=_auth_headers())

    if response.status_code == 404:
        return None
    if not response.is_success:
        raise RuntimeError(f"Supabase download failed ({response.status_code}): {response.text}")

    return response.content


def download_to_path(bucket: str, object_path: str, local_path: str) -> bool:
    content = download_bytes(bucket, object_path)
    if content is None:
        return False

    os.makedirs(os.path.dirname(local_path), exist_ok=True)
    with open(local_path, "wb") as handle:
        handle.write(content)
    return True


def list_objects(bucket: str, prefix: str = ""):
    if not is_enabled():
        return []

    endpoint = f"{SUPABASE_URL}/storage/v1/object/list/{bucket}"
    payload = {
        "prefix": normalize_object_path(prefix),
        "limit": 1000,
        "offset": 0,
        "sortBy": {"column": "name", "order": "asc"},
    }

    with httpx.Client(timeout=SUPABASE_REQUEST_TIMEOUT) as client:
        response = client.post(
            endpoint,
            headers=_auth_headers({"Content-Type": "application/json"}),
            json=payload,
        )

    if not response.is_success:
        raise RuntimeError(f"Supabase list failed ({response.status_code}): {response.text}")

    return response.json() or []


def delete_object(bucket: str, object_path: str) -> bool:
    if not is_enabled():
        return False

    endpoint = f"{SUPABASE_URL}/storage/v1/object/{bucket}"
    payload = {"prefixes": [normalize_object_path(object_path)]}

    with httpx.Client(timeout=SUPABASE_REQUEST_TIMEOUT) as client:
        response = client.request(
            "DELETE",
            endpoint,
            headers=_auth_headers({"Content-Type": "application/json"}),
            json=payload,
        )

    if response.status_code not in {200, 204}:
        raise RuntimeError(f"Supabase delete failed ({response.status_code}): {response.text}")

    return True


def move_object(bucket: str, source_path: str, destination_path: str) -> str:
    if not is_enabled():
        raise RuntimeError("Supabase storage is not configured")

    endpoint = f"{SUPABASE_URL}/storage/v1/object/move"
    payload = {
        "bucketId": bucket,
        "sourceKey": normalize_object_path(source_path),
        "destinationKey": normalize_object_path(destination_path),
    }

    with httpx.Client(timeout=SUPABASE_REQUEST_TIMEOUT) as client:
        response = client.post(
            endpoint,
            headers=_auth_headers({"Content-Type": "application/json"}),
            json=payload,
        )

    if not response.is_success:
        raise RuntimeError(f"Supabase move failed ({response.status_code}): {response.text}")

    return public_url(bucket, destination_path)
