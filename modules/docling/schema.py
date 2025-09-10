from pydantic import BaseModel
from typing import Optional

class DoclingExtractionRequest(BaseModel):
    pdf_file: str
    do_ocr: Optional[bool] = False
    do_table_structure: Optional[bool] = False
    do_table_structure_cell_matching: Optional[bool] = False