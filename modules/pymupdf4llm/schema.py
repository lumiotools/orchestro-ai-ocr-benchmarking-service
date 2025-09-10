from pydantic import BaseModel

class PyMuPDF4LLMExtractionRequest(BaseModel):
    pdf_file: str