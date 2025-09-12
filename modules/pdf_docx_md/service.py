from pdf2docx import Converter
import docx2md
from markdownify import markdownify
import tempfile
import os

class PdfDocsMdExtractor:
    """Single-class extractor that exposes only .extract(pdf_bytes).

    This keeps the public surface minimal while encapsulating markdown-sanitization logic.
    """
    
    def __init__(self):
        pass

    def extract(self, pdf_bytes: bytes) -> str:
        """
        Extract text from PDF bytes using PdfDocsMdExtractor.
        
        Args:
            pdf_bytes (bytes): The PDF file content in bytes.

        Returns:
            str: The extracted text from the PDF.
        """
        tmp = tempfile.NamedTemporaryFile(suffix=".docx", delete=False)
        tmp_path = tmp.name
        tmp.close()
        
        cv = Converter(stream=pdf_bytes)
        cv.convert(tmp_path)
        cv.close()
        
        semi_html_markdown = docx2md.do_convert(tmp_path, use_md_table=False)
        markdown = markdownify(semi_html_markdown, table_infer_header=True)
        
        os.remove(tmp_path)

        return markdown
