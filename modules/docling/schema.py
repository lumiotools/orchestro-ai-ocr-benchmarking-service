from pydantic import BaseModel
from typing import Optional

class DoclingExtractionRequest(BaseModel):
    pdf_file: str
    do_ocr: Optional[bool] = True
    force_ocr: Optional[bool] = False
    ocr_engine: Optional[str] = "easyocr"
    pdf_backend: Optional[str] = "dlparse_v4"
    table_mode: Optional[str] = "accurate"
    table_cell_matching: Optional[bool] = True
    do_table_structure: Optional[bool] = True
    md_page_break_placeholder: Optional[str] = ""