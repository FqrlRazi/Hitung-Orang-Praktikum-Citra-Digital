from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import cv2
import numpy as np


HISTORY_DIR = Path(__file__).resolve().parents[2] / "data" / "history"
HISTORY_FILE = HISTORY_DIR / "records.json"


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


def save_record(
    file_name: str,
    result: Any,
    source_bytes: bytes,
) -> dict[str, Any]:
    HISTORY_DIR.mkdir(parents=True, exist_ok=True)
    record_id = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]

    source_path = HISTORY_DIR / f"{record_id}_original.png"
    source = cv2.imdecode(np.frombuffer(source_bytes, dtype=np.uint8), cv2.IMREAD_UNCHANGED)
    if source is not None:
        cv2.imwrite(str(source_path), source)

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
        "files": {
            "original": source_path.name if source is not None else None,
            "annotated": _save_image(record_id, "annotated", result.annotated_image),
            "mask": _save_image(record_id, "mask", result.mask_image),
            "face_mask": _save_image(record_id, "face_mask", result.face_mask_image),
        },
    }

    records = _read_records()
    records.insert(0, record)
    _write_records(records)
    return record


def list_records(limit: int = 100) -> list[dict[str, Any]]:
    return _read_records()[:limit]


def get_record(record_id: str) -> dict[str, Any] | None:
    return next(
        (record for record in _read_records() if record["id"] == record_id),
        None,
    )
