import requests
import os
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

DOCLING_URL = "http://34.138.80.251/v1/convert/file"

class DoclingExtractor:
    """Convert PDF bytes to Markdown using Docling.

    Minimal overrides supported:
    - do_ocr
    - table_structure
    - cell_matching (table_structure_options.do_cell_matching)

    Advanced accelerator / lang overrides removed for now to keep interface minimal.
    """

    def __init__(
            self,
            do_ocr: Optional[bool] = True,
            force_ocr: Optional[bool] = False,
            ocr_engine: Optional[str] = "easyocr",
            pdf_backend: Optional[str] = "dlparse_v4",
            table_mode: Optional[str] = "accurate",
            table_cell_matching: Optional[bool] = True,
            do_table_structure: Optional[bool] = True,
            md_page_break_placeholder: Optional[str] = "",
    ):
        """Initialize the extractor and prepare pipeline options.

        Args:
                pdf_pipeline_options: Pre-built PdfPipelineOptions to start from.
                do_ocr: Override for OCR enabling.
                table_structure: Override for table structure extraction.
                cell_matching: Override for cell matching inside table structure options.
        """
        self.api_key = os.environ.get("DOCLING_API_KEY")
        self.docling_url = DOCLING_URL
  
        self.do_ocr = do_ocr
        self.force_ocr = force_ocr
        self.ocr_engine = ocr_engine
        self.pdf_backend = pdf_backend
        self.table_mode = table_mode
        self.table_cell_matching = table_cell_matching
        self.do_table_structure = do_table_structure
        self.md_page_break_placeholder = md_page_break_placeholder

    def extract(
            self,
            pdf_bytes: bytes,
    ) -> str:
        """Extract markdown from PDF bytes using the configured pipeline.

        Raises:
                RuntimeError: on conversion errors.
        """
        
        if not self.api_key:
            raise RuntimeError("DOCLING_API_KEY not configured in environment and not provided to DoclingExtractor()")
        
        files = {"files": ("Contract.pdf", pdf_bytes, "application/pdf")}
        data = self._build_payload()
        headers = {"Authorization": self.api_key}

        response = requests.post(self.docling_url, headers=headers, data=data, files=files)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(f"API Error ({response.status_code}): {response.text}") from e
        
        response_json = response.json()
        markdown_content = response_json.get("document").get("md_content")
        
        return markdown_content
  

    def _build_payload(
            self,
    ) -> dict:
        # Start with provided or default instance
        payload = {
            "do_ocr": self.do_ocr,
            "force_ocr": self.force_ocr,
            "ocr_engine": self.ocr_engine,
            "pdf_backend": self.pdf_backend,
            "table_mode": self.table_mode,
            "do_cell_matching": self.table_cell_matching,
            "do_table_structure": self.do_table_structure,
            "md_page_break_placeholder": self.md_page_break_placeholder,
        }

        return payload
