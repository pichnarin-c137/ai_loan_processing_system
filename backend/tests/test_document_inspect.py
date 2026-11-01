import asyncio
import io
from collections.abc import AsyncIterator
from typing import Any

import pytest
from fastapi import HTTPException
from PIL import Image
from pypdf import PdfWriter

from app.models.enums import Stage
from app.services import documents as docs
from app.services.applications import customer_status


def make_pdf(
    pages: int = 1, *, password: str | None = None, owner_password: str | None = None
) -> bytes:
    writer = PdfWriter()
    for _ in range(pages):
        writer.add_blank_page(width=100, height=100)
    if password:
        writer.encrypt(password)
    if owner_password:
        writer.encrypt(user_password="", owner_password=owner_password)
    out = io.BytesIO()
    writer.write(out)
    return out.getvalue()


def make_image(fmt: str, size: tuple[int, int] = (20, 20)) -> bytes:
    out = io.BytesIO()
    Image.new("RGB", size, "white").save(out, format=fmt)
    return out.getvalue()


def detail_of(error: HTTPException) -> Any:
    return error.detail


def run_inspect(data: bytes) -> tuple[str, int]:
    return docs.inspect(io.BytesIO(data))


def error_of(data: bytes) -> HTTPException:
    with pytest.raises(HTTPException) as info:
        run_inspect(data)
    return info.value


@pytest.mark.parametrize(
    ("data", "expected"),
    [
        (make_pdf(1), ("application/pdf", 1)),
        (make_pdf(3), ("application/pdf", 3)),
        (make_image("JPEG"), ("image/jpeg", 1)),
        (make_image("PNG"), ("image/png", 1)),
    ],
)
def test_valid_files(data: bytes, expected: tuple[str, int]) -> None:
    assert run_inspect(data) == expected


def test_gif_and_text_are_unsupported() -> None:
    for data in (make_image("GIF"), b"hello world, not a file"):
        err = error_of(data)
        assert err.status_code == 415
        assert detail_of(err) == {"code": "unsupported_file_type"}


def test_corrupt_pdf() -> None:
    err = error_of(b"%PDF-1.7 this is not really a pdf")
    assert (err.status_code, detail_of(err)) == (422, {"code": "unreadable_file"})


def test_encrypted_pdf() -> None:
    err = error_of(make_pdf(1, password="secret"))
    assert (err.status_code, detail_of(err)) == (422, {"code": "encrypted_pdf"})


def test_owner_password_only_pdf_is_accepted() -> None:
    assert run_inspect(make_pdf(2, owner_password="owner")) == ("application/pdf", 2)


def test_pdf_parser_crash_is_unreadable(monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_args: Any, **_kwargs: Any) -> None:
        raise IndexError("broken")

    monkeypatch.setattr(docs, "PdfReader", boom)
    err = error_of(make_pdf(1))
    assert (err.status_code, detail_of(err)) == (422, {"code": "unreadable_file"})


def test_mpo_jpeg_is_accepted() -> None:
    out = io.BytesIO()
    first = Image.new("RGB", (20, 20), "white")
    first.save(out, "MPO", save_all=True, append_images=[Image.new("RGB", (20, 20), "black")])
    assert run_inspect(out.getvalue()) == ("image/jpeg", 1)


def test_too_many_pages() -> None:
    err = error_of(make_pdf(31))
    assert (err.status_code, detail_of(err)) == (422, {"code": "too_many_pages"})


def test_image_bomb() -> None:
    err = error_of(make_image("PNG", (10000, 10000)))
    assert (err.status_code, detail_of(err)) == (422, {"code": "unreadable_file"})


def test_pixel_limit_does_not_touch_pillow_global(monkeypatch: pytest.MonkeyPatch) -> None:
    before = Image.MAX_IMAGE_PIXELS
    monkeypatch.setattr(docs, "MAX_IMAGE_PIXELS", 100)
    err = error_of(make_image("PNG", (20, 20)))
    assert (err.status_code, detail_of(err)) == (422, {"code": "unreadable_file"})
    assert before == Image.MAX_IMAGE_PIXELS


def test_truncated_jpeg() -> None:
    data = make_image("JPEG", (200, 200))
    err = error_of(data[: len(data) // 2])
    assert (err.status_code, detail_of(err)) == (422, {"code": "unreadable_file"})


class FakeRequest:
    def __init__(self, chunks: list[bytes], headers: dict[str, str] | None = None) -> None:
        self.headers = headers or {}
        self.chunks = chunks
        self.sent = 0

    async def stream(self) -> AsyncIterator[bytes]:
        for chunk in self.chunks:
            self.sent += 1
            yield chunk


def read(request: FakeRequest) -> Any:
    return asyncio.run(docs.read_body(request))


def test_read_body_rejects_declared_size_without_reading() -> None:
    request = FakeRequest([b"x"], {"content-length": str(docs.MAX_UPLOAD_BYTES + 1)})
    with pytest.raises(HTTPException) as info:
        read(request)
    assert info.value.status_code == 413
    assert request.sent == 0


def test_read_body_stops_streaming_over_the_limit() -> None:
    chunk = b"x" * (1024 * 1024)
    request = FakeRequest([chunk] * 20)
    with pytest.raises(HTTPException) as info:
        read(request)
    assert info.value.status_code == 413
    assert detail_of(info.value) == {"code": "file_too_large", "max_bytes": docs.MAX_UPLOAD_BYTES}
    assert request.sent == 11


def test_read_body_hash_and_size() -> None:
    file, digest, size = read(FakeRequest([b"hel", b"lo"]))
    assert size == 5
    assert digest == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert file.read() == b"hello"
    file.close()


def test_read_body_empty() -> None:
    with pytest.raises(HTTPException) as info:
        read(FakeRequest([]))
    assert (info.value.status_code, detail_of(info.value)) == (422, {"code": "unreadable_file"})


def test_customer_status_covers_every_stage() -> None:
    for stage in Stage:
        assert customer_status(stage)
