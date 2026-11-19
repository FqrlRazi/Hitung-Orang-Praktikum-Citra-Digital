from __future__ import annotations

import base64
from io import BytesIO
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np
from reportlab.lib import colors  # pyright: ignore[reportMissingModuleSource]
from reportlab.lib.enums import TA_LEFT  # pyright: ignore[reportMissingModuleSource]
from reportlab.lib.pagesizes import A4  # pyright: ignore[reportMissingModuleSource]
from reportlab.lib.styles import (  # pyright: ignore[reportMissingModuleSource]
    getSampleStyleSheet,
    ParagraphStyle,
)
from reportlab.lib.units import mm  # pyright: ignore[reportMissingModuleSource]
from reportlab.platypus import (  # pyright: ignore[reportMissingModuleSource]
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


MAX_IMAGE_PIXELS = 25_000_000
FACE_MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "models"
    / "face_detection_yunet_2023mar.onnx"
)


@dataclass(frozen=True)
class AnalysisResult:
    count: int
    detection_method: str
    segmentation_method: str
    annotated_image: str
    mask_image: str
    face_mask_image: str
    image_width: int
    image_height: int
    background_color: list[int]
    detections: list[dict[str, int | float | str]]
    contour_detections: list[dict[str, int | float | str]]


def _encode_image(image: np.ndarray) -> str:
    success, encoded = cv2.imencode(".png", image)
    if not success:
        raise RuntimeError("Gagal mengubah hasil pemrosesan menjadi gambar.")
    return base64.b64encode(encoded.tobytes()).decode("ascii")


def generate_report_pdf(result: AnalysisResult) -> bytes:
    pdf_buffer = BytesIO()
    document = SimpleDocTemplate(
        pdf_buffer,
        pagesize=A4,
        rightMargin=15 * mm,
        leftMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="Laporan Hasil Pendeteksian Sistem",
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="ReportTitle",
            parent=styles["Title"],
            alignment=TA_LEFT,
            textColor=colors.HexColor("#1d5948"),
            fontSize=18,
            leading=22,
            spaceAfter=8,
        )
    )
    styles.add(
        ParagraphStyle(
            name="Section",
            parent=styles["Heading2"],
            textColor=colors.HexColor("#1d5948"),
            fontSize=12,
            spaceBefore=5,
            spaceAfter=5,
        )
    )

    story = [
        Paragraph("Laporan Hasil Pendeteksian Sistem", styles["ReportTitle"]),
        Paragraph("Pengolahan Citra Digital - Hitung Orang", styles["Normal"]),
        Spacer(1, 5 * mm),
        Table(
            [
                ["Jumlah hasil", str(result.count)],
                ["Metode deteksi", "YuNet Face Detection" if result.detection_method == "wajah" else "Analisis kontur eksternal"],
                ["Metode segmentasi", result.segmentation_method],
                ["Ukuran citra", f"{result.image_width} x {result.image_height} piksel"],
                ["Warna latar perkiraan", f"RGB ({', '.join(str(value) for value in result.background_color)})"],
            ],
            colWidths=[48 * mm, 125 * mm],
            style=TableStyle([
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f6f7f2")),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#17221f")),
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#d7ddd8")),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]),
        ),
        Spacer(1, 7 * mm),
        Paragraph("1. Citra Hasil Deteksi", styles["Section"]),
    ]

    annotated = Image(
        BytesIO(base64.b64decode(result.annotated_image)),
        width=170 * mm,
        height=105 * mm,
        kind="proportional",
    )
    story.extend([
        annotated,
        Spacer(1, 5 * mm),
        PageBreak(),
        Paragraph("2. Mask Latar", styles["Section"]),
    ])

    mask = Image(
        BytesIO(base64.b64decode(result.mask_image)),
        width=170 * mm,
        height=105 * mm,
        kind="proportional",
    )
    story.extend([
        mask,
        Spacer(1, 5 * mm),
        Paragraph("Putih = foreground; hitam = latar.", styles["Normal"]),
        Spacer(1, 5 * mm),
        PageBreak(),
        Paragraph("2.1. Mask Kotak Wajah", styles["Section"]),
    ])

    face_mask = Image(
        BytesIO(base64.b64decode(result.face_mask_image)),
        width=170 * mm,
        height=105 * mm,
        kind="proportional",
    )
    story.extend([
        face_mask,
        Spacer(1, 5 * mm),
        Paragraph(
            "Putih = kotak hasil deteksi wajah YuNet; hitam = area di luar wajah.",
            styles["Normal"],
        ),
        Spacer(1, 5 * mm),
        Paragraph("3. Tabel Analisis Kontur", styles["Section"]),
    ])

    reported = result.detections if result.detection_method == "wajah" else result.contour_detections
    table_data = [["No.", "Bentuk", "Ukuran (px)", "Rasio aspek", "Skor analisis", "Sumber"]]
    for index, detection in enumerate(reported, start=1):
        table_data.append([
            str(index),
            str(detection.get("shape", "Tidak diketahui")),
            f"{detection.get('width', 0)} x {detection.get('height', 0)}",
            f"{float(detection.get('aspect_ratio', 0.0)): .2f}",
            (
                f"{float(detection.get('confidence', detection.get('shape_confidence', 0.0))):.1f}%"
            ),
            str(detection.get("shape_source", "Analisis kontur")),
        ])
    if len(table_data) == 1:
        table_data.append(["-", "Tidak ada kontur lolos", "-", "-", "-"])

    table = Table(
        table_data,
        repeatRows=1,
        colWidths=[10 * mm, 35 * mm, 30 * mm, 25 * mm, 73 * mm],
        style=TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d5948")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("GRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#bcc6c1")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f7f2")]),
            ("LEFTPADDING", (0, 0), (-1, -1), 4),
            ("RIGHTPADDING", (0, 0), (-1, -1), 4),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ]),
    )
    story.append(table)

    document.build(story)
    return pdf_buffer.getvalue()


def _border_pixels(image: np.ndarray) -> np.ndarray:
    height, width = image.shape[:2]
    band = max(1, min(height, width) // 20)
    return np.concatenate(
        (
            image[:band, :, :].reshape(-1, 3),
            image[-band:, :, :].reshape(-1, 3),
            image[:, :band, :].reshape(-1, 3),
            image[:, -band:, :].reshape(-1, 3),
        ),
        axis=0,
    )


def _detect_faces(image: np.ndarray) -> list[tuple[int, int, int, int, float]]:
    height, width = image.shape[:2]
    scale = min(1.0, 1200 / max(height, width))
    if scale < 1:
        detection_image = cv2.resize(
            image,
            (round(width * scale), round(height * scale)),
            interpolation=cv2.INTER_AREA,
        )
    else:
        detection_image = image

    if not FACE_MODEL_PATH.is_file():
        raise RuntimeError(f"Model deteksi wajah tidak ditemukan: {FACE_MODEL_PATH}")

    detector = cv2.FaceDetectorYN.create(
        str(FACE_MODEL_PATH),
        "",
        (detection_image.shape[1], detection_image.shape[0]),
        0.7,
        0.3,
        5000,
    )
    _, faces = detector.detect(detection_image)
    if faces is None:
        return []
    detections = []
    for face in faces:
        x, y, face_width, face_height = face[:4]
        confidence = float(face[14]) if face.size > 14 else 0.0
        detections.append(
            (
                round(x / scale),
                round(y / scale),
                round(face_width / scale),
                round(face_height / scale),
                round(confidence * 100.0, 1),
            )
        )
    return detections


def _split_touching_components(mask: np.ndarray, min_area: float) -> np.ndarray:
    """Conservatively watershed-split wide components with distinct interior peaks."""
    component_count, component_labels, stats, _ = cv2.connectedComponentsWithStats(
        mask, connectivity=8
    )
    result = mask.copy()
    for label in range(1, component_count):
        x, y, width, height, area = stats[label]
        # A single person's vertically elongated silhouette is unlikely to be a
        # shoulder-connected pair. This guard also avoids splitting most limbs.
        if area < min_area * 2 or width < height * 0.65 or width < 16:
            continue

        component = (component_labels[y : y + height, x : x + width] == label).astype(
            np.uint8
        )
        distance = cv2.distanceTransform(component, cv2.DIST_L2, 5)
        peak_height = float(distance.max())
        if peak_height < 3:
            continue

        # Find prominent local maxima. A relative threshold suppresses head/limb
        # bumps on one silhouette while retaining two similarly sized torsos.
        peak_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
        local_maxima = (distance >= cv2.dilate(distance, peak_kernel)) & (
            distance >= max(3.0, peak_height * 0.65)
        )
        peak_count, peak_labels, _, peak_centroids = cv2.connectedComponentsWithStats(
            local_maxima.astype(np.uint8), connectivity=8
        )
        peaks: list[tuple[float, float, float, int]] = []
        for peak_label in range(1, peak_count):
            px, py = peak_centroids[peak_label]
            peak_value = float(distance[peak_labels == peak_label].max())
            if peak_value >= peak_height * 0.55:
                peaks.append((float(px), float(py), peak_value, peak_label))
        peaks.sort(key=lambda peak: peak[2], reverse=True)

        selected: list[tuple[float, float, float, int]] = []
        for peak in peaks:
            if all(
                np.hypot(peak[0] - other[0], peak[1] - other[1])
                >= max(8.0, min(peak[2], other[2]) * 1.2)
                for other in selected
            ):
                selected.append(peak)
        if len(selected) < 2:
            continue
        selected = selected[:5]

        # Require a meaningful distance-map saddle between each pair; nearby
        # lobes with almost no neck are more likely one irregular silhouette.
        has_clear_saddles = True
        for first_index, first in enumerate(selected):
            for second in selected[first_index + 1 :]:
                steps = max(
                    2,
                    int(np.hypot(second[0] - first[0], second[1] - first[1])),
                )
                xs = np.rint(np.linspace(first[0], second[0], steps)).astype(int)
                ys = np.rint(np.linspace(first[1], second[1], steps)).astype(int)
                saddle = float(distance[ys, xs].min())
                if saddle > min(first[2], second[2]) * 0.85:
                    has_clear_saddles = False
                    break
            if not has_clear_saddles:
                break
        if not has_clear_saddles:
            continue

        markers = np.ones(component.shape, dtype=np.int32)
        markers[component != 0] = 0
        yy, xx = np.ogrid[:height, :width]
        for marker_id, (px, py, peak_value, _) in enumerate(selected, start=2):
            seed_radius = max(3.0, peak_value * 0.35)
            core = (
                ((xx - px) ** 2 + (yy - py) ** 2 <= seed_radius**2)
                & (component != 0)
            )
            markers[core] = marker_id

        distance_u8 = np.clip(distance / peak_height * 255, 0, 255).astype(np.uint8)
        watershed_image = cv2.cvtColor(255 - distance_u8, cv2.COLOR_GRAY2BGR)
        labels = cv2.watershed(watershed_image, markers)
        basin_areas = [
            int(np.count_nonzero((labels == marker_id) & (component != 0)))
            for marker_id in range(2, len(selected) + 2)
        ]
        # Reject fragile splits that would turn one blob into tiny fragments.
        if any(basin_area < max(min_area, area * 0.18) for basin_area in basin_areas):
            continue

        # OpenCV's watershed boundary is one pixel wide; thicken it so external
        # contour extraction (8-connected) sees two independent regions.
        boundary = (labels == -1).astype(np.uint8)
        basin_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        for first_id in range(2, len(selected) + 2):
            first_basin = (labels == first_id).astype(np.uint8)
            for second_id in range(first_id + 1, len(selected) + 2):
                second_basin = (labels == second_id).astype(np.uint8)
                boundary |= (
                    (first_basin != 0)
                    & (cv2.dilate(second_basin, basin_kernel) != 0)
                ).astype(np.uint8)
                boundary |= (
                    (second_basin != 0)
                    & (cv2.dilate(first_basin, basin_kernel) != 0)
                ).astype(np.uint8)
        boundary = cv2.dilate(boundary, basin_kernel)
        component_result = result[y : y + height, x : x + width]
        component_result[component != 0] = 0
        for marker_id in range(2, len(selected) + 2):
            component_result[(labels == marker_id) & (component != 0)] = 255
        component_result[boundary != 0] = 0

    return result


def _analyze_face_contour(
    image: np.ndarray,
    x: int,
    y: int,
    face_width: int,
    face_height: int,
) -> tuple[str, float, float, float]:
    height, width = image.shape[:2]
    padding_x = max(2, round(face_width * 0.10))
    padding_y = max(2, round(face_height * 0.10))
    left = max(0, x - padding_x)
    top = max(0, y - padding_y)
    right = min(width, x + face_width + padding_x)
    bottom = min(height, y + face_height + padding_y)
    crop = image[top:bottom, left:right]
    if crop.size == 0:
        return "Tidak terdeteksi", 0.0, 0.0, 0.0

    crop_height, crop_width = crop.shape[:2]
    yy, xx = np.ogrid[:crop_height, :crop_width]
    ellipse_x = float(face_width / 2 + (x - left))
    ellipse_y = float(face_height / 2 + (y - top))
    ellipse_mask = (
        ((xx - ellipse_x) / max(face_width * 0.58, 1)) ** 2
        + ((yy - ellipse_y) / max(face_height * 0.58, 1)) ** 2
        <= 1
    ).astype(np.uint8)

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
    ycrcb = cv2.cvtColor(crop, cv2.COLOR_BGR2YCrCb)
    hsv_skin = cv2.inRange(hsv, (0, 20, 50), (25, 180, 255))
    ycrcb_skin = cv2.inRange(ycrcb, (0, 135, 85), (255, 180, 135))
    skin_mask = cv2.bitwise_and(hsv_skin, ycrcb_skin)
    skin_mask = cv2.bitwise_and(skin_mask, skin_mask, mask=ellipse_mask)

    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_CLOSE, kernel)
    skin_mask = cv2.morphologyEx(skin_mask, cv2.MORPH_OPEN, kernel)

    contours, _ = cv2.findContours(
        skin_mask,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    if not contours:
        return "Tidak terdeteksi", 0.0, 0.0, 0.0

    face_contour = max(contours, key=cv2.contourArea)
    contour_area = cv2.contourArea(face_contour)
    minimum_area = face_width * face_height * 0.08
    if contour_area < minimum_area or len(face_contour) < 5:
        return "Tidak terdeteksi", 0.0, 0.0, 0.0

    ellipse = cv2.fitEllipse(face_contour)
    ellipse_width, ellipse_height = ellipse[1]
    perimeter = cv2.arcLength(face_contour, True)
    circularity = (
        float(4 * np.pi * contour_area / (perimeter * perimeter))
        if perimeter > 0
        else 0.0
    )
    face_ratio = float(ellipse_width / ellipse_height) if ellipse_height else 0.0
    perimeter = cv2.arcLength(face_contour, True)
    polygon = cv2.approxPolyDP(face_contour, 0.035 * perimeter, True)
    vertices = len(polygon)
    hull = cv2.convexHull(face_contour, returnPoints=False)
    defects = []
    if len(hull) >= 3:
        try:
            contour_defects = cv2.convexityDefects(face_contour, hull)
            if contour_defects is not None:
                defects = [
                    float(item[0][3]) / 256.0
                    for item in contour_defects
                    if float(item[0][3]) / 256.0 >= 4.0
                ]
        except cv2.error:
            defects = []

    bx, by, bw, bh = cv2.boundingRect(face_contour)
    aspect = float(bw / bh) if bh else 0.0
    solidity = float(contour_area / cv2.contourArea(cv2.convexHull(face_contour))) if cv2.contourArea(cv2.convexHull(face_contour)) else 1.0

    if vertices == 3:
        shape = "Segitiga"
    elif defects and solidity < 0.93:
        defect_depth = max(defects)
        if aspect >= 0.72 and aspect <= 1.35 and defect_depth >= bh * 0.10:
            shape = "Hati"
        elif vertices == 4:
            shape = "Kotak" if 0.78 <= aspect <= 1.25 else "Persegi panjang"
        elif vertices == 5:
            shape = "Segi lima"
        elif vertices == 6:
            shape = "Segi enam"
        elif circularity >= 0.82:
            shape = "Bulat"
        elif 0.78 <= aspect <= 1.20:
            shape = "Oval"
        elif aspect < 0.78:
            shape = "Lonjong"
        else:
            shape = "Mendatar"
    elif vertices == 4:
        shape = "Kotak" if 0.78 <= aspect <= 1.25 else "Persegi panjang"
    elif vertices == 5:
        shape = "Segi lima"
    elif vertices == 6:
        shape = "Segi enam"
    elif circularity >= 0.82:
        shape = "Bulat"
    elif 0.78 <= aspect <= 1.20:
        shape = "Oval"
    elif aspect < 0.78:
        shape = "Lonjong"
    else:
        shape = "Mendatar"

    shape_confidence = max(
        0.0,
        min(
            100.0,
            (circularity * 55.0)
            + (solidity * 30.0)
            + (15.0 if 0.78 <= aspect <= 1.20 else 0.0),
        ),
    )
    return shape, circularity, face_ratio, round(shape_confidence, 1)


def _classify_face_box(width: int, height: int) -> str:
    if width <= 0 or height <= 0:
        return "Tidak diketahui"

    ratio = float(height / width)
    if 0.88 <= ratio <= 1.12:
        return "Bulat"
    if 0.78 <= ratio < 0.88:
        return "Mendatar"
    if 1.12 < ratio <= 1.28:
        return "Kotak"
    if 1.28 < ratio <= 1.50:
        return "Oval"
    if ratio > 1.50:
        return "Lonjong"
    if ratio < 0.78:
        return "Persegi panjang"
    return "Tidak diketahui"


def _analyze_contour_shape(contour: np.ndarray) -> tuple[str, float, float, float]:
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    if perimeter <= 0:
        return "Tidak diketahui", 0.0, 0.0, 0.0

    circularity = float(4 * np.pi * area / (perimeter * perimeter))
    x, y, width, height = cv2.boundingRect(contour)
    aspect_ratio = float(width / height) if height else 0.0
    polygon = cv2.approxPolyDP(contour, 0.04 * perimeter, True)
    vertices = len(polygon)
    rectangle_area = float(width * height)
    contour_occupancy = float(area / rectangle_area) if rectangle_area else 0.0

    ellipse_roundness = 0.0
    if len(contour) >= 5:
        ellipse = cv2.fitEllipse(contour)
        ellipse_width, ellipse_height = ellipse[1]
        ellipse_area = np.pi * ellipse_width * ellipse_height / 4
        ellipse_roundness = float(area / ellipse_area) if ellipse_area else 0.0

    if vertices == 3 and contour_occupancy >= 0.25:
        shape = "Segitiga"
    elif vertices == 4 and contour_occupancy >= 0.55:
        width_height_ratio = max(width, height) / max(min(width, height), 1)
        shape = "Kotak" if width_height_ratio < 1.25 else "Persegi panjang"
    elif vertices == 5 and contour_occupancy >= 0.55:
        shape = "Segi lima"
    elif vertices == 6 and contour_occupancy >= 0.55:
        shape = "Segi enam"
    elif circularity >= 0.82 and ellipse_roundness >= 0.72:
        shape = "Bulat"
    elif 0.78 <= aspect_ratio <= 1.28:
        shape = "Lonjong"
    elif aspect_ratio > 1.35:
        shape = "Mendatar"
    else:
        shape = "Tegak"
    shape_confidence = max(
        0.0,
        min(
            100.0,
            (ellipse_roundness * 35.0)
            + (contour_occupancy * 35.0)
            + (circularity * 30.0),
        ),
    )
    return shape, circularity, aspect_ratio, round(shape_confidence, 1)


def analyze_image(
    image_bytes: bytes,
    sensitivity: int = 35,
    min_area_percent: float = 0.5,
) -> AnalysisResult:
    encoded = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError("File tidak dapat dibaca sebagai gambar.")

    height, width = image.shape[:2]
    if width * height > MAX_IMAGE_PIXELS:
        raise ValueError("Resolusi gambar terlalu besar (maksimal 25 megapiksel).")

    border = _border_pixels(image)
    background_color = np.median(border, axis=0).astype(np.uint8)
    background_patch = np.empty_like(image)
    background_patch[:] = background_color

    image_lab = cv2.cvtColor(image, cv2.COLOR_BGR2LAB).astype(np.int16)
    background_lab = cv2.cvtColor(background_patch, cv2.COLOR_BGR2LAB).astype(
        np.int16
    )
    color_difference = image_lab.astype(np.int32) - background_lab.astype(np.int32)
    color_distance = np.sqrt(np.sum(color_difference**2, axis=2))
    color_distance = np.clip(color_distance, 0, 255).astype(np.uint8)
    _, mask = cv2.threshold(
        color_distance,
        sensitivity,
        255,
        cv2.THRESH_BINARY,
    )

    mask = cv2.GaussianBlur(mask, (5, 5), 0)
    _, mask = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    opening_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
    closing_kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, opening_kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, closing_kernel)

    min_area = width * height * min_area_percent / 100
    mask = _split_touching_components(mask, min_area)
    contours, _ = cv2.findContours(
        mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    detections: list[dict[str, int | float]] = []
    for contour in contours:
        area = cv2.contourArea(contour)
        if area < min_area:
            continue
        x, y, box_width, box_height = cv2.boundingRect(contour)
        shape, circularity, aspect_ratio, shape_confidence = _analyze_contour_shape(contour)
        detections.append(
            {
                "x": x,
                "y": y,
                "width": box_width,
                "height": box_height,
                "area": round(area, 1),
                "shape": shape,
                "circularity": round(circularity, 3),
                "aspect_ratio": round(aspect_ratio, 3),
                "shape_confidence": shape_confidence,
                "shape_source": "Kontur segmentasi latar",
            }
        )

    detections.sort(key=lambda detection: int(detection["x"]))
    contour_detections = [detection.copy() for detection in detections]

    detection_method = "kontur"
    faces = _detect_faces(image)
    face_mask = np.zeros((height, width), dtype=np.uint8)
    for x, y, face_width, face_height, confidence in faces:
        cv2.rectangle(
            face_mask,
            (x, y),
            (x + face_width, y + face_height),
            255,
            thickness=-1,
        )

    if faces and len(faces) >= 2:
        detections = []
        for x, y, face_width, face_height, confidence in faces:
            shape, circularity, face_ratio, shape_confidence = _analyze_face_contour(
                image, x, y, face_width, face_height
            )
            detections.append(
                {
                    "x": x,
                    "y": y,
                    "width": face_width,
                    "height": face_height,
                    "area": float(face_width * face_height),
                    "shape": shape,
                    "circularity": round(circularity, 3),
                    "aspect_ratio": round(face_ratio, 3),
                    "confidence": confidence,
                    "shape_confidence": shape_confidence,
                    "shape_source": "Kontur piksel area wajah",
                }
            )
        detection_method = "wajah"

    detections.sort(key=lambda detection: int(detection["x"]))
    annotated = image.copy()
    for index, detection in enumerate(detections, start=1):
        x = int(detection["x"])
        y = int(detection["y"])
        box_width = int(detection["width"])
        box_height = int(detection["height"])
        cv2.rectangle(
            annotated,
            (x, y),
            (x + box_width, y + box_height),
            (55, 205, 145),
            max(2, width // 500),
        )
        cv2.putText(
            annotated,
            str(index),
            (x, max(24, y - 8)),
            cv2.FONT_HERSHEY_SIMPLEX,
            max(0.6, width / 1200),
            (55, 205, 145),
            max(2, width // 500),
            cv2.LINE_AA,
        )

    return AnalysisResult(
        count=len(detections),
        detection_method=detection_method,
        segmentation_method="Threshold perbedaan warna CIELAB + Gaussian blur + opening/closing",
        annotated_image=_encode_image(annotated),
        mask_image=_encode_image(mask),
        face_mask_image=_encode_image(face_mask),
        image_width=width,
        image_height=height,
        background_color=[int(channel) for channel in background_color[::-1]],
        detections=detections,
        contour_detections=contour_detections,
    )
