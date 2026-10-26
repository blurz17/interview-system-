import uuid
from pathlib import Path

from fastapi import UploadFile

from app.core.config import get_settings
from app.core.errors import BadRequestError

settings = get_settings()

ALLOWED_MIME_TYPES = {
    "application/pdf": ".pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document": ".docx",
    "text/plain": ".txt",
    "text/markdown": ".txt",
}

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt"}


class LocalStorageService:
    def __init__(self, base_dir: str | None = None):
        self.base_dir = Path(base_dir or settings.STORAGE_LOCAL_DIR)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def validate_file(self, upload_file: UploadFile) -> str:
        filename = upload_file.filename or "unknown.txt"
        ext = Path(filename).suffix.lower()

        if ext not in ALLOWED_EXTENSIONS:
            raise BadRequestError(
                f"Unsupported file extension '{ext}'. Allowed types: PDF, DOCX, TXT."
            )

        return ext

    async def save_file(self, user_id: uuid.UUID, upload_file: UploadFile) -> tuple[str, int]:
        ext = self.validate_file(upload_file)

        # Secure random file key inside user folder
        user_dir = self.base_dir / str(user_id)
        user_dir.mkdir(parents=True, exist_ok=True)

        file_id = uuid.uuid4()
        storage_rel_path = f"{user_id}/{file_id}{ext}"
        target_path = self.base_dir / storage_rel_path

        # Stream write with bounded size check
        total_bytes = 0
        max_bytes = settings.STORAGE_MAX_FILE_SIZE_BYTES

        with open(target_path, "wb") as f:
            while chunk := await upload_file.read(1024 * 64):  # 64 KB chunks
                total_bytes += len(chunk)
                if total_bytes > max_bytes:
                    # Clean up oversized file
                    f.close()
                    if target_path.exists():
                        target_path.unlink()
                    raise BadRequestError(
                        f"File size exceeds limit of {max_bytes // (1024 * 1024)}MB."
                    )
                f.write(chunk)

        return storage_rel_path, total_bytes

    def read_file(self, storage_key: str) -> bytes:
        # Prevent directory traversal
        target_path = (self.base_dir / storage_key).resolve()
        if not str(target_path).startswith(str(self.base_dir.resolve())):
            raise BadRequestError("Invalid storage access path.")

        if not target_path.exists():
            raise BadRequestError("File not found on storage.")

        with open(target_path, "rb") as f:
            return f.read()

    def delete_file(self, storage_key: str) -> None:
        target_path = (self.base_dir / storage_key).resolve()
        if str(target_path).startswith(str(self.base_dir.resolve())) and target_path.exists():
            target_path.unlink()
