from __future__ import annotations

import base64
import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np
from vercel import blob


HISTORY_DIR = Path(__file__).resolve().parents[2] / "data" / "history"
HISTORY_FILE = HISTORY_DIR / "records.json"
BLOB_RECORDS_PREFIX = "history/records/"
BLOB_IMAGES_PREFIX = "history/images/"


class HistoryStorageConfigurationError(RuntimeError):
    pass


def _uses_blob_storage() -> bool:
    return bool(os.getenv("VERCEL")) or bool(
        os.getenv("BLOB_READ_WRITE_TOKEN")
        or os.getenv("VERCEL_BLOB_READ_WRITE_TOKEN")
        or (
            os.getenv("BLOB_STORE_ID")
            and (os.getenv("VERCEL_OIDC_TOKEN") or os.getenv("VERCEL"))
        )
    )


def _require_blob_credentials() -> None:
    has_read_write_token = bool(
        os.getenv("BLOB_READ_WRITE_TOKEN") or os.getenv("VERCEL_BLOB_READ_WRITE_TOKEN")
    )
    has_oidc_credentials = bool(
        os.getenv("BLOB_STORE_ID")
        and (os.getenv("VERCEL_OIDC_TOKEN") or os.getenv("VERCEL"))
    )
    if not (has_read_write_token or has_oidc_credentials):
        raise HistoryStorageConfigurationError(
            "Hubungkan Vercel Blob ke project ini agar upload dapat disimpan. "
            "Buat private Blob store lalu hubungkan ke project Vercel."
        )


def _decode_image(value: str) -> np.ndarray | None:
    encoded = base64.b64decode(value)
    source = np.frombuffer(encoded, dtype=np.uint8)
    return cv2.imdecode(source, cv2.IMREAD_UNCHANGED)


def _save_image(record_id: str, name: str, value: str) -> str:
    image = _decode_image(value)
    if image is None:
        raise ValueError("Gagal menyimpan citra hasil.")
    path = HISTORY_DIR / f"{record_id}_{name}.png"
    if not cv2.imwrite(str(path), image):
        raise ValueError("Gagal menyimpan citra hasil.")
    return path.name


def _read_records() -> list[dict[str, Any]]:
    if not HISTORY_FILE.is_file():
        return []
    try:
        return json.loads(HISTORY_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return []


def _write_records(records: list[dict[str, Any]]) -> None:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(
        json.dumps(records, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


async def _save_blob(pathname: str, content: bytes, content_type: str) -> str:
    await blob.put_blob(
        pathname,
        content,
        access="private",
        content_type=content_type,
    )
    return pathname


async def save_record(
    file_name: str,
    result: Any,
    source_bytes: bytes,
) -> dict[str, Any]:
    record_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]

    source = cv2.imdecode(np.frombuffer(source_bytes, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if _uses_blob_storage():
        _require_blob_credentials()
        files = {}
        if source is not None:
            success, encoded_source = cv2.imencode(".png", source)
            if not success:
                raise ValueError("Gagal menyimpan citra asli.")
            files["original"] = await _save_blob(
                f"{BLOB_IMAGES_PREFIX}{record_id}/original.png",
                encoded_source.tobytes(),
                "image/png",
            )
        else:
            files["original"] = None

        for image_name in ("annotated", "mask", "face_mask"):
            image_data = getattr(result, f"{image_name}_image")
            files[image_name] = await _save_blob(
                f"{BLOB_IMAGES_PREFIX}{record_id}/{image_name}.png",
                base64.b64decode(image_data),
                "image/png",
            )
    else:
        HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        source_path = HISTORY_DIR / f"{record_id}_original.png"
        if source is not None:
            cv2.imwrite(str(source_path), source)
        files = {
            "original": source_path.name if source is not None else None,
            "annotated": _save_image(record_id, "annotated", result.annotated_image),
            "mask": _save_image(record_id, "mask", result.mask_image),
            "face_mask": _save_image(record_id, "face_mask", result.face_mask_image),
        }

    record = {
        "id": record_id,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "file_name": file_name,
        "count": result.count,
        "detection_method": result.detection_method,
        "segmentation_method": result.segmentation_method,
        "image_width": result.image_width,
        "image_height": result.image_height,
        "background_color": result.background_color,
        "detections": result.detections,
        "contour_detections": result.contour_detections,
        "files": files,
    }

    if _uses_blob_storage():
        await _save_blob(
            f"{BLOB_RECORDS_PREFIX}{record_id}.json",
            json.dumps(record, ensure_ascii=False).encode("utf-8"),
            "application/json",
        )
    else:
        records = _read_records()
        records.insert(0, record)
        _write_records(records)
    return record


async def list_records(limit: int = 100) -> list[dict[str, Any]]:
    if not _uses_blob_storage():
        return _read_records()[:limit]

    _require_blob_credentials()
    records = _read_records()
    async for item in blob.query_blobs(prefix=BLOB_RECORDS_PREFIX):
        stored = await blob.get_blob(item.pathname, access="private")
        record = json.loads(stored.body)
        if isinstance(record, dict):
            records.append(record)
    records.sort(key=lambda record: record.get("created_at", ""), reverse=True)
    unique_records = {record["id"]: record for record in records}
    return list(unique_records.values())[:limit]


async def get_record(record_id: str) -> dict[str, Any] | None:
    local_record = next(
        (record for record in _read_records() if record["id"] == record_id),
        None,
    )
    if local_record is not None or not _uses_blob_storage():
        return local_record

    _require_blob_credentials()
    try:
        stored = await blob.get_blob(
            f"{BLOB_RECORDS_PREFIX}{record_id}.json",
            access="private",
        )
    except blob.BlobNotFoundError:
        return None
    return json.loads(stored.body)


async def get_previous_record(record_id: str) -> dict[str, Any] | None:
    records = await list_records(limit=100_000)
    for index, record in enumerate(records):
        if record["id"] == record_id:
            return next(
                (
                    previous
                    for previous in records[index + 1 :]
                    if previous.get("detection_method") == record.get("detection_method")
                ),
                None,
            )
    return None


async def read_record_image(record: dict[str, Any], image_name: str) -> bytes:
    file_name = record.get("files", {}).get(image_name)
    if not file_name:
        raise FileNotFoundError("Gambar tidak tersedia.")

    if file_name.startswith(BLOB_IMAGES_PREFIX):
        record_prefix = f"{BLOB_IMAGES_PREFIX}{record['id']}/"
        if not file_name.startswith(record_prefix):
            raise FileNotFoundError("Referensi gambar tidak valid.")
        _require_blob_credentials()
        try:
            stored = await blob.get_blob(file_name, access="private")
        except blob.BlobNotFoundError:
            raise FileNotFoundError("Gambar tidak ditemukan.") from None
        return stored.body

    image_path = (HISTORY_DIR / file_name).resolve()
    if HISTORY_DIR.resolve() not in image_path.parents:
        raise FileNotFoundError("Referensi gambar tidak valid.")
    try:
        return image_path.read_bytes()
    except OSError as error:
        raise FileNotFoundError("Gambar tidak ditemukan.") from error
