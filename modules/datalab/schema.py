from pydantic import BaseModel
from typing import Optional
from fastapi import Form


class DatalabExtractionRequest(BaseModel):
    pdf_type: str
    pdf_file: Optional[str] = None
    paginated: Optional[bool] = False
    force_ocr: Optional[bool] = False

    @classmethod
    def as_form(
        cls,
        pdf_type: str = Form(...),
        pdf_file: Optional[str] = Form(None),
        paginated: Optional[bool] = Form(False),
        force_ocr: Optional[bool] = Form(False)
    ):
        return cls(pdf_type=pdf_type, pdf_file=pdf_file, paginated=paginated, force_ocr=force_ocr)
