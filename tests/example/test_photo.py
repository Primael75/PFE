import struct
import zlib

import httpx2
import pytest
from fastmcp import Client

from agritech.example import photo_mcp_server
from agritech.example.photo import inspect_photo_bytes
from agritech.example.photo_source import DirectoryPhotoSource, KnowledgeFlowPhotoSource


def make_png(width: int, height: int) -> bytes:
    def chunk(kind: bytes, payload: bytes) -> bytes:
        body = kind + payload
        return (
            struct.pack(">I", len(payload)) + body + struct.pack(">I", zlib.crc32(body))
        )

    header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    pixels = zlib.compress(b"\x00" + b"\x00\x00\x00" * width) * height
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", header)
        + chunk(b"IDAT", pixels)
        + chunk(b"IEND", b"")
    )


def make_jpeg(width: int, height: int) -> bytes:
    # Start of image, an APP0 segment, then a start-of-frame segment with the size.
    app0 = b"\xff\xe0" + struct.pack(">H", 16) + b"JFIF\x00" + b"\x00" * 9
    sof = b"\xff\xc0" + struct.pack(">HBHH", 11, 8, height, width) + b"\x01\x01\x11\x00"
    return b"\xff\xd8" + app0 + sof + b"\xff\xd9"


def test_domain_reads_a_png():
    info = inspect_photo_bytes(make_png(4, 3))
    assert (info.format, info.width, info.height) == ("PNG", 4, 3)


def test_domain_reads_a_jpeg():
    info = inspect_photo_bytes(make_jpeg(640, 480))
    assert (info.format, info.width, info.height) == ("JPEG", 640, 480)


def test_domain_rejects_other_files():
    assert inspect_photo_bytes(b"%PDF-1.7 not a photo") is None


@pytest.fixture
def photo_dir(tmp_path, monkeypatch):
    (tmp_path / "doc-1").write_bytes(make_jpeg(640, 480))
    (tmp_path / "doc-2").write_bytes(b"%PDF-1.7 not a photo")
    monkeypatch.setattr(photo_mcp_server, "source", DirectoryPhotoSource(tmp_path))
    return tmp_path


@pytest.mark.anyio
async def test_tool_returns_the_photo_size(photo_dir):
    async with Client(photo_mcp_server.mcp) as client:
        result = await client.call_tool("inspect_photo", {"document_uid": "doc-1"})
    assert result.structured_content["value"].startswith("JPEG 640x480")


@pytest.mark.anyio
@pytest.mark.parametrize("uid", ["doc-2", "unknown", "../doc-1"])
async def test_tool_reports_missing_or_invalid_photos(photo_dir, uid):
    async with Client(photo_mcp_server.mcp) as client:
        result = await client.call_tool(
            "inspect_photo", {"document_uid": uid}, raise_on_error=False
        )
    assert result.is_error


@pytest.mark.anyio
async def test_knowledge_flow_source_forwards_bearer_and_grant():
    seen = {}

    def handler(request: httpx2.Request) -> httpx2.Response:
        seen["url"] = str(request.url)
        seen["authorization"] = request.headers.get("authorization")
        return httpx2.Response(200, content=b"photo bytes")

    kf = KnowledgeFlowPhotoSource(
        "http://kf/knowledge-flow/v1/", httpx2.MockTransport(handler)
    )
    grant = {"person": "p1", "run": "r1", "agent": "a1", "other": "dropped"}
    data = await kf.fetch("doc-1", "Bearer token", grant)

    assert data == b"photo bytes"
    assert seen["authorization"] == "Bearer token"
    assert seen["url"] == (
        "http://kf/knowledge-flow/v1/raw_content/doc-1?person=p1&run=r1&agent=a1"
    )


@pytest.mark.anyio
async def test_knowledge_flow_source_returns_none_when_not_found():
    kf = KnowledgeFlowPhotoSource(
        "http://kf", httpx2.MockTransport(lambda _: httpx2.Response(404))
    )
    assert await kf.fetch("doc-1", None, {}) is None
