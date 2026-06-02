from pathlib import Path
from typing import Any

from src.converters.ocr_base import BaseOCREngine
from src.converters.ocr_paddle_engine import _validate_image_path


class VisionOCREngine(BaseOCREngine):
    name = "vision"

    @classmethod
    def is_available(cls) -> bool:
        try:
            from ocrmac import ocrmac  # noqa: F401
        except ImportError:
            return False
        return True

    def extract_text(self, image_path: Path) -> str:
        _validate_image_path(image_path)
        try:
            from ocrmac import ocrmac

            annotations = ocrmac.OCR(str(image_path), language_preference=["en-US"]).recognize()
        except ValueError:
            raise
        except Exception as exc:
            raise ValueError("Could not read this image. Check that the file is a valid image and try again.") from exc

        text = _text_from_annotations(annotations)
        if not text:
            raise ValueError("No text detected in image.")
        return text


def _text_from_annotations(annotations: Any) -> str:
    lines = []
    for annotation in annotations or []:
        if not isinstance(annotation, (list, tuple)) or not annotation:
            continue
        text = str(annotation[0]).strip()
        if text:
            lines.append(text)
    return "\n".join(lines).strip()
