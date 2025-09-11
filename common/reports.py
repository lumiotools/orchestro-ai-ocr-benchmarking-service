from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4
from datetime import datetime


class Reports:
    """Simple reports manager that saves JSON reports under a project-level `reports/` dir.

    Usage:
        reports = Reports()
        report_id = reports.save_report({"module": "pymupdf4llm", "result": "..."})
        reports.list_reports()  # -> list of metadata dicts
        reports.get_report(report_id)  # -> full saved content
    """

    def __init__(self, reports_dir: Optional[Path] = None):
        # project root is two levels up from this file: /common -> project root
        if reports_dir is None:
            self.project_root = Path(__file__).resolve().parent.parent
            self.reports_dir = self.project_root / "reports"
        else:
            self.reports_dir = Path(reports_dir)
            self.project_root = self.reports_dir.parent

        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _report_path(self, report_id: str) -> Path:
        return self.reports_dir / f"{report_id}.json"

    def save_report(self, data: Dict[str, Any]) -> str:
        """Save a report dict as a JSON file and return its uuid id string.

        The method will add an `id` and `created_at` field (ISO 8601 UTC) to the saved object.
        """
        report_id = str(uuid4())
        now = datetime.utcnow().isoformat() + "Z"

        payload = dict(data)  # shallow copy
        payload.setdefault("id", report_id)
        payload.setdefault("created_at", now)

        path = self._report_path(report_id)
        with path.open("w", encoding="utf-8") as fh:
            json.dump(payload, fh, ensure_ascii=False, indent=2)

        return report_id

    def get_report(self, report_id: str) -> Dict[str, Any]:
        """Return the saved report contents for a given id.

        Raises FileNotFoundError if not present.
        """
        path = self._report_path(report_id)
        with path.open("r", encoding="utf-8") as fh:
            return json.load(fh)

    def list_reports(self) -> List[Dict[str, Any]]:
        """List metadata for all saved reports.

        Returns a list of dicts with at least 'id' and 'created_at', sorted by created_at (newest first).
        """
        results: List[Dict[str, Any]] = []
        for p in sorted(self.reports_dir.glob("*.json")):
            try:
                with p.open("r", encoding="utf-8") as fh:
                    payload = json.load(fh)
            except Exception:
                # if a file is corrupted, skip it
                continue

            meta = {
                "id": payload.get("id") or p.stem,
                "inputs": {
                    "provider": payload.get("inputs", {}).get("provider"),
                    "pdf_file": payload.get("inputs", {}).get("pdf_file"),
                },
                "created_at": payload.get("created_at"),
            }
            results.append(meta)

        # Inline parsing of created_at into a datetime for sorting (no separate function).
        results_with_dt = []
        for m in results:
            dt = m.get("created_at")
            if not dt:
                parsed = datetime.min
            else:
                try:
                    parsed = datetime.fromisoformat(dt.rstrip("Z"))
                except Exception:
                    parsed = datetime.min
            results_with_dt.append((parsed, m))

        results_with_dt.sort(key=lambda t: t[0], reverse=True)
        return [m for _, m in results_with_dt]
