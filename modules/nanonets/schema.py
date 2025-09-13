from pydantic import BaseModel
from typing import Optional

class NanonetsExtractionRequest(BaseModel):
    pdf_file: str
    prompt: Optional[str] = None