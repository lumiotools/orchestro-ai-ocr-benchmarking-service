from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse
from time import time
import asyncio

from constants.option_types import OPTION_TYPES
from common.contract_files import list_available_contracts, read_contract_file_bytes, read_contract_markdown
from common.confidence import ConfidenceCalculator
from common.reports import Reports
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
            "default": True
        },
        "force_ocr": {
            "type": OPTION_TYPES.BOOLEAN,
            "default": False
        },
        "ocr_engine": {
            "type": OPTION_TYPES.SELECT,
            "default": "easyocr",
            "choices": ["easyocr", "ocrmac", "rapidocr", "tesserocr", "tesseract"]
        },
        "pdf_backend": {
            "type": OPTION_TYPES.SELECT,
            "default": "dlparse_v4",
            "choices": ["pypdfium2", "dlparse_v1", "dlparse_v2", "dlparse_v4"]
        },
        "table_mode": {
            "type": OPTION_TYPES.SELECT,
            "default": "accurate",
            "choices": ["fast", "accurate"]
        },
        "table_cell_matching": {
            "type": OPTION_TYPES.BOOLEAN,
            "default": True
        },
        "do_table_structure": {
            "type": OPTION_TYPES.BOOLEAN,
            "default": True
        },
        "md_page_break_placeholder": {
            "type": OPTION_TYPES.STRING,
            "default": ""
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
            force_ocr=body.force_ocr,
            ocr_engine=body.ocr_engine,
            pdf_backend=body.pdf_backend,
            table_mode=body.table_mode,
            table_cell_matching=body.table_cell_matching,
            do_table_structure=body.do_table_structure,
            md_page_break_placeholder=body.md_page_break_placeholder,
        ).extract,
        pdf_bytes,
    )

    completed_at = int(time())

    extraction_time = completed_at - started_at

    expected_markdown = await asyncio.to_thread(read_contract_markdown, body.pdf_file)
    score = await asyncio.to_thread(ConfidenceCalculator().calculate_confidence_score, expected_markdown, extracted_markdown)

    report_id = Reports().save_report({
        "inputs": {
            "provider": "Docling",
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
