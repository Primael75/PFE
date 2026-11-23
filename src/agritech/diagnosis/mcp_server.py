"""Diagnosis MCP server (case A): the photo diagnosis tool, as Fred calls it.

Configuration, by environment variable:
- AGRITECH_KF_BASE_URL: Knowledge Flow address, to read photos attached in Fred;
- AGRITECH_PHOTO_DIR: a local folder of photos, used instead (tests, measures);
- AGRITECH_DIAGNOSIS_MODEL: path of the weights (default: the brick's weights/best.pt).
"""

import asyncio
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
from agritech.core.tool_output import missing_data, to_tool_result
from agritech.diagnosis import diagnosis
from agritech.diagnosis.diagnosis import Classifier
from agritech.example.photo_source import (
    GRANT_PARAMS,
    DirectoryPhotoSource,
    KnowledgeFlowPhotoSource,
    PhotoSource,
)

logger = logging.getLogger(__name__)

mcp = FastMCP(name="agritech-diagnosis")

# Replaced by the tests; otherwise built from the environment on first use.
source: PhotoSource | None = None
classifier: Classifier | None = None


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


def _get_classifier() -> Classifier:
    global classifier
    if classifier is None:
        # Imported here: PyTorch is only needed when the real model runs.
        from agritech.diagnosis.classifier import DEFAULT_MODEL, TorchClassifier

        path = Path(os.environ.get("AGRITECH_DIAGNOSIS_MODEL", DEFAULT_MODEL))
        started = time.perf_counter()
        classifier = TorchClassifier(path)
        logger.info("Model loaded in %.1f s: %s", time.perf_counter() - started, path)
    return classifier


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


@mcp.tool(name="diagnose_photo")
async def diagnose_photo(document_uid: str) -> ToolResult:
    """Suspected disease or pest on a photo of a cashew, cassava, maize or tomato leaf.

    Pass the document uid shown next to the attached photo, never its name.
    Returns a class name with its confidence, "uncertain" when the model is
    not confident enough, or "off_topic" when the photo is not one of these
    leaves. The result is a suspicion, always to be confirmed by a technician.
    """
    started = time.perf_counter()
    authorization, grant = _caller_credentials()
    data = await _get_source().fetch(document_uid, authorization, grant)
    if data is None:
        return missing_data(f"No photo found for document {document_uid}.")
    # Inference is CPU-bound: run it in a thread so the server stays responsive.
    result = await asyncio.to_thread(
        diagnosis.diagnose_photo, _get_classifier(), data, date.today()
    )
    if result is None:
        return missing_data(f"Document {document_uid} is not a readable photo.")
    logger.info(
        "diagnose_photo %s: %s (%.2f) in %.0f ms",
        document_uid,
        result.value,
        result.uncertainty,
        (time.perf_counter() - started) * 1000,
    )
    return to_tool_result(result)


def create_app():
    """Build the HTTP application served by uvicorn, as Fred will call it."""
    configure_logging()
    _get_classifier()  # load the model at startup, not on the first user's photo
    return mcp.http_app(path="/mcp", stateless_http=True, json_response=True)


if __name__ == "__main__":
    configure_logging()
    mcp.run()
