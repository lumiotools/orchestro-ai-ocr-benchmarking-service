from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse
from time import time

from constants.option_types import OPTION_TYPES
from common.contract_files import list_available_contracts
from .schema import PyMuPDF4LLMExtractionRequest
from .service import PyMuPDF4LLMExtractor

router = APIRouter(prefix="/pymupdf4llm")

@router.get("/options")
async def get_options():
    options = {
        "pdf_file": {
            "type": OPTION_TYPES.SELECT,
            "choices": list_available_contracts(),
        }
    }
    return JSONResponse(content={"success": True, "options": options}, status_code=200)


@router.post("/extract")
async def extract_data(body: PyMuPDF4LLMExtractionRequest):
    if(body.pdf_file not in list_available_contracts()):
        return JSONResponse(content={"success": False, "error": "Invalid pdf_file option"}, status_code=400)

    pdf_bytes = open(f"contracts/{body.pdf_file}", "rb").read()
    
    started_at = int(time())

    extracted_markdown = PyMuPDF4LLMExtractor().extract(pdf_bytes)

    completed_at = int(time())

    extraction_time = completed_at - started_at

    return JSONResponse(content={
        "success": True,
        "metadata": {
            "started_at": started_at,
            "completed_at": completed_at,
            "extraction_time": extraction_time
        },
        "data": {
            "markdown": extracted_markdown
        }
    }, status_code=200)
