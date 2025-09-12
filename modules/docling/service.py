import requests
import os
import time
from typing import Optional
from dotenv import load_dotenv
load_dotenv()

DOCLING_URL_FILE_ASYNC = "https://api-docling-dev.app.orchestro.ai/v1/convert/file/async"
DOCLING_URL_TASK_POOL = "https://api-docling-dev.app.orchestro.ai/v1/status/poll/{task_id}"
DOCLING_URL_TASK_RESULT = "https://api-docling-dev.app.orchestro.ai/v1/result/{task_id}"

class DoclingExtractor:
    """Convert PDF bytes to Markdown using Docling.

    Minimal overrides supported:
    - do_ocr
    - table_structure
    - cell_matching (table_structure_options.do_cell_matching)

    Advanced accelerator / lang overrides removed for now to keep interface minimal.
    """

    def __init__(
            self,
            do_ocr: Optional[bool] = True,
            force_ocr: Optional[bool] = False,
            ocr_engine: Optional[str] = "easyocr",
            pdf_backend: Optional[str] = "dlparse_v4",
            table_mode: Optional[str] = "accurate",
            table_cell_matching: Optional[bool] = True,
            do_table_structure: Optional[bool] = True,
            md_page_break_placeholder: Optional[str] = "",
    ):
        """Initialize the extractor and prepare pipeline options.

        Args:
                pdf_pipeline_options: Pre-built PdfPipelineOptions to start from.
                do_ocr: Override for OCR enabling.
                table_structure: Override for table structure extraction.
                cell_matching: Override for cell matching inside table structure options.
        """
        self.api_key = os.environ.get("DOCLING_API_KEY")
        self.docling_url_file_async = DOCLING_URL_FILE_ASYNC
        self.docling_url_task_pool = DOCLING_URL_TASK_POOL
        self.docling_url_task_result = DOCLING_URL_TASK_RESULT
  
        self.do_ocr = do_ocr
        self.force_ocr = force_ocr
        self.ocr_engine = ocr_engine
        self.pdf_backend = pdf_backend
        self.table_mode = table_mode
        self.table_cell_matching = table_cell_matching
        self.do_table_structure = do_table_structure
        self.md_page_break_placeholder = md_page_break_placeholder

    def extract(
            self,
            pdf_bytes: bytes,
    ) -> str:
        """Extract markdown from PDF bytes using the configured pipeline.

        Raises:
                RuntimeError: on conversion errors.
        """
        
        if not self.api_key:
            raise RuntimeError("DOCLING_API_KEY not configured in environment and not provided to DoclingExtractor()")

        headers = {"Authorization": self.api_key}

        # Submit the PDF and get a task id
        task_id = self._submit_file_async(pdf_bytes, headers)

        # Poll until the task reports success
        self._poll_task_until_success(task_id, headers)

        # Fetch result
        markdown_content = self._fetch_result(task_id, headers)

        return markdown_content

    def _submit_file_async(self, pdf_bytes: bytes, headers: dict) -> str:
        """Submit PDF bytes to the async endpoint and return the task_id.

        Raises RuntimeError on HTTP error.
        """
        files = {"files": ("Contract.pdf", pdf_bytes, "application/pdf")}
        data = self._build_payload()

        response = requests.post(self.docling_url_file_async, headers=headers, data=data, files=files)
        try:
            response.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(f"API Error ({response.status_code}): {response.text}") from e

        response_json = response.json()
        task_id = response_json.get("task_id")
        return task_id

    def _poll_task_until_success(self, task_id: str, headers: dict, poll_interval: float = 1, timeout: Optional[float] = 300) -> None:
        """Poll the task pool endpoint until the task_status is 'success'.

        This will loop until success. Optional timeout in seconds can be provided.
        """
        start = time.time()
        while True:
            pool_response = requests.get(self.docling_url_task_pool.format(task_id=task_id), headers=headers)
            pool_response.raise_for_status()
            pool_response_json = pool_response.json()
            status = pool_response_json.get("task_status")

            if status == "success":
                return

            if timeout is not None and (time.time() - start) > timeout:
                raise RuntimeError(f"Polling timed out after {timeout} seconds for task {task_id}")

            time.sleep(poll_interval)

    def _fetch_result(self, task_id: str, headers: dict) -> str:
        """Fetch the result payload for a completed task and return markdown content.

        Raises RuntimeError on HTTP error.
        """
        result_response = requests.get(self.docling_url_task_result.format(task_id=task_id), headers=headers)
        try:
            result_response.raise_for_status()
        except requests.HTTPError as e:
            raise RuntimeError(f"API Error ({result_response.status_code}): {result_response.text}") from e

        result_response_json = result_response.json()
        markdown_content = result_response_json.get("document", {}).get("md_content", "")
        return markdown_content
  

    def _build_payload(
            self,
    ) -> dict:
        # Start with provided or default instance
        payload = {
            "do_ocr": self.do_ocr,
            "force_ocr": self.force_ocr,
            "ocr_engine": self.ocr_engine,
            "pdf_backend": self.pdf_backend,
            "table_mode": self.table_mode,
            "do_cell_matching": self.table_cell_matching,
            "do_table_structure": self.do_table_structure,
            "md_page_break_placeholder": self.md_page_break_placeholder,
        }

        return payload
