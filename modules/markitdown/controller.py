from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse
from time import time

from constants.option_types import OPTION_TYPES
from common.contract_files import list_available_contracts, read_contract_file_bytes, read_contract_markdown
from common.confidence import ConfidenceCalculator
from .schema import MarkItDownExtractionRequest
from .service import MarkItDownExtractor

router = APIRouter(prefix="/markitdown")

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
async def extract_data(body: MarkItDownExtractionRequest):
    if(body.pdf_file not in list_available_contracts()):
        return JSONResponse(content={"success": False, "error": "Invalid pdf_file option"}, status_code=400)

    pdf_bytes = read_contract_file_bytes(body.pdf_file)
    
    started_at = int(time())

    extracted_markdown = MarkItDownExtractor().extract(pdf_bytes)

    completed_at = int(time())

    extraction_time = completed_at - started_at

    expected_markdown = read_contract_markdown(body.pdf_file)
    score = ConfidenceCalculator().calculate_confidence_score(expected_markdown, extracted_markdown)

    return JSONResponse(content={
        "success": True,
        "metadata": {
            "started_at": started_at,
            "completed_at": completed_at,
            "extraction_time": extraction_time,
            "score": score
        },
        "data": {
            "markdown": extracted_markdown
        }
    }, status_code=200)
