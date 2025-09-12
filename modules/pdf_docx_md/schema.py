from pydantic import BaseModel

class PdfDocsMdExtractionRequest(BaseModel):
    pdf_file: str