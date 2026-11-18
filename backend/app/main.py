from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles

from .image_processing import analyze_image, generate_report_pdf


MAX_UPLOAD_BYTES = 10 * 1024 * 1024

app = FastAPI(
    title="Hitung Orang dari Citra",
    description="Demo segmentasi latar terkendali dan analisis kontur.",
    version="1.0.0",
)


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

    return {
        "count": result.count,
        "detection_method": result.detection_method,
        "segmentation_method": result.segmentation_method,
        "annotated_image": result.annotated_image,
        "mask_image": result.mask_image,
        "image_width": result.image_width,
        "image_height": result.image_height,
        "background_color": result.background_color,
        "detections": result.detections,
        "contour_detections": result.contour_detections,
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


app.mount(
    "/",
    StaticFiles(directory="frontend", html=True),
    name="frontend-assets",
)
