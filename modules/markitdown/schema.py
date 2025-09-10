from pydantic import BaseModel

class MarkItDownExtractionRequest(BaseModel):
    pdf_file: str