"""
File Ingestion Module.
Handles processing of .txt, .md, .pdf, and .docx files into standardized JSON format.
"""

import os
from datetime import datetime
from typing import Any

try:
    from pypdf import PdfReader
except ImportError:
    PdfReader = None

try:
    from docx import Document
except ImportError:
    Document = None


class FileIngestor:
    """Ingests files and converts them to text with metadata."""

    @staticmethod
    def extract_text_from_pdf(filepath: str) -> str:
        """Extract text from PDF."""
        if not PdfReader:
            return "[Error: pypdf not installed]"
        try:
            reader = PdfReader(filepath)
            text = []
            for page in reader.pages:
                text.append(page.extract_text() or "")
            return "\n".join(text)
        except Exception as e:
            return f"[Error reading PDF: {str(e)}]"

    @staticmethod
    def extract_text_from_docx(filepath: str) -> str:
        """Extract text from DOCX."""
        if not Document:
            return "[Error: python-docx not installed]"
        try:
            doc = Document(filepath)
            return "\n".join([paragraph.text for paragraph in doc.paragraphs])
        except Exception as e:
            return f"[Error reading DOCX: {str(e)}]"

    @classmethod
    def process_file(cls, filepath: str) -> dict[str, Any]:
        """Process a single file and return its structured representation."""
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        filename = os.path.basename(filepath)
        ext = os.path.splitext(filename)[1].lower()
        
        content = ""
        
        if ext == '.pdf':
            content = cls.extract_text_from_pdf(filepath)
        elif ext == '.docx':
            content = cls.extract_text_from_docx(filepath)
        elif ext in ['.txt', '.md', '.json', '.py', '.csv']:
            try:
                with open(filepath, encoding='utf-8', errors='ignore') as f:
                    content = f.read()
            except Exception as e:
                content = f"[Error reading text file: {str(e)}]"
        else:
            content = "[Unsupported file type]"

        # Create standardized JSON structure
        file_data = {
            "metadata": {
                "filename": filename,
                "extension": ext,
                "path": os.path.abspath(filepath),
                "ingested_at": datetime.now().isoformat(),
                "size_bytes": os.path.getsize(filepath)
            },
            "content": content
        }
        
        return file_data

    @classmethod
    def ingest_paths(cls, paths: list[str]) -> list[dict[str, Any]]:
        """Ingest a list of file paths."""
        results = []
        for path in paths:
            if path.strip():
                try:
                    results.append(cls.process_file(path.strip()))
                except Exception as e:
                    print(f"Warning: Could not process {path}: {e}")
        return results

