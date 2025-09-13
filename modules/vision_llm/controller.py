from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse
from time import time
import asyncio

from constants.option_types import OPTION_TYPES
from common.contract_files import list_available_contracts, read_contract_file_bytes, read_contract_markdown
from common.confidence_llm import LLMConfidenceCalculator
from common.reports import Reports
from .schema import VisionLLMExtractionRequest
from .service import VisionLLMExtractor

router = APIRouter(prefix="/vision_llm")

@router.get("/options")
async def get_options():
    # list_available_contracts touches filesystem -- run in threadpool
    choices = await asyncio.to_thread(list_available_contracts)
    options = {
        "pdf_file": {
            "type": OPTION_TYPES.SELECT,
            "choices": choices,
        },
        "vllm_base_url": {
            "type": OPTION_TYPES.STRING,
            "default": "https://openrouter.ai/api/v1"
        },
        "vllm_api_key": {
            "type": OPTION_TYPES.STRING,
        },
        "vllm_model_id": {
            "type": OPTION_TYPES.STRING,
        },
        "vllm_prompt": {
            "type": OPTION_TYPES.LONG_STRING,
            "default": "Extract the text from the above document as if you were reading it naturally. Return the tables in html format. If there is an image in the document and image caption is not present, add a small description of the image inside the <img></img> tag; otherwise, add the image caption inside <img></img>. Watermarks should be wrapped in brackets. Ex: <watermark>OFFICIAL COPY</watermark>. Page numbers should be wrapped in brackets. Do not include any additional explaination or information. Extract only what's visible in the document.",
        }
    }
    return JSONResponse(content={"success": True, "options": options}, status_code=200)


@router.post("/extract")
async def extract_data(body: VisionLLMExtractionRequest):
    # validate and read file in threadpool
    available = await asyncio.to_thread(list_available_contracts)
    if body.pdf_file not in available:
        return JSONResponse(content={"success": False, "error": "Invalid pdf_file option"}, status_code=400)

    pdf_bytes = await asyncio.to_thread(read_contract_file_bytes, body.pdf_file)

    started_at = int(time())

    # extractor may be blocking; run in threadpool
    extracted_markdown = await asyncio.to_thread(VisionLLMExtractor(
        vllm_base_url=body.vllm_base_url,
        vllm_api_key=body.vllm_api_key,
        vllm_model_id=body.vllm_model_id,
        vllm_prompt=body.vllm_prompt
    ).extract, pdf_bytes)

    completed_at = int(time())

    extraction_time = completed_at - started_at

    expected_markdown = await asyncio.to_thread(read_contract_markdown, body.pdf_file)
    score = await asyncio.to_thread(LLMConfidenceCalculator().calculate_confidence_score, expected_markdown, extracted_markdown)

    body.vllm_api_key = "****"  # mask api key in report
    
    report_id = Reports().save_report({
        "inputs": {
            "provider": "VisionLLM",
            **body.dict()
        },
        "metadata": {
            "started_at": started_at,
            "completed_at": completed_at,
            "extraction_time": extraction_time,
            "score": score
        },
        "markdown": extracted_markdown
    })

    return JSONResponse(content={
        "success": True,
        "report_id": report_id
    }, status_code=200)
