from pydantic import BaseModel
from typing import Optional

class DatalabExtractionRequest(BaseModel):
    pdf_file: str
    paginated: Optional[bool] = False
    force_ocr: Optional[bool] = False