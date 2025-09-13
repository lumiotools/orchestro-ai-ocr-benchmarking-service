from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

from cron.ping import scheduler as ping_scheduler
from modules.nanonets.controller import router as nanonets_router
from modules.docling.controller import router as docling_router
from modules.datalab.controller import router as datalab_router
from modules.vision_llm.controller import router as vision_llm_router
from modules.pymupdf4llm.controller import router as pymupdf4llm_router
from modules.markitdown.controller import router as markitdown_router
from modules.pdf_docx_md.controller import router as pdf_docx_md_router

from common.reports import Reports

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start the scheduler
    ping_scheduler.start()
    print("Cron Scheduler started.")
    
    yield  # This is where FastAPI serves requests
    
    # Shutdown: Any cleanup can go here
    ping_scheduler.shutdown() # Uncomment if needed
    
app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(nanonets_router, prefix="/api/providers")
app.include_router(docling_router, prefix="/api/providers")
app.include_router(datalab_router, prefix="/api/providers")
app.include_router(vision_llm_router, prefix="/api/providers")
app.include_router(pymupdf4llm_router, prefix="/api/providers")
app.include_router(markitdown_router, prefix="/api/providers")
app.include_router(pdf_docx_md_router, prefix="/api/providers")

@app.get("/")
async def root():
	return JSONResponse(content={"success": True})

@app.get("/api/ping")
async def ping():
	return JSONResponse(content={"success": True})

@app.get("/api/providers")
async def get_providers():
    providers = [
        {"name": "Nanonets", "label": "nanonets"},
        {"name": "Docling", "label": "docling"},
        {"name": "Datalab", "label": "datalab"},
        {"name": "VisionLLM", "label": "vision_llm"},
        {"name": "PyMuPDF4LLM", "label": "pymupdf4llm"},
        {"name": "MarkItDown", "label": "markitdown"},
        {"name": "PdfDocsMd", "label": "pdf_docx_md"},
    ]
    return JSONResponse(content={"success": True, "data": {"providers": providers}}, status_code=200)


@app.get("/api/reports")
async def list_reports():
    try:
        reports = Reports()
        items = reports.list_reports()
        return JSONResponse(content={"success": True, "data": {"reports": items}}, status_code=200)
    except Exception as exc:
        return JSONResponse(content={"success": False, "error": str(exc)}, status_code=500)


@app.get("/api/reports/{report_id}")
async def get_report(report_id: str):
    try:
        reports = Reports()
        payload = reports.get_report(report_id)
        return JSONResponse(content={"success": True, "data": {"report": payload}}, status_code=200)
    except FileNotFoundError:
        return JSONResponse(content={"success": False, "error": "Report not found"}, status_code=404)
    except Exception as exc:
        return JSONResponse(content={"success": False, "error": str(exc)}, status_code=500)

if __name__ == "__main__":
	uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
