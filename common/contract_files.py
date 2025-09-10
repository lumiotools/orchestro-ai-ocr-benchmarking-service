from pathlib import Path
from typing import List

def list_available_contracts() -> List[str]:
    """
    List all available contract PDF files in the contracts directory.
    """
    contracts_dir = Path("contracts")
    if not contracts_dir.exists() or not contracts_dir.is_dir():
        return []
    return [f.name for f in contracts_dir.iterdir() if f.is_file() and f.suffix.lower() == ".pdf"]