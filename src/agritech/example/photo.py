"""Domain of the photo example (H-T4): read a photo's format and size.

No model and no diagnosis: the point is to prove that the tool receives
the real bytes of the photo sent in Fred.
"""

import struct
from dataclasses import dataclass

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
# JPEG "start of frame" markers carry the size; C4, C8 and CC are other segments.
_JPEG_SOF_MARKERS = {0xC0 + n for n in range(16)} - {0xC4, 0xC8, 0xCC}


@dataclass(frozen=True)
class PhotoInfo:
    """What the tool can tell about a photo without a model."""

    format: str
    width: int
    height: int
    size_bytes: int


def inspect_photo_bytes(data: bytes) -> PhotoInfo | None:
    """Format and size of a JPEG or PNG photo, or None if it is neither."""
    if data.startswith(_PNG_SIGNATURE) and len(data) >= 24:
        width, height = struct.unpack(">II", data[16:24])
        return PhotoInfo("PNG", width, height, len(data))
    if data.startswith(b"\xff\xd8"):
        size = _jpeg_size(data)
        if size is not None:
            return PhotoInfo("JPEG", size[0], size[1], len(data))
    return None


def _jpeg_size(data: bytes) -> tuple[int, int] | None:
    # Walk the segments: each starts with FF, a marker byte, then a 2-byte length.
    position = 2
    while position + 9 <= len(data):
        if data[position] != 0xFF:
            return None
        marker = data[position + 1]
        if marker == 0xFF:  # padding byte
            position += 1
            continue
        length = struct.unpack(">H", data[position + 2 : position + 4])[0]
        if marker in _JPEG_SOF_MARKERS:
            height, width = struct.unpack(">HH", data[position + 5 : position + 9])
            return width, height
        position += 2 + length
    return None
