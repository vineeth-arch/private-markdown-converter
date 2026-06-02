from abc import ABC, abstractmethod
from pathlib import Path


class BaseOCREngine(ABC):
    name: str

    @classmethod
    @abstractmethod
    def is_available(cls) -> bool:
        """Return True when the OCR engine can be imported."""

    @abstractmethod
    def extract_text(self, image_path: Path) -> str:
        """Extract text from an image path."""
