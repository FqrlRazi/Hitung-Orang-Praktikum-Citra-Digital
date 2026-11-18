import cv2
import numpy as np

from app.image_processing import analyze_image


def _person_silhouette(mask: np.ndarray, center_x: int) -> None:
    cv2.circle(mask, (center_x, 27), 12, 255, -1)
    cv2.rectangle(mask, (center_x - 8, 37), (center_x + 8, 50), 255, -1)
    cv2.fillPoly(
        mask,
        [
            np.array(
                [
                    [center_x - 14, 46],
                    [center_x - 25, 53],
                    [center_x - 24, 86],
                    [center_x - 14, 91],
                    [center_x - 13, 119],
                    [center_x + 13, 119],
                    [center_x + 14, 91],
                    [center_x + 24, 86],
                    [center_x + 25, 53],
                    [center_x + 14, 46],
                ],
                dtype=np.int32,
            )
        ],
        255,
    )


def _analyze_mask(foreground: np.ndarray) -> int:
    image = np.full((*foreground.shape, 3), 180, dtype=np.uint8)
    image[foreground != 0] = (35, 35, 35)
    success, encoded = cv2.imencode(".png", image)
    assert success
    return analyze_image(encoded.tobytes(), sensitivity=35).count


def test_counts_separated_silhouettes() -> None:
    foreground = np.zeros((160, 220), dtype=np.uint8)
    _person_silhouette(foreground, 55)
    _person_silhouette(foreground, 160)

    assert _analyze_mask(foreground) == 2


def test_splits_touching_silhouettes() -> None:
    foreground = np.zeros((160, 190), dtype=np.uint8)
    _person_silhouette(foreground, 70)
    _person_silhouette(foreground, 120)

    assert _analyze_mask(foreground) == 2


def test_keeps_single_silhouette_as_one_detection() -> None:
    foreground = np.zeros((160, 130), dtype=np.uint8)
    _person_silhouette(foreground, 65)

    assert _analyze_mask(foreground) == 1
