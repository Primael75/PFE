"""The trained diagnosis network, served behind the `Classifier` protocol.

Loading and preprocessing come from `model.py`, the contract shared with
training: the server must prepare a photo exactly as training did. PyTorch is
imported on first use, so that the rest of the brick and its tests run
without it.
"""

import io
import json
import logging
from collections.abc import Mapping
from pathlib import Path

logger = logging.getLogger(__name__)

# Downloaded next to the brick, out of Git; AGRITECH_DIAGNOSIS_MODEL can override.
DEFAULT_MODEL = Path(__file__).resolve().parent / "weights" / "best.pt"


class TorchClassifier:
    """Loads the checkpoint once and runs it on CPU."""

    def __init__(self, model_path: Path = DEFAULT_MODEL):
        import torch

        from agritech.diagnosis.model import eval_transform, load_checkpoint

        self._network, checkpoint = load_checkpoint(model_path, torch.device("cpu"))
        self.classes: list[str] = list(checkpoint["classes"])
        self._transform = eval_transform(int(checkpoint["img_size"]))
        self._torch = torch

        # Calibration (temperature and abstention threshold) is computed on the
        # validation set and saved next to the weights; without it the model
        # never abstains.
        calibration_path = model_path.parent / "calibration.json"
        calibration = (
            json.loads(calibration_path.read_text(encoding="utf-8"))
            if calibration_path.exists()
            else {}
        )
        self._temperature = float(calibration.get("temperature", 1.0))
        self.threshold: float | None = calibration.get("threshold")
        if self.threshold is None:
            logger.warning(
                "No calibration.json next to %s: the model never abstains", model_path
            )
        self.name = (
            f"Agritech diagnosis model ({model_path.name}, {len(self.classes)} classes)"
        )

    def probabilities(self, photo: bytes) -> Mapping[str, float] | None:
        from PIL import UnidentifiedImageError

        from agritech.diagnosis.model import load_rgb

        try:
            image = load_rgb(io.BytesIO(photo))
        except (UnidentifiedImageError, OSError, ValueError):
            return None
        batch = self._transform(image).unsqueeze(0)
        with self._torch.no_grad():
            scores = self._network(batch)[0]
        probabilities = self._torch.softmax(scores / self._temperature, dim=0)
        return dict(zip(self.classes, probabilities.tolist(), strict=True))
