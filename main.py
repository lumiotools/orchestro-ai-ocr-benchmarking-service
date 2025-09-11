from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
from contextlib import asynccontextmanager

from cron.ping import scheduler as ping_scheduler
from modules.datalab.controller import router as datalab_router
from modules.pymupdf4llm.controller import router as pymupdf4llm_router
from modules.docling.controller import router as docling_router
from modules.markitdown.controller import router as markitdown_router

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

app.include_router(datalab_router, prefix="/api/providers")
app.include_router(pymupdf4llm_router, prefix="/api/providers")
app.include_router(docling_router, prefix="/api/providers")
app.include_router(markitdown_router, prefix="/api/providers")

@app.get("/")
async def root():
	return JSONResponse(content={"success": True})

@app.get("/api/ping")
async def ping():
	return JSONResponse(content={"success": True})

@app.get("/api/providers")
async def get_providers():
    providers = [
        {"name": "Datalab", "label": "datalab"},
        {"name": "PyMuPDF4LLM", "label": "pymupdf4llm"},
        {"name": "Docling", "label": "docling"},
        {"name": "MarkItDown", "label": "markitdown"},
    ]
    return JSONResponse(content={"success": True, "data": {"providers": providers}}, status_code=200)

if __name__ == "__main__":
	uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
