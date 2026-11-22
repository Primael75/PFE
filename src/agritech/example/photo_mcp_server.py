"""Photo example (H-T4): an MCP tool that receives a photo sent in Fred.

Configuration, by environment variable:
- AGRITECH_KF_BASE_URL: Knowledge Flow address, for example
  http://knowledge-flow-backend:8111/knowledge-flow/v1 (in Fred);
- AGRITECH_PHOTO_DIR: a local folder of photos, used instead (tests, measures).
"""

import logging
import os
import time
from collections.abc import Mapping
from datetime import date
from pathlib import Path

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_request
from fastmcp.tools import ToolResult

from agritech.core.logging_config import configure_logging
from agritech.core.tool_output import Source, SourcedValue, missing_data, to_tool_result
from agritech.example.photo import inspect_photo_bytes
from agritech.example.photo_source import (
    GRANT_PARAMS,
    DirectoryPhotoSource,
    KnowledgeFlowPhotoSource,
    PhotoSource,
)

logger = logging.getLogger(__name__)

mcp = FastMCP(name="agritech-photo-example")

# Replaced by the tests; otherwise built from the environment on first call.
source: PhotoSource | None = None


def _get_source() -> PhotoSource:
    global source
    if source is None:
        if os.environ.get("AGRITECH_PHOTO_DIR"):
            source = DirectoryPhotoSource(Path(os.environ["AGRITECH_PHOTO_DIR"]))
        elif os.environ.get("AGRITECH_KF_BASE_URL"):
            source = KnowledgeFlowPhotoSource(os.environ["AGRITECH_KF_BASE_URL"])
        else:
            raise RuntimeError("Set AGRITECH_KF_BASE_URL or AGRITECH_PHOTO_DIR")
    return source


def _caller_credentials() -> tuple[str | None, Mapping[str, str]]:
    # Over HTTP, Fred sends a bearer and the delegation grant in the query
    # string. In stdio or in memory there is no HTTP request.
    try:
        request = get_http_request()
    except RuntimeError:
        return None, {}
    grant = {
        name: request.query_params[name]
        for name in GRANT_PARAMS
        if name in request.query_params
    }
    return request.headers.get("authorization"), grant


@mcp.tool
async def inspect_photo(document_uid: str) -> ToolResult:
    """Format and size of a photo attached in the conversation.

    Pass the document uid shown next to the attached file, never its name.
    Demo tool for H-T4: it gives no diagnosis.
    """
    started = time.perf_counter()
    authorization, grant = _caller_credentials()
    data = await _get_source().fetch(document_uid, authorization, grant)
    if data is None:
        return missing_data(f"No photo found for document {document_uid}.")
    info = inspect_photo_bytes(data)
    if info is None:
        return missing_data(f"Document {document_uid} is not a JPEG or PNG photo.")
    logger.info(
        "inspect_photo read %s (%d bytes) in %.0f ms",
        document_uid,
        info.size_bytes,
        (time.perf_counter() - started) * 1000,
    )
    return to_tool_result(
        SourcedValue(
            value=f"{info.format} {info.width}x{info.height}, {info.size_bytes} bytes",
            unit="label",
            source=Source(name=f"Photo attached in Fred (document {document_uid})"),
            as_of=date.today(),  # the upload date is not known to the tool
        )
    )


def create_app():
    """Build the HTTP application served by uvicorn, as Fred will call it."""
    configure_logging()
    return mcp.http_app(path="/mcp", stateless_http=True, json_response=True)


if __name__ == "__main__":
    configure_logging()
    mcp.run()
