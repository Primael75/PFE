from collections.abc import Mapping
from datetime import date

import pytest
from fastmcp import Client

from agritech.diagnosis import mcp_server
from agritech.diagnosis.diagnosis import (
    OFF_TOPIC,
    OFF_TOPIC_CLASS,
    UNCERTAIN,
    decide,
    diagnose_photo,
)
from agritech.example.photo_source import DirectoryPhotoSource

AS_OF = date(2026, 11, 23)


class FakeClassifier:
    """Returns fixed probabilities; any bytes starting with 'photo' are readable."""

    name = "Fake diagnosis model"

    def __init__(
        self, probabilities: Mapping[str, float], threshold: float | None = 0.6
    ):
        self._probabilities = probabilities
        self.threshold = threshold

    def probabilities(self, photo: bytes) -> Mapping[str, float] | None:
        return self._probabilities if photo.startswith(b"photo") else None


CONFIDENT = {"cassava_mosaic": 0.91, "maize_healthy": 0.06, "tomato_leaf_curl": 0.03}
UNSURE = {"cassava_brown_spot": 0.41, "cassava_mosaic": 0.39, "maize_healthy": 0.2}


def test_decide_returns_the_most_likely_class():
    assert decide(CONFIDENT, threshold=0.6) == ("cassava_mosaic", 0.91)


def test_decide_abstains_below_the_threshold():
    assert decide(UNSURE, threshold=0.6) == (UNCERTAIN, 0.41)


def test_decide_never_abstains_without_calibration():
    assert decide(UNSURE, threshold=None) == ("cassava_brown_spot", 0.41)


def test_decide_reports_off_topic_photos():
    assert decide({OFF_TOPIC_CLASS: 0.8, "maize_healthy": 0.2}, 0.6) == (OFF_TOPIC, 0.8)


def test_domain_returns_a_sourced_label():
    result = diagnose_photo(FakeClassifier(CONFIDENT), b"photo", AS_OF)
    assert (result.value, result.unit, result.uncertainty) == (
        "cassava_mosaic",
        "label",
        0.91,
    )
    assert result.source.name == "Fake diagnosis model"
    assert result.as_of == AS_OF


def test_domain_returns_none_for_unreadable_photos():
    assert diagnose_photo(FakeClassifier(CONFIDENT), b"%PDF-1.7", AS_OF) is None


@pytest.fixture
def server(tmp_path, monkeypatch):
    (tmp_path / "doc-1").write_bytes(b"photo of a leaf")
    (tmp_path / "doc-2").write_bytes(b"%PDF-1.7 not a photo")
    monkeypatch.setattr(mcp_server, "source", DirectoryPhotoSource(tmp_path))

    def use(probabilities):
        monkeypatch.setattr(mcp_server, "classifier", FakeClassifier(probabilities))

    use(CONFIDENT)
    return use


@pytest.mark.anyio
async def test_tool_is_declared_with_a_document_uid(server):
    async with Client(mcp_server.mcp) as client:
        tools = {tool.name: tool for tool in await client.list_tools()}
    assert list(tools["diagnose_photo"].input_schema["properties"]) == ["document_uid"]


@pytest.mark.anyio
async def test_tool_returns_the_diagnosis(server):
    async with Client(mcp_server.mcp) as client:
        result = await client.call_tool("diagnose_photo", {"document_uid": "doc-1"})
    assert result.structured_content["value"] == "cassava_mosaic"
    assert result.structured_content["uncertainty"] == 0.91
    # The model reads the text, which must carry the source and the confidence.
    assert "Fake diagnosis model" in result.content[0].text
    assert "confidence 91%" in result.content[0].text


@pytest.mark.anyio
async def test_tool_reports_uncertain_photos(server):
    server(UNSURE)
    async with Client(mcp_server.mcp) as client:
        result = await client.call_tool("diagnose_photo", {"document_uid": "doc-1"})
    assert result.structured_content["value"] == UNCERTAIN


@pytest.mark.anyio
@pytest.mark.parametrize("uid", ["doc-2", "unknown", "../doc-1"])
async def test_tool_reports_missing_or_unreadable_photos(server, uid):
    async with Client(mcp_server.mcp) as client:
        result = await client.call_tool(
            "diagnose_photo", {"document_uid": uid}, raise_on_error=False
        )
    assert result.is_error


def test_torch_classifier_matches_the_training_contract(tmp_path):
    """Real network, random weights: runs only where PyTorch is installed."""
    torch = pytest.importorskip("torch")
    pytest.importorskip("torchvision")
    import io

    from PIL import Image

    from agritech.diagnosis.classifier import TorchClassifier
    from agritech.diagnosis.model import build_model

    classes = ["cassava_mosaic", "maize_healthy", "tomato_leaf_curl"]
    network = build_model(len(classes), weights="none")
    path = tmp_path / "best.pt"
    torch.save(
        {"classes": classes, "img_size": 224, "state_dict": network.state_dict()}, path
    )
    (tmp_path / "calibration.json").write_text('{"temperature": 1.5, "threshold": 0.6}')

    classifier = TorchClassifier(path)
    photo = io.BytesIO()
    Image.new("RGB", (640, 480), (40, 120, 40)).save(photo, format="JPEG")
    probabilities = classifier.probabilities(photo.getvalue())

    assert list(probabilities) == classes
    assert sum(probabilities.values()) == pytest.approx(1.0, abs=1e-5)
    assert classifier.threshold == 0.6
    assert classifier.probabilities(b"%PDF-1.7 not a photo") is None
