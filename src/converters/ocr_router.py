from src.converters.ocr_base import BaseOCREngine
from src.converters.ocr_paddle_engine import PaddleOCREngine
from src.converters.ocr_vision_engine import VisionOCREngine

SUPPORTED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "heic", "tiff", "tif", "bmp", "gif"}


def list_available_engines() -> list[str]:
    engines = []
    for engine_class in (PaddleOCREngine, VisionOCREngine):
        if engine_class.is_available():
            engines.append(engine_class.name)
    return engines


def get_default_engine() -> BaseOCREngine:
    if PaddleOCREngine.is_available():
        return PaddleOCREngine()
    if VisionOCREngine.is_available():
        return VisionOCREngine()
    raise RuntimeError(
        "No OCR engine is available. Install PaddleOCR or macOS Vision OCR dependencies, then try again."
    )
