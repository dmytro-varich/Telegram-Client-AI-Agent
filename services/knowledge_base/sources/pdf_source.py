"""PDF text extraction source for loading document content."""

from typing import Iterable
from pypdf import PdfReader


class PdfTextSource: 
    def __init__(self, file_path: str) -> None:
        self.file_path = file_path
        
    def exists(self) -> bool:
        try:
            with open(self.file_path, 'rb'):
                return True
        except FileNotFoundError:
            return False

    def load(self) -> Iterable[str]:
        reader = PdfReader(self.file_path)
        texts = []
        for page in reader.pages:
            texts.append(page.extract_text())
        return texts