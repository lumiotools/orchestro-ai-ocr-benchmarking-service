from markitdown import MarkItDown
from io import BytesIO

class MarkItDownExtractor:
    """Single-class extractor that exposes only .extract(pdf_bytes).

    This keeps the public surface minimal while encapsulating markdown-sanitization logic.
    """
    
    def __init__(self):
        pass

    def extract(self, pdf_bytes: bytes) -> str:
        """
        Extract text from PDF bytes using MarkItDown.
        
        Args:
            pdf_bytes (bytes): The PDF file content in bytes.

        Returns:
            str: The extracted text from the PDF.
        """
        markitdown = MarkItDown()
        
        extracted_markdown = markitdown.convert(BytesIO(pdf_bytes)).markdown

        return extracted_markdown
