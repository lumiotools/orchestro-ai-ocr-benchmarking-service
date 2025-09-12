from pathlib import Path
from typing import List

def list_available_contracts() -> List[str]:
    """
    List all available contract PDF files in the contracts directory, sorted by filename.
    """
    contracts_dir = Path("contracts")
    if not contracts_dir.exists() or not contracts_dir.is_dir():
        return []
    # Recursively find all PDF files and return their paths relative to the contracts directory.
    pdf_files = []
    for f in contracts_dir.rglob("*.pdf"):
        if f.is_file():
            # return POSIX-style relative path (e.g. "abc/def.pdf") for consistency across platforms
            pdf_files.append(str(f.relative_to(contracts_dir).as_posix()))
    # Sort by the base filename (case-insensitive) for predictable ordering
    pdf_files.sort(key=lambda p: Path(p).name.lower())
    return pdf_files

def read_contract_file_bytes(contract_filename: str) -> bytes:
    """
    Read the content of a contract PDF file as bytes.
    """
    contracts_dir = Path("contracts")
    if not contracts_dir.exists() or not contracts_dir.is_dir():
        raise FileNotFoundError(f"Contracts directory not found: {contracts_dir}")

    # Try the provided path first (supports nested paths like 'abc/def.pdf')
    contract_path = contracts_dir / contract_filename
    if contract_path.exists() and contract_path.is_file():
        with open(contract_path, "rb") as f:
            return f.read()

    # Fallback: treat input as a basename and search recursively for a matching PDF
    requested_name = Path(contract_filename).name
    for f in contracts_dir.rglob("*.pdf"):
        if f.is_file() and f.name == requested_name:
            with open(f, "rb") as fh:
                return fh.read()

    raise FileNotFoundError(f"Contract file not found: {contract_filename}")
    
def read_contract_markdown(contract_filename: str) -> str:
    """
    Read the content of a contract markdown file as text.
    """
    md_dir = Path("contract_markdowns")
    if not md_dir.exists() or not md_dir.is_dir():
        raise FileNotFoundError(f"Contract markdowns directory not found: {md_dir}")

    # Map requested contract filename to markdown name (supports both 'abc/def.pdf' and 'def.pdf')
    requested_md = Path(contract_filename).with_suffix(".md")

    # Try the provided path first
    md_path = md_dir / requested_md
    if md_path.exists() and md_path.is_file():
        with open(md_path, "r", encoding="utf-8") as f:
            return f.read()

    # Fallback: search by basename for matching markdown file
    requested_name = requested_md.name
    for f in md_dir.rglob("*.md"):
        if f.is_file() and f.name == requested_name:
            with open(f, "r", encoding="utf-8") as fh:
                return fh.read()

    raise FileNotFoundError(f"Contract markdown file not found for: {contract_filename}")