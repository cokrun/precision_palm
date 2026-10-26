"""SAM 2 segmentation previews refined and serialized with OpenCV."""

import base64
from collections.abc import Mapping, Sequence
from functools import lru_cache
import os
from pathlib import Path
import threading
from typing import Any

import cv2
import numpy as np

_MAX_IMAGE_PIXELS = 20_000_000
_MAX_PROCESSING_DIMENSION = 1600
_MAX_ENTITIES = 16
_MAX_CONTOUR_POINTS = 96
_MAX_REPLAY_CONTOURS = 12
_SAM_MODEL_LOCK = threading.Lock()


@lru_cache(maxsize=1)
def _load_sam_model(model_path: str) -> Any:
    from ultralytics import SAM

    return SAM(model_path)


def build_opencv_box_contour_preview(
    image_bytes: bytes,
    entities: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Extract lightweight pixel contours for Gemini bounding boxes using pure OpenCV."""
    if not image_bytes:
        return {"status": "unavailable", "reason": "image_decode_failed"}

    encoded = np.frombuffer(image_bytes, dtype=np.uint8)
    try:
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    except cv2.error:
        return {"status": "unavailable", "reason": "image_decode_failed"}
    if image is None:
        return {"status": "unavailable", "reason": "image_decode_failed"}

    original_height, original_width = image.shape[:2]
    if original_width * original_height > _MAX_IMAGE_PIXELS:
        return {"status": "unavailable", "reason": "image_too_large"}

    valid_entities: list[tuple[int, Mapping[str, Any], list[float]]] = []
    for entity_index, entity in enumerate(entities[:_MAX_ENTITIES]):
        box = entity.get("box_2d")
        if not isinstance(box, Sequence) or isinstance(box, (str, bytes)) or len(box) != 4:
            continue
        try:
            top, left, bottom, right = (float(value) for value in box)
        except (TypeError, ValueError):
            continue
        if not all(np.isfinite(value) for value in (top, left, bottom, right)):
            continue
        if not (0 <= top < bottom <= 1000 and 0 <= left < right <= 1000):
            continue
        valid_entities.append((entity_index, entity, [left, top, right, bottom]))

    if not valid_entities:
        return {
            "status": "ready",
            "method": "opencv_box_contour",
            "width": original_width,
            "height": original_height,
            "coordinate_space": "original_image_pixels",
            "verification": "opencv_edge_segmentation",
            "contours": [],
        }

    scale = min(1.0, _MAX_PROCESSING_DIMENSION / max(original_width, original_height))
    if scale < 1.0:
        image = cv2.resize(
            image,
            (max(1, round(original_width * scale)), max(1, round(original_height * scale))),
            interpolation=cv2.INTER_AREA,
        )

    height, width = image.shape[:2]
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    edge_neighborhood = cv2.dilate(edges, np.ones((3, 3), dtype=np.uint8))

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    # Broad vegetation / palm canopy mask in HSV
    veg_mask = cv2.inRange(
        hsv,
        np.array([15, 25, 25], dtype=np.uint8),
        np.array([95, 255, 255], dtype=np.uint8),
    )
    veg_mask = cv2.morphologyEx(
        veg_mask,
        cv2.MORPH_CLOSE,
        cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
    )

    suggestions: list[dict[str, Any]] = []
    inverse_scale = 1.0 / scale

    for entity_index, entity, (left, top, right, bottom) in valid_entities:
        x0 = max(0, int(left * width / 1000))
        y0 = max(0, int(top * height / 1000))
        x1 = min(width, int(np.ceil(right * width / 1000)))
        y1 = min(height, int(np.ceil(bottom * height / 1000)))
        if x1 - x0 < 4 or y1 - y0 < 4:
            continue

        roi_area = (x1 - x0) * (y1 - y0)
        roi_veg = veg_mask[y0:y1, x0:x1]
        roi_edges = edges[y0:y1, x0:x1]

        # Combine vegetation mask with edge boundaries for palm canopy / crop features
        combined_roi = cv2.bitwise_or(roi_veg, roi_edges)
        combined_roi = cv2.morphologyEx(
            combined_roi,
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        )

        contours, _ = cv2.findContours(
            combined_roi.copy(),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )

        min_area = max(16.0, roi_area * 0.05)
        candidates = [c for c in contours if cv2.contourArea(c) >= min_area]

        if candidates:
            contour = max(candidates, key=cv2.contourArea)
            perimeter = cv2.arcLength(contour, True)
            polygon = cv2.approxPolyDP(contour, max(1.5, perimeter * 0.01), True)
            points = polygon.reshape(-1, 2)
        else:
            # Fallback to smooth rounded box if texture has low contrast
            pad_x = max(2, int((x1 - x0) * 0.08))
            pad_y = max(2, int((y1 - y0) * 0.08))
            points = np.array([
                [pad_x, pad_y],
                [(x1 - x0) - pad_x, pad_y],
                [(x1 - x0) - pad_x, (y1 - y0) - pad_y],
                [pad_x, (y1 - y0) - pad_y],
            ], dtype=np.int32)

        if len(points) > _MAX_CONTOUR_POINTS:
            indices = np.linspace(0, len(points) - 1, _MAX_CONTOUR_POINTS, dtype=np.int32)
            points = points[indices]

        boundary = np.zeros((y1 - y0, x1 - x0), dtype=np.uint8)
        cv2.drawContours(boundary, [points.reshape(-1, 1, 2)], -1, 1, thickness=1)
        boundary_pixels = boundary.astype(bool)
        edge_support = (
            float(np.mean(edge_neighborhood[y0:y1, x0:x1][boundary_pixels] > 0))
            if np.any(boundary_pixels)
            else 0.5
        )

        suggestions.append({
            "entity_index": entity_index,
            "label": str(
                entity.get("label_name")
                or entity.get("label")
                or entity.get("cluster")
                or "Detected object"
            )[:120],
            "cluster": str(entity.get("cluster") or "unknown")[:64],
            "points": [
                [
                    round((float(point[0]) + x0) * inverse_scale, 1),
                    round((float(point[1]) + y0) * inverse_scale, 1),
                ]
                for point in points
            ],
            "mask_area_fraction": round(float(cv2.contourArea(points)) / max(1.0, roi_area), 4),
            "edge_support": round(edge_support, 3),
        })

    return {
        "status": "ready",
        "method": "opencv_box_contour",
        "width": original_width,
        "height": original_height,
        "coordinate_space": "original_image_pixels",
        "verification": "opencv_edge_segmentation",
        "contours": suggestions,
    }


def build_sam2_contour_preview(
    image_bytes: bytes,
    entities: Sequence[Mapping[str, Any]],
    model_path: str | None = None,
) -> dict[str, Any]:
    """Use SAM 2 box prompts to suggest object masks and pixel contours."""
    if not image_bytes:
        return {"status": "unavailable", "reason": "image_decode_failed"}

    encoded = np.frombuffer(image_bytes, dtype=np.uint8)
    try:
        image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)
    except cv2.error:
        return {"status": "unavailable", "reason": "image_decode_failed"}
    if image is None:
        return {"status": "unavailable", "reason": "image_decode_failed"}

    original_height, original_width = image.shape[:2]
    if original_width * original_height > _MAX_IMAGE_PIXELS:
        return {"status": "unavailable", "reason": "image_too_large"}

    valid_entities: list[tuple[int, Mapping[str, Any], list[float]]] = []
    for entity_index, entity in enumerate(entities[:_MAX_ENTITIES]):
        box = entity.get("box_2d")
        if not isinstance(box, Sequence) or isinstance(box, (str, bytes)) or len(box) != 4:
            continue
        try:
            top, left, bottom, right = (float(value) for value in box)
        except (TypeError, ValueError):
            continue
        if not all(np.isfinite(value) for value in (top, left, bottom, right)):
            continue
        if not (0 <= top < bottom <= 1000 and 0 <= left < right <= 1000):
            continue
        valid_entities.append((entity_index, entity, [left, top, right, bottom]))

    if not valid_entities:
        return {
            "status": "ready",
            "method": "sam2_box_prompt_opencv_contour",
            "model": Path(model_path or os.environ.get("SPATIAL_SAM2_MODEL", "sam2.1_b.pt")).name,
            "width": original_width,
            "height": original_height,
            "coordinate_space": "original_image_pixels",
            "verification": "unverified_model_segmentation",
            "contours": [],
        }


    scale = min(1.0, _MAX_PROCESSING_DIMENSION / max(original_width, original_height))
    if scale < 1.0:
        image = cv2.resize(
            image,
            (max(1, round(original_width * scale)), max(1, round(original_height * scale))),
            interpolation=cv2.INTER_AREA,
        )

    height, width = image.shape[:2]
    prompts = [
        [
            left * width / 1000,
            top * height / 1000,
            right * width / 1000,
            bottom * height / 1000,
        ]
        for _, _, (left, top, right, bottom) in valid_entities
    ]
    selected_model_path = model_path or os.environ.get("SPATIAL_SAM2_MODEL", "sam2.1_b.pt")

    try:
        model = _load_sam_model(selected_model_path)
        with _SAM_MODEL_LOCK:
            predictions = model.predict(
                source=image,
                bboxes=prompts,
                verbose=False,
            )
    except ImportError:
        return {"status": "unavailable", "reason": "ultralytics_not_installed"}
    except FileNotFoundError:
        return {"status": "unavailable", "reason": "sam2_checkpoint_missing"}
    except Exception:
        return {"status": "unavailable", "reason": "sam2_inference_failed"}

    if not predictions or predictions[0].masks is None:
        return {
            "status": "ready",
            "method": "sam2_box_prompt_opencv_contour",
            "model": Path(selected_model_path).name,
            "width": original_width,
            "height": original_height,
            "coordinate_space": "original_image_pixels",
            "verification": "unverified_model_segmentation",
            "contours": [],
        }

    masks = predictions[0].masks.data
    if hasattr(masks, "detach"):
        masks = masks.detach().cpu().numpy()
    masks = np.asarray(masks)
    if masks.ndim == 2:
        masks = masks[np.newaxis, ...]

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(cv2.GaussianBlur(gray, (5, 5), 0), 60, 160)
    edge_neighborhood = cv2.dilate(edges, np.ones((3, 3), dtype=np.uint8))
    suggestions: list[dict[str, Any]] = []

    for mask_index, mask in enumerate(masks[: len(valid_entities)]):
        entity_index, _, (left, top, right, bottom) = valid_entities[mask_index]
        binary_mask = (mask > 0).astype(np.uint8)
        if binary_mask.shape != (height, width):
            binary_mask = cv2.resize(
                binary_mask,
                (width, height),
                interpolation=cv2.INTER_NEAREST,
            )

        x0 = max(0, int(left * width / 1000))
        y0 = max(0, int(top * height / 1000))
        x1 = min(width, int(np.ceil(right * width / 1000)))
        y1 = min(height, int(np.ceil(bottom * height / 1000)))
        if x1 - x0 < 3 or y1 - y0 < 3:
            continue

        roi_mask = binary_mask[y0:y1, x0:x1]
        roi_area = roi_mask.shape[0] * roi_mask.shape[1]
        mask_fraction = float(np.count_nonzero(roi_mask) / roi_area)
        if mask_fraction < 0.005 or mask_fraction > 0.98:
            continue

        cleaned_mask = cv2.morphologyEx(
            roi_mask,
            cv2.MORPH_CLOSE,
            cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5)),
        )
        contours, _ = cv2.findContours(
            cleaned_mask.copy(),
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE,
        )
        min_area = max(8.0, roi_area * 0.002)
        candidates = [
            contour
            for contour in contours
            if cv2.contourArea(contour) >= min_area
        ]
        if not candidates:
            continue

        contour = max(candidates, key=cv2.contourArea)
        perimeter = cv2.arcLength(contour, True)
        if perimeter <= 0:
            continue
        polygon = cv2.approxPolyDP(contour, max(1.0, perimeter * 0.003), True)
        points = polygon.reshape(-1, 2)
        if len(points) < 3:
            continue
        if len(points) > _MAX_CONTOUR_POINTS:
            indices = np.linspace(
                0,
                len(points) - 1,
                _MAX_CONTOUR_POINTS,
                dtype=np.int32,
            )
            points = points[indices]

        boundary = np.zeros_like(roi_mask)
        cv2.drawContours(boundary, [contour], -1, 1, thickness=1)
        boundary_pixels = boundary.astype(bool)
        edge_support = (
            float(np.mean(edge_neighborhood[y0:y1, x0:x1][boundary_pixels] > 0))
            if np.any(boundary_pixels)
            else 0.0
        )
        inverse_scale = 1.0 / scale
        suggestions.append(
            {
                "entity_index": entity_index,
                "label": str(
                    entity.get("label_name")
                    or entity.get("label")
                    or entity.get("cluster")
                    or "Detected object"
                )[:120],
                "cluster": str(entity.get("cluster") or "unknown")[:64],
                "points": [
                    [
                        round((float(point[0]) + x0) * inverse_scale, 1),
                        round((float(point[1]) + y0) * inverse_scale, 1),
                    ]
                    for point in points
                ],
                "mask_area_fraction": round(mask_fraction, 4),
                "edge_support": round(edge_support, 3),
            }
        )

    return {
        "status": "ready",
        "method": "sam2_box_prompt_opencv_contour",
        "model": Path(selected_model_path).name,
        "width": original_width,
        "height": original_height,
        "coordinate_space": "original_image_pixels",
        "verification": "unverified_model_segmentation",
        "contours": suggestions,
    }


def build_opencv_static_replay_preview(
    image_bytes: bytes,
    replay_frames: int = 30,
) -> dict[str, Any]:
    if not image_bytes:
        return {"status": "unavailable", "reason": "image_decode_failed"}
    if not isinstance(replay_frames, int) or not 1 <= replay_frames <= 120:
        return {"status": "unavailable", "reason": "invalid_replay_frame_count"}

    try:
        image = cv2.imdecode(np.frombuffer(image_bytes, dtype=np.uint8), cv2.IMREAD_COLOR)
    except cv2.error:
        return {"status": "unavailable", "reason": "image_decode_failed"}
    if image is None:
        return {"status": "unavailable", "reason": "image_decode_failed"}

    original_height, original_width = image.shape[:2]
    if original_width * original_height > _MAX_IMAGE_PIXELS:
        return {"status": "unavailable", "reason": "image_too_large"}

    scale = min(1.0, _MAX_PROCESSING_DIMENSION / max(original_width, original_height))
    if scale < 1.0:
        image = cv2.resize(
            image,
            (round(original_width * scale), round(original_height * scale)),
            interpolation=cv2.INTER_AREA,
        )

    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    instant_mask = cv2.inRange(
        hsv,
        np.array([25, 40, 40], dtype=np.uint8),
        np.array([85, 255, 255], dtype=np.uint8),
    )
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    instant_mask = cv2.morphologyEx(instant_mask, cv2.MORPH_CLOSE, kernel)

    master_canvas = None
    first_locked_frame = None
    for frame_index in range(1, replay_frames + 1):
        mask_float = instant_mask.astype(np.float32)
        master_canvas = mask_float if master_canvas is None else 0.82 * master_canvas + 0.18 * mask_float
        locked_mask = (master_canvas >= 130).astype(np.uint8) * 255
        if first_locked_frame is None and cv2.countNonZero(locked_mask):
            first_locked_frame = frame_index

    contours, _ = cv2.findContours(
        locked_mask.copy(),
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE,
    )
    serialized_contours = []
    for contour in sorted(contours, key=cv2.contourArea, reverse=True):
        area = float(cv2.contourArea(contour))
        if area <= 1200:
            continue
        perimeter = cv2.arcLength(contour, True)
        epsilon = max(1.0, perimeter * 0.002)
        polygon = cv2.approxPolyDP(contour, epsilon, True)
        while len(polygon) > _MAX_CONTOUR_POINTS:
            epsilon *= 1.5
            polygon = cv2.approxPolyDP(contour, epsilon, True)
        points = polygon.reshape(-1, 2)
        if len(points) < 3:
            continue
        x, y, width, height = cv2.boundingRect(contour)
        serialized_contours.append({
            "points": [[int(point[0]), int(point[1])] for point in points],
            "area_px": round(area, 1),
            "bbox_xywh": [int(x), int(y), int(width), int(height)],
        })
        if len(serialized_contours) >= _MAX_REPLAY_CONTOURS:
            break

    overlay = np.zeros((*locked_mask.shape, 4), dtype=np.uint8)
    overlay[locked_mask > 0] = (238, 211, 34, 28)
    encoded_overlay, png_bytes = cv2.imencode(".png", overlay)
    if not encoded_overlay:
        return {"status": "unavailable", "reason": "mask_overlay_encode_failed"}

    return {
        "status": "ready",
        "method": "opencv_hsv_ema_static_replay",
        "verification": "diagnostic_static_replay_not_streaming",
        "width": int(image.shape[1]),
        "height": int(image.shape[0]),
        "source_width": int(original_width),
        "source_height": int(original_height),
        "replay_frames": replay_frames,
        "first_locked_frame": first_locked_frame,
        "mask_coverage_percent": round(cv2.countNonZero(locked_mask) * 100 / locked_mask.size, 2),
        "mask_overlay_base64": base64.b64encode(png_bytes).decode("ascii"),
        "contours": serialized_contours,
    }
