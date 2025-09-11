from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse
from time import time
import asyncio

from constants.option_types import OPTION_TYPES
from common.contract_files import list_available_contracts, read_contract_file_bytes, read_contract_markdown
from common.confidence import ConfidenceCalculator
from .schema import DoclingExtractionRequest
from .service import DoclingExtractor

router = APIRouter(prefix="/docling")

@router.get("/options")
async def get_options():
    # list_available_contracts touches filesystem -- run in threadpool
    choices = await asyncio.to_thread(list_available_contracts)
    options = {
        "pdf_file": {
            "type": OPTION_TYPES.SELECT,
            "choices": choices,
        },
        "do_ocr": {
            "type": OPTION_TYPES.BOOLEAN,
            "default": False
        },
        "do_table_structure": {
            "type": OPTION_TYPES.BOOLEAN,
            "default": True
        },
        "do_table_structure_cell_matching": {
            "type": OPTION_TYPES.BOOLEAN,
            "default": True
        }
    }
    return JSONResponse(content={"success": True, "options": options}, status_code=200)


@router.post("/extract")
async def extract_data(body: DoclingExtractionRequest):
    # validate and read file in threadpool to avoid blocking the event loop
    available = await asyncio.to_thread(list_available_contracts)
    if body.pdf_file not in available:
        return JSONResponse(content={"success": False, "error": "Invalid pdf_file option"}, status_code=400)

    pdf_bytes = await asyncio.to_thread(read_contract_file_bytes, body.pdf_file)

    started_at = int(time())

    # extractor.extract is synchronous and may be CPU/IO heavy: run in threadpool
    extracted_markdown = await asyncio.to_thread(
        DoclingExtractor(
            do_ocr=body.do_ocr,
            do_table_structure=body.do_table_structure,
            do_table_structure_cell_matching=body.do_table_structure_cell_matching,
        ).extract,
        pdf_bytes,
    )

    completed_at = int(time())

    extraction_time = completed_at - started_at
    
    expected_markdown = await asyncio.to_thread(read_contract_markdown, body.pdf_file)
    score = await asyncio.to_thread(ConfidenceCalculator().calculate_confidence_score, expected_markdown, extracted_markdown)

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
