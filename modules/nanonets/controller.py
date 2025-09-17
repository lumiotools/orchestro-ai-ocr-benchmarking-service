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
from .schema import NanonetsExtractionRequest
from .service import NanonetsExtractor

router = APIRouter(prefix="/nanonets")

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
        },
        "prompt": {
            "type": OPTION_TYPES.LONG_STRING,
            "default": "Extract the text from the above document as if you were reading it naturally. Return the tables in html format. Return the equations in LaTeX representation. If there is an image in the document and image caption is not present, add a small description of the image inside the <img></img> tag; otherwise, add the image caption inside <img></img>. Watermarks should be wrapped in brackets. Ex: <watermark>OFFICIAL COPY</watermark>. Page numbers should be wrapped in brackets. Ex: <page_number>14</page_number> or <page_number>9/22</page_number>. Prefer using ☐ and ☑ for check boxes.",
        }
    }
    return JSONResponse(content={"success": True, "options": options}, status_code=200)


@router.post("/extract")
async def extract_data(
    body: NanonetsExtractionRequest = Depends(NanonetsExtractionRequest.as_form),
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
    extracted_markdown = await asyncio.to_thread(NanonetsExtractor(prompt=body.prompt).extract, pdf_bytes)

    completed_at = int(time())

    extraction_time = completed_at - started_at

    if body.pdf_type == PDF_TYPES.EXISTING:
        expected_markdown = await asyncio.to_thread(read_contract_markdown, body.pdf_file)
        score = await asyncio.to_thread(LLMConfidenceCalculator().calculate_confidence_score, expected_markdown, extracted_markdown)
    else:
        expected_markdown = ""
        score = {}
        body.pdf_file = upload_pdf.filename

    report_id = Reports().save_report({
        "inputs": {
            "provider": "Nanonets",
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
