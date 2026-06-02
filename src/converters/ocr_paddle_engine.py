from pathlib import Path
from statistics import median
from typing import Any

from src.converters.ocr_base import BaseOCREngine

SUPPORTED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "heic", "tiff", "tif", "bmp", "gif"}

_ocr_model: Any | None = None


def _validate_image_path(image_path: Path) -> None:
    suffix = image_path.suffix.lower().lstrip(".")
    if suffix not in SUPPORTED_IMAGE_EXTENSIONS:
        raise ValueError("Unsupported image format for OCR.")
    if not image_path.exists() or not image_path.is_file():
        raise ValueError("Could not read this image. Check that the file exists and try again.")
    try:
        with image_path.open("rb") as file:
            file.read(1)
    except OSError as exc:
        raise ValueError("Could not read this image. Check that the file is readable and try again.") from exc


def _get_ocr_model() -> Any:
    global _ocr_model
    if _ocr_model is None:
        from paddleocr import PaddleOCR

        _ocr_model = PaddleOCR(use_angle_cls=True, lang="en")
    return _ocr_model


def _is_detection(value: Any) -> bool:
    if not isinstance(value, (list, tuple)) or len(value) != 2:
        return False
    bbox, text_result = value[0], value[1]
    return (
        isinstance(bbox, (list, tuple))
        and bbox
        and isinstance(text_result, (list, tuple))
        and len(text_result) >= 1
        and isinstance(text_result[0], str)
    )


def _iter_detections(result: Any) -> list[Any]:
    if result is None:
        return []
    if _is_detection(result):
        return [result]
    if isinstance(result, (list, tuple)):
        detections: list[Any] = []
        for item in result:
            detections.extend(_iter_detections(item))
        return detections
    return []


def _bbox_metrics(bbox: Any) -> tuple[float, float, float, float]:
    points = [(float(point[0]), float(point[1])) for point in bbox if isinstance(point, (list, tuple)) and len(point) >= 2]
    if not points:
        return 0.0, 0.0, 0.0, 0.0
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    top = min(ys)
    left = min(xs)
    height = max(ys) - top
    center_y = top + (height / 2)
    return top, left, height, center_y


def _ordered_text_from_detections(detections: list[Any]) -> str:
    entries: list[dict[str, Any]] = []
    for detection in detections:
        text = str(detection[1][0]).strip()
        if not text:
            continue
        top, left, height, center_y = _bbox_metrics(detection[0])
        entries.append({"text": text, "top": top, "left": left, "height": height, "center_y": center_y})

    if not entries:
        return ""

    heights = [entry["height"] for entry in entries if entry["height"] > 0]
    line_tolerance = max((median(heights) * 0.7) if heights else 10.0, 8.0)
    lines: list[dict[str, Any]] = []

    for entry in sorted(entries, key=lambda item: (item["top"], item["left"])):
        matching_line = None
        for line in lines:
            if abs(entry["center_y"] - line["center_y"]) <= line_tolerance:
                matching_line = line
                break
        if matching_line is None:
            lines.append({"center_y": entry["center_y"], "top": entry["top"], "entries": [entry]})
        else:
            matching_line["entries"].append(entry)
            matching_line["center_y"] = median([item["center_y"] for item in matching_line["entries"]])
            matching_line["top"] = min(item["top"] for item in matching_line["entries"])

    ordered_lines = []
    for line in sorted(lines, key=lambda item: item["top"]):
        line_entries = sorted(line["entries"], key=lambda item: item["left"])
        ordered_lines.append(" ".join(item["text"] for item in line_entries))
    return "\n".join(ordered_lines).strip()


class PaddleOCREngine(BaseOCREngine):
    name = "paddleocr"

    @classmethod
    def is_available(cls) -> bool:
        try:
            import paddleocr  # noqa: F401
        except ImportError:
            return False
        return True

    def extract_text(self, image_path: Path) -> str:
        _validate_image_path(image_path)
        try:
            result = _get_ocr_model().ocr(str(image_path), cls=True)
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("Could not read this image. Check that the file is a valid image and try again.") from exc

        text = _ordered_text_from_detections(_iter_detections(result))
        if not text:
            raise ValueError("No text detected in image.")
        return text
