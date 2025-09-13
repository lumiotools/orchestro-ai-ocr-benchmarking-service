from pydantic import BaseModel
from typing import Optional

class VisionLLMExtractionRequest(BaseModel):
    pdf_file: str
    vllm_base_url: str
    vllm_api_key: str
    vllm_model_id: str
    vllm_prompt: Optional[str] = None