import re
from typing import Optional
import fitz  # PyMuPDF
import pymupdf4llm as pm4l


class PyMuPDF4LLMExtractor:
    """Single-class extractor that exposes only .extract(pdf_bytes, sanitize_mode).

    This keeps the public surface minimal while encapsulating markdown-sanitization logic.
    """

    def __init__(self, sanitize_mode: str = "strip"):
        self.sanitize_mode = sanitize_mode

    def _sanitize_segment(self, segment: str, mode: str) -> str:
        if mode == "strip":
            return re.sub(r"~~(.*?)~~", r"\1", segment, flags=re.DOTALL)
        elif mode == "escape":
            return segment.replace("~~", r"\~\~")
        return segment

    def _sanitize_markdown(self, md: str, mode: str) -> str:
        parts = re.split(r'(```.*?```)', md, flags=re.DOTALL)
        for i in range(len(parts)):
            chunk = parts[i]
            if chunk.startswith("```") and chunk.endswith("```"):
                continue

            segments = re.split(r'(`[^`\n]*`)', chunk)
            for j in range(len(segments)):
                seg = segments[j]
                if seg.startswith("`") and seg.endswith("`"):
                    continue
                segments[j] = self._sanitize_segment(seg, mode)
            parts[i] = "".join(segments)
        return "".join(parts)

    def _doc_to_markdown(self, doc: fitz.Document) -> str:
        return pm4l.to_markdown(doc)

    def extract(self, pdf_bytes: bytes, sanitize_mode: Optional[str] = None) -> str:
        """Open PDF bytes, convert to markdown, sanitize, and return the string.

        Args:
            pdf_bytes: raw PDF file bytes
            sanitize_mode: 'strip' or 'escape' to control strikethrough handling (defaults to instance setting)
        """
        mode = sanitize_mode if sanitize_mode is not None else self.sanitize_mode

        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        try:
            md = self._doc_to_markdown(doc)
        finally:
            try:
                doc.close()
            except Exception:
                pass

        return self._sanitize_markdown(md, mode=mode)