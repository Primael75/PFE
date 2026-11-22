"""Where the photo example reads a photo from.

In Fred, a photo attached in the chat is uploaded to Knowledge Flow. The
agent never sees its bytes: it receives a document uid and passes it to
the tool. The tool then downloads the original bytes from Knowledge
Flow (`GET /raw_content/{document_uid}`).
"""

import logging
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

import httpx2

logger = logging.getLogger(__name__)

# Query parameters of a Fred delegation grant: the person, run and agent a
# call acts for (fred_core.security.delegation.GRANT_PARAM_NAMES).
GRANT_PARAMS = ("person", "run", "agent")


class PhotoSource(Protocol):
    """Anything that returns the bytes of a photo from its document uid."""

    async def fetch(
        self, document_uid: str, authorization: str | None, grant: Mapping[str, str]
    ) -> bytes | None: ...


class KnowledgeFlowPhotoSource:
    """Downloads the original photo from Fred's Knowledge Flow.

    H-T4 demo only: it forwards the bearer and the grant received by the
    tool. The next version of the template will use the server's own
    service identity instead (see the README).
    """

    def __init__(
        self, base_url: str, transport: httpx2.AsyncBaseTransport | None = None
    ):
        self._base_url = base_url.rstrip("/")
        self._transport = transport

    async def fetch(
        self, document_uid: str, authorization: str | None, grant: Mapping[str, str]
    ) -> bytes | None:
        headers = {"Authorization": authorization} if authorization else {}
        params = {name: grant[name] for name in GRANT_PARAMS if name in grant}
        async with httpx2.AsyncClient(transport=self._transport, timeout=30) as client:
            response = await client.get(
                f"{self._base_url}/raw_content/{document_uid}",
                headers=headers,
                params=params,
            )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        return response.content


class DirectoryPhotoSource:
    """Reads photos from a local folder, the file name being the uid (tests, measures)."""

    def __init__(self, root: Path):
        self._root = root.resolve()

    async def fetch(
        self, document_uid: str, authorization: str | None, grant: Mapping[str, str]
    ) -> bytes | None:
        path = (self._root / document_uid).resolve()
        # Refuse a uid such as "../secret" that would leave the folder.
        if path.parent != self._root or not path.is_file():
            return None
        return path.read_bytes()
