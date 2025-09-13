import fitz
from openai import OpenAI
from html_to_markdown import convert_to_markdown
import base64

PROMPT = """Extract the text from the above document as if you were reading it naturally. Return the tables in html format. If there is an image in the document and image caption is not present, add a small description of the image inside the <img></img> tag; otherwise, add the image caption inside <img></img>. Watermarks should be wrapped in brackets. Ex: <watermark>OFFICIAL COPY</watermark>. Page numbers should be wrapped in brackets. Do not include any additional explaination or information. Extract only what's visible in the document."""

class VisionLLMExtractor:
    """Single-class extractor that exposes only .extract(pdf_bytes).

    This keeps the public surface minimal while encapsulating markdown-sanitization logic.
    """

    def __init__(self, vllm_base_url: str = None, vllm_api_key: str = None, vllm_model_id: str = None, vllm_prompt: str = PROMPT):
        if not all([vllm_base_url, vllm_api_key, vllm_model_id]):
            raise ValueError("All VisionLLM parameters must be provided.")
        
        self.vision_llm_client = OpenAI(
            api_key=vllm_api_key,
            base_url=vllm_base_url,
        )
        self.vision_llm_model_id = vllm_model_id
        self.vision_llm_prompt = vllm_prompt

    def extract(self, pdf_bytes: bytes) -> str:
        """
        Extract text from PDF bytes using VisionLLM.

        Args:
            pdf_bytes (bytes): The PDF file content in bytes.

        Returns:
            str: The extracted text from the PDF.
        """

        total_pages = self._get_page_count(pdf_bytes)
        
        print(f"Extracting text from {total_pages} pages using VisionLLM...")
        
        extracted_markdown = ""

        import concurrent.futures

        def _process(page_number: int):
            try:
                print(f"Processing page {page_number + 1}...")
                page_image_b64 = self._get_page_image(pdf_bytes, page_number)
                extracted = self._read_page_as_markdown(page_image_b64)
                print(f"Extracted markdown from page {page_number + 1}.")
                return page_number, extracted
            except Exception as e:
                print(f"Error processing page {page_number + 1}: {e}")
                return page_number, ""

        if total_pages == 0:
            return ""

        results = ["" for _ in range(total_pages)]

        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = [executor.submit(_process, i) for i in range(total_pages)]
            for fut in concurrent.futures.as_completed(futures):
                page_num, markdown = fut.result()
                results[page_num] = markdown

        # Preserve original behavior of adding a blank line after each page
        extracted_markdown = "\n\n".join(results) + ("\n\n" if results else "")

        return extracted_markdown

    def _read_page_as_markdown(self, page_image_b64: str) -> str:
        """
        Use VisionLLM to extract markdown text from a base64-encoded page image.

        Args:
            page_image_b64 (str): The base64-encoded image of the page.
        Returns:
            str: The extracted markdown text from the image.
        """

        response = self.vision_llm_client.chat.completions.create(
            model=self.vision_llm_model_id,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": page_image_b64,
                            },
                        },
                        {
                            "type": "text",
                            "text": self.vision_llm_prompt,
                        },
                    ]
                }
            ]
        )
        
        markdown_text = response.choices[0].message.content
        markdown_text = convert_to_markdown(markdown_text, escape_asterisks=False, escape_misc=False).replace("\n", "  \n")
        return markdown_text

    def _get_page_count(self, pdf_bytes: bytes) -> int:
        """
        Get the number of pages in a PDF from its bytes.

        Args:
            pdf_bytes (bytes): The PDF file content in bytes.
        Returns:
            int: The number of pages in the PDF.
        """
        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        try:
            return pdf_document.page_count
        finally:
            pdf_document.close()

    def _get_page_image(self, pdf_bytes: bytes, page_number: int):
        """
        Extract a specific page from PDF bytes as an image.

        Args:
            pdf_bytes (bytes): The PDF file content in bytes.
            page_number (int): The page number to extract (0-indexed).

        Returns:
            base64: The extracted page as a base64-encoded image.
        """

        pdf_document = fitz.open(stream=pdf_bytes, filetype="pdf")
        try:
            page = pdf_document.load_page(page_number)
            scale = 1.5
            mat = fitz.Matrix(scale, scale)
            pix = page.get_pixmap(matrix=mat)
            img_bytes = pix.tobytes("png")
            b64 = base64.b64encode(img_bytes).decode("ascii")
            return f"data:image/png;base64,{b64}"
        finally:
            pdf_document.close()
