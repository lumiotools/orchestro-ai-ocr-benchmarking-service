from fastapi.routing import APIRouter
from fastapi.responses import JSONResponse
from fastapi import UploadFile, File, Depends
from typing import Optional
from time import time
import asyncio

from constants.option_types import OPTION_TYPES, PDF_TYPES
from common.contract_files import list_available_contracts, read_contract_file_bytes, read_contract_markdown
from common.confidence_llm import LLMConfidenceCalculator
from common.reports import Reports
from .schema import PdfDocsMdExtractionRequest
from .service import PdfDocsMdExtractor

router = APIRouter(prefix="/pdf_docx_md")

@router.get("/options")
async def get_options():
    # list_available_contracts touches filesystem -- run in threadpool
    choices = await asyncio.to_thread(list_available_contracts)
    options = {
        "pdf_type": {
            "type": OPTION_TYPES.TAB,
            "choices": [PDF_TYPES.UPLOAD, PDF_TYPES.EXISTING],
            "content": {
                PDF_TYPES.UPLOAD: {
                    "upload_pdf": {
                        "type": OPTION_TYPES.FILE,
                    }
                },
                PDF_TYPES.EXISTING: {
                    "pdf_file": {
                        "type": OPTION_TYPES.SELECT,
                        "choices": choices,
                    }
                }
            }
        }
    }
    return JSONResponse(content={"success": True, "options": options}, status_code=200)


@router.post("/extract")
async def extract_data(
    body: PdfDocsMdExtractionRequest = Depends(PdfDocsMdExtractionRequest.as_form),
    upload_pdf: Optional[UploadFile] = File(None)
):
    # Validate pdf_file against available contracts (run IO in threadpool)
    available = await asyncio.to_thread(list_available_contracts)
    if body.pdf_type == PDF_TYPES.EXISTING and body.pdf_file not in available:
        return JSONResponse(content={"success": False, "error": "Invalid PDF file selected"}, status_code=400)
    
    if body.pdf_type == PDF_TYPES.UPLOAD and upload_pdf is None:
        return JSONResponse(content={"success": False, "error": "PDF file is required"}, status_code=400)

    if body.pdf_type == PDF_TYPES.EXISTING:
        # Read PDF from predefined contracts (run IO in threadpool)
        pdf_bytes = await asyncio.to_thread(read_contract_file_bytes, body.pdf_file)
    else:
        pdf_bytes = await upload_pdf.read()

    started_at = int(time())

    # extractor may be blocking; run in threadpool
    extracted_markdown = await asyncio.to_thread(PdfDocsMdExtractor().extract, pdf_bytes)

    completed_at = int(time())

    extraction_time = completed_at - started_at

    if body.pdf_type == PDF_TYPES.EXISTING:
        expected_markdown = await asyncio.to_thread(read_contract_markdown, body.pdf_file)
        score = await asyncio.to_thread(LLMConfidenceCalculator().calculate_confidence_score, expected_markdown, extracted_markdown)
    else:
        expected_markdown = ""
        score = {}

    report_id = Reports().save_report({
        "inputs": {
            "provider": "PdfDocsMd",
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
