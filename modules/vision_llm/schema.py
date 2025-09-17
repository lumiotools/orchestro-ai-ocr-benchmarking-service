from pydantic import BaseModel
from typing import Optional
from fastapi import Form


class VisionLLMExtractionRequest(BaseModel):
    pdf_type: str
    pdf_file: Optional[str] = None
    vllm_base_url: str
    vllm_api_key: str
    vllm_model_id: str
    vllm_prompt: Optional[str] = None

    @classmethod
    def as_form(cls, pdf_type: str = Form(...), pdf_file: Optional[str] = Form(None), vllm_base_url: str = Form(...), vllm_api_key: str = Form(...), vllm_model_id: str = Form(...), vllm_prompt: Optional[str] = Form(None)):
        return cls(pdf_type=pdf_type, pdf_file=pdf_file, vllm_base_url=vllm_base_url, vllm_api_key=vllm_api_key, vllm_model_id=vllm_model_id, vllm_prompt=vllm_prompt)
