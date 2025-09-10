import os
from typing import Any, Dict, Optional
from dotenv import load_dotenv
load_dotenv()

import requests
import json
import time

MARKER_URL = "https://www.datalab.to/api/v1/marker"


class DatalabExtractor:
	"""Client for the Datalab marker API.

	Example:
		client = DatalabExtractor(api_key=os.environ.get('DATALAB_API_KEY'))
		markdown = client.extract(pdf_bytes)
	"""

	def __init__(self, paginated: bool = False, force_ocr: bool = False, filename: str = "contract.pdf", timeout: int = 60):
		self.api_key = os.environ.get("DATALAB_API_KEY")
		self.marker_url = MARKER_URL

		self.paginated = paginated
		self.force_ocr = force_ocr
		self.filename = filename
		self.timeout = timeout

	def extract(self, pdf_bytes: bytes) -> str:
		"""
		Send PDF bytes to the Datalab marker API and return the final markdown string.

		Raises RuntimeError on configuration, network, or API errors.
		"""
		if not self.api_key:
			raise RuntimeError("DATALAB_API_KEY not configured in environment and not provided to Datalab()")

		files = {"file": (self.filename, pdf_bytes, "application/pdf")}
		data = {
			"output_format": "markdown",
			"langs": "English",
			"paginate": "true" if self.paginated else "false",
			"force_ocr": "true" if self.force_ocr else "false",
		}
		headers = {"X-Api-Key": self.api_key}

		resp = requests.post(self.marker_url, headers=headers, files=files, data=data, timeout=self.timeout)
		try:
			resp.raise_for_status()
		except requests.HTTPError:
			raise RuntimeError(f"API Error ({resp.status_code}): {resp.text}")

		try:
			payload = resp.json()
		except ValueError:
			raise RuntimeError(f"Invalid JSON response from Datalab: {resp.text}")
        
		if not payload.get("success", True):
			err = payload.get("error") or payload.get("message") or "Unknown error"
			raise RuntimeError(f"API Error: {err}")

		# Follow check URL if present
		check_url = payload["request_check_url"]

		status = "processing"
		final_payload = None
  
		while status == "processing":
			time.sleep(2) 
			final_payload = self._fetch_url(check_url, timeout=self.timeout)
			status = final_payload.get("status", "processing")

   
		markdown = self._extract_markdown_from_payload(final_payload)
		if markdown is None:
			raise RuntimeError(f"No markdown found in Datalab response: {json.dumps(final_payload)[:2000]}")

		return markdown

	def _fetch_url(self, check_url: str, timeout: int = 60) -> Dict[str, Any]:
		if not self.api_key:
			raise RuntimeError("DATALAB_API_KEY not configured in environment and not provided to Datalab()")
		headers = {"X-Api-Key": self.api_key}
		resp = requests.get(check_url, headers=headers, timeout=timeout)
		try:
			resp.raise_for_status()
		except requests.HTTPError:
			raise RuntimeError(f"API Error ({resp.status_code}): {resp.text}")

		try:
			return resp.json()
		except ValueError:
			raise RuntimeError(f"Invalid JSON response from Datalab URL: {resp.text}")

	@staticmethod
	def _extract_markdown_from_payload(payload: Dict[str, Any]) -> Optional[str]:
		# Direct keys
		for key in ("markdown", "result", "text", "output", "data", "content"):
			if key in payload and isinstance(payload[key], str):
				return payload[key]

		# Nested under 'data'
		data = payload.get("data")
		if isinstance(data, dict):
			for key in ("markdown", "text", "content", "output"):
				if key in data and isinstance(data[key], str):
					return data[key]

		# Fallback: if payload contains a single string value anywhere, return it
		for v in payload.values():
			if isinstance(v, str):
				return v

		return None

