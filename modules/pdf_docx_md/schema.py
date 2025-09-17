from pydantic import BaseModel
from typing import Optional
from fastapi import Form


class PdfDocsMdExtractionRequest(BaseModel):
    pdf_type: str
    pdf_file: Optional[str] = None

    @classmethod
    def as_form(cls, pdf_type: str = Form(...), pdf_file: Optional[str] = Form(None)):
        return cls(pdf_type=pdf_type, pdf_file=pdf_file)
