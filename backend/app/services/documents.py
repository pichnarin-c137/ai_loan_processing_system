import hashlib
import io
from tempfile import SpooledTemporaryFile
from typing import IO, Any

from fastapi import HTTPException
from PIL import Image, UnidentifiedImageError
from pypdf import PasswordType, PdfReader

MAX_UPLOAD_BYTES = 10 * 1024 * 1024
MAX_PDF_PAGES = 30
MAX_IMAGE_PIXELS = 50_000_000
_SPOOL_BYTES = 1024 * 1024

_PDF = b"%PDF-"
_JPEG = b"\xff\xd8\xff"
_PNG = b"\x89PNG\r\n\x1a\n"


def _unreadable() -> HTTPException:
    return HTTPException(422, detail={"code": "unreadable_file"})


def _too_large() -> HTTPException:
    return HTTPException(413, detail={"code": "file_too_large", "max_bytes": MAX_UPLOAD_BYTES})


async def read_body(request: Any) -> tuple[SpooledTemporaryFile[bytes], str, int]:
    declared = request.headers.get("content-length")
    if declared is not None and declared.isdigit() and int(declared) > MAX_UPLOAD_BYTES:
        raise _too_large()
    file: SpooledTemporaryFile[bytes] = SpooledTemporaryFile(max_size=_SPOOL_BYTES)  # noqa: SIM115
    digest = hashlib.sha256()
    size = 0
    try:
        async for chunk in request.stream():
            size += len(chunk)
            if size > MAX_UPLOAD_BYTES:
                raise _too_large()
            digest.update(chunk)
            file.write(chunk)
        if size == 0:
            raise _unreadable()
    except BaseException:
        file.close()
        raise
    file.seek(0)
    return file, digest.hexdigest(), size


def inspect(file: IO[bytes]) -> tuple[str, int]:
    file.seek(0)
    head = file.read(8)
    file.seek(0)
    if head.startswith(_PDF):
        return "application/pdf", _pdf_pages(file)
    if head.startswith(_JPEG):
        _check_image(file, {"JPEG", "MPO"})
        return "image/jpeg", 1
    if head.startswith(_PNG):
        _check_image(file, {"PNG"})
        return "image/png", 1
    raise HTTPException(415, detail={"code": "unsupported_file_type"})


def _pdf_pages(file: IO[bytes]) -> int:
    try:
        reader = PdfReader(file)
        # Owner-password-only PDFs open without a prompt; only a user password blocks us.
        if reader.is_encrypted and reader.decrypt("") == PasswordType.NOT_DECRYPTED:
            raise HTTPException(422, detail={"code": "encrypted_pdf"})
        pages = len(reader.pages)
    except HTTPException:
        raise
    except Exception:  # noqa: BLE001
        # The file is untrusted: any parser failure means it is unreadable.
        raise _unreadable() from None
    if pages > MAX_PDF_PAGES:
        raise HTTPException(422, detail={"code": "too_many_pages"})
    if pages == 0:
        raise _unreadable()
    return pages


def _check_image(file: IO[bytes], allowed_formats: set[str]) -> None:
    data = file.read()
    file.seek(0)
    try:
        with Image.open(io.BytesIO(data)) as image:
            if image.format not in allowed_formats:
                raise _unreadable()
            # Pillow has only read the header here, so refuse oversized images before decoding.
            if image.width * image.height > MAX_IMAGE_PIXELS:
                raise _unreadable()
            image.verify()
        with Image.open(io.BytesIO(data)) as image:
            image.load()
    except HTTPException:
        raise
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        ValueError,
        EOFError,
    ):
        raise _unreadable() from None
