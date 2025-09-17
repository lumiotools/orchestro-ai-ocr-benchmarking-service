from pydantic import BaseModel
from typing import Optional
from fastapi import Form


class DoclingExtractionRequest(BaseModel):
    pdf_type: str
    pdf_file: Optional[str] = None
    do_ocr: Optional[bool] = True
    force_ocr: Optional[bool] = False
    ocr_engine: Optional[str] = "easyocr"
    pdf_backend: Optional[str] = "dlparse_v4"
    table_mode: Optional[str] = "accurate"
    table_cell_matching: Optional[bool] = True
    do_table_structure: Optional[bool] = True
    md_page_break_placeholder: Optional[str] = ""

    @classmethod
    def as_form(cls, pdf_type: str = Form(...),
                pdf_file: Optional[str] = Form(None),
                do_ocr: Optional[bool] = Form(True),
                force_ocr: Optional[bool] = Form(False),
                ocr_engine: Optional[str] = Form("easyocr"),
                pdf_backend: Optional[str] = Form("dlparse_v4"),
                table_mode: Optional[str] = Form("accurate"),
                table_cell_matching: Optional[bool] = Form(True),
                do_table_structure: Optional[bool] = Form(True),
                md_page_break_placeholder: Optional[str] = Form("")):
        return cls(pdf_type=pdf_type,
                   pdf_file=pdf_file,
                   do_ocr=do_ocr,
                   force_ocr=force_ocr,
                   ocr_engine=ocr_engine,
                   pdf_backend=pdf_backend,
                   table_mode=table_mode,
                   table_cell_matching=table_cell_matching,
                   do_table_structure=do_table_structure,
                   md_page_break_placeholder=md_page_break_placeholder)
