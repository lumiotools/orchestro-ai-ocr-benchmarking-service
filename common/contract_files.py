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

def read_contract_file_bytes(contract_filename: str) -> bytes:
    """
    Read the content of a contract PDF file as bytes.
    """
    contract_path = Path("contracts") / contract_filename
    if not contract_path.exists() or not contract_path.is_file():
        raise FileNotFoundError(f"Contract file not found: {contract_path}")
    with open(contract_path, "rb") as f:
        return f.read()
    
def read_contract_markdown(contract_filename: str) -> str:
    """
    Read the content of a contract markdown file as text.
    """
    contract_path = Path("contract_markdowns") / contract_filename.replace(".pdf", ".md")
    if not contract_path.exists() or not contract_path.is_file():
        raise FileNotFoundError(f"Contract markdown file not found: {contract_path}")
    with open(contract_path, "r", encoding="utf-8") as f:
        return f.read()