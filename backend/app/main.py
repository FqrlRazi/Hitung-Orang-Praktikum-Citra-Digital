import base64
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles

from .image_processing import AnalysisResult, analyze_image, generate_report_pdf
from .history_store import (
    HistoryStorageConfigurationError,
    get_previous_record,
    get_record,
    list_records,
    read_record_image,
    save_record,
)


MAX_UPLOAD_BYTES = 10 * 1024 * 1024

app = FastAPI(
    title="Hitung Orang dari Citra",
    description="Demo segmentasi latar terkendali dan analisis kontur.",
    version="1.0.0",
)


@app.exception_handler(HistoryStorageConfigurationError)
async def history_storage_configuration_error(
    request: Request,
    error: HistoryStorageConfigurationError,
) -> JSONResponse:
    return JSONResponse(status_code=503, content={"detail": str(error)})


@app.get("/api/health")
def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/api/analyze")
async def analyze_upload(
    file: UploadFile = File(...),
    sensitivity: int = Form(35, ge=5, le=120),
    min_area_percent: float = Form(0.5, gt=0, le=20),
) -> dict:
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(
            status_code=415,
            detail="Format gambar harus JPG, PNG, atau WebP.",
        )

    image_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Ukuran gambar melebihi batas 10 MB.",
        )

    try:
        result = analyze_image(image_bytes, sensitivity, min_area_percent)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    record = await save_record(file.filename or "gambar-tanpa-nama", result, image_bytes)

    return {
        "count": result.count,
        "detection_method": result.detection_method,
        "segmentation_method": result.segmentation_method,
        "annotated_image": result.annotated_image,
        "mask_image": result.mask_image,
        "face_mask_image": result.face_mask_image,
        "image_width": result.image_width,
        "image_height": result.image_height,
        "background_color": result.background_color,
        "detections": result.detections,
        "contour_detections": result.contour_detections,
        "history_id": record["id"],
    }


@app.post("/api/report/pdf")
async def download_report_pdf(
    file: UploadFile = File(...),
    sensitivity: int = Form(35, ge=5, le=120),
    min_area_percent: float = Form(0.5, gt=0, le=20),
) -> Response:
    if file.content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(
            status_code=415,
            detail="Format gambar harus JPG, PNG, atau WebP.",
        )

    image_bytes = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(image_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=413,
            detail="Ukuran gambar melebihi batas 10 MB.",
        )

    try:
        result = analyze_image(image_bytes, sensitivity, min_area_percent)
        pdf_bytes = generate_report_pdf(result)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    safe_name = Path(file.filename or "laporan-pendeteksian").stem
    safe_name = "".join(
        character if character.isalnum() or character in ("-", "_") else "_"
        for character in safe_name
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="laporan-{safe_name}.pdf"',
        },
    )


@app.get("/api/history")
async def history_list(limit: int = 100) -> dict:
    return {"records": await list_records(limit)}


@app.get("/api/history/{record_id}")
async def history_detail(record_id: str) -> dict:
    record = await get_record(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Riwayat tidak ditemukan.")
    return record


@app.get("/api/history/{record_id}/report/pdf")
async def download_history_report_pdf(record_id: str) -> Response:
    record = await get_record(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Riwayat tidak ditemukan.")

    image_data = {}
    for image_name in ("annotated", "mask", "face_mask"):
        try:
            image_data[image_name] = base64.b64encode(
                await read_record_image(record, image_name)
            ).decode("ascii")
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error

    result = AnalysisResult(
        count=record["count"],
        detection_method=record["detection_method"],
        segmentation_method=record["segmentation_method"],
        annotated_image=image_data["annotated"],
        mask_image=image_data["mask"],
        face_mask_image=image_data["face_mask"],
        image_width=record["image_width"],
        image_height=record["image_height"],
        background_color=record["background_color"],
        detections=record.get("detections", []),
        contour_detections=record.get("contour_detections", []),
    )
    pdf_bytes = generate_report_pdf(
        result,
        history_context={
            "file_name": record.get("file_name", "-"),
            "created_at": record.get("created_at", "-"),
            "previous": await get_previous_record(record_id),
        },
    )
    safe_name = Path(record.get("file_name", "laporan-pendeteksian")).stem
    safe_name = "".join(
        character if character.isalnum() or character in ("-", "_") else "_"
        for character in safe_name
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="laporan-{safe_name}.pdf"',
        },
    )


@app.get("/api/history/{record_id}/image/{image_name}")
async def history_image(record_id: str, image_name: str) -> Response:
    record = await get_record(record_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Riwayat tidak ditemukan.")

    if image_name not in {"original", "annotated", "mask", "face_mask"}:
        raise HTTPException(status_code=404, detail="Gambar tidak ditemukan.")

    try:
        image_bytes = await read_record_image(record, image_name)
    except FileNotFoundError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    return Response(content=image_bytes, media_type="image/png")


app.mount(
    "/",
    StaticFiles(directory="frontend", html=True),
    name="frontend-assets",
)
