"""
Handles saving uploaded files to disk.

Files are organized as:  storage/documents/{workspace_id}/{filename}
The path stored in the database is relative to the backend/ directory so it
remains valid if the project is moved.
"""

import shutil
from pathlib import Path

from fastapi import UploadFile

# Root of the storage directory, relative to this file's location.
# Path(__file__) is this file → .parent × 3 climbs to backend/ → storage/documents
STORAGE_ROOT = Path(__file__).parent.parent.parent / "storage" / "documents"


def save_upload(file: UploadFile, workspace_id: int) -> tuple[Path, int]:
    """
    Write an uploaded file to disk and return (absolute_path, file_size_bytes).

    Creates the workspace sub-directory if it doesn't exist yet.
    If a file with the same name already exists it is overwritten — a more
    robust system would add a UUID prefix, but that's fine for the MVP.
    """
    dest_dir = STORAGE_ROOT / str(workspace_id)
    dest_dir.mkdir(parents=True, exist_ok=True)

    dest_path = dest_dir / file.filename

    # shutil.copyfileobj streams the upload directly to disk — it never loads
    # the whole file into memory at once, which matters for large PDFs.
    with dest_path.open("wb") as out:
        shutil.copyfileobj(file.file, out)

    file_size = dest_path.stat().st_size
    return dest_path, file_size


def delete_file(storage_path: str) -> None:
    """Remove a file from disk. Called when a Document row is deleted."""
    path = Path(storage_path)
    if path.exists():
        path.unlink()
