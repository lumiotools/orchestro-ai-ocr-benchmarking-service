from io import BytesIO
from typing import Optional

from docling.document_converter import DocumentConverter, PdfFormatOption  # type: ignore
from docling.datamodel.base_models import DocumentStream, InputFormat  # type: ignore
from docling.datamodel.pipeline_options import PdfPipelineOptions  # type: ignore


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
            do_ocr: Optional[bool] = False,
            do_table_structure: Optional[bool] = False,
            do_table_structure_cell_matching: Optional[bool] = False,
    ):
        """Initialize the extractor and prepare pipeline options.

        Args:
                pdf_pipeline_options: Pre-built PdfPipelineOptions to start from.
                do_ocr: Override for OCR enabling.
                table_structure: Override for table structure extraction.
                cell_matching: Override for cell matching inside table structure options.
        """
        self.pipeline_options = self._build_pipeline_options(
            do_ocr=do_ocr,
            do_table_structure=do_table_structure,
            do_table_structure_cell_matching=do_table_structure_cell_matching,
        )

    def extract(
            self,
            pdf_bytes: bytes,
    ) -> str:
        """Extract markdown from PDF bytes using the configured pipeline.

        Raises:
                RuntimeError: on conversion errors.
        """
        format_options = {InputFormat.PDF: PdfFormatOption(
            pipeline_options=self.pipeline_options)}
        converter = DocumentConverter(format_options=format_options)
        stream = DocumentStream(name="contract.pdf", stream=BytesIO(pdf_bytes))
        try:
            result = converter.convert(stream)
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Docling conversion failed: {exc}") from exc

        document = result.document
        if document is None:
            raise RuntimeError("Docling result missing 'document' attribute")
        return document.export_to_markdown()

    def _build_pipeline_options(
            self,
            do_ocr: Optional[bool] = False,
            do_table_structure: Optional[bool] = False,
            do_table_structure_cell_matching: Optional[bool] = False,
    ) -> PdfPipelineOptions:
        # Start with provided or default instance
        opts = PdfPipelineOptions()

        if do_ocr is not None:
            opts.do_ocr = do_ocr
        if do_table_structure is not None:
            opts.do_table_structure = do_table_structure
        if do_table_structure_cell_matching is not None:
            opts.table_structure_options.do_cell_matching = do_table_structure_cell_matching

        return opts
