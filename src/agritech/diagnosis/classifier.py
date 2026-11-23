"""The trained diagnosis network (MobileNetV3), behind the `Classifier` protocol.

Preprocessing must match training exactly: EXIF rotation, RGB, direct resize
to a square (no crop, so that a spot on the border is kept), ImageNet
normalisation. PyTorch is imported on first use, so that the rest of the
brick and its tests run without it.
"""

import io
import json
import logging
from collections.abc import Mapping
from pathlib import Path

logger = logging.getLogger(__name__)

IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

# Weights shipped with the brick; AGRITECH_DIAGNOSIS_MODEL can point elsewhere.
DEFAULT_MODEL = Path(__file__).resolve().parent / "weights" / "best.pt"


class TorchClassifier:
    """Loads the checkpoint once and runs it on CPU."""

    def __init__(self, model_path: Path = DEFAULT_MODEL):
        import torch
        from torchvision import models, transforms

        # weights_only refuses arbitrary pickled objects: the checkpoint only
        # needs tensors, the class list and the image size.
        checkpoint = torch.load(model_path, map_location="cpu", weights_only=True)
        self.classes: list[str] = list(checkpoint["classes"])
        network = models.mobilenet_v3_large(weights=None)
        network.classifier[3] = torch.nn.Linear(
            network.classifier[3].in_features, len(self.classes)
        )
        network.load_state_dict(checkpoint["state_dict"])
        self._network = network.eval()
        size = int(checkpoint["img_size"])
        self._transform = transforms.Compose(
            [
                transforms.Resize((size, size)),
                transforms.ToTensor(),
                transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
            ]
        )
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
        from PIL import Image, ImageOps, UnidentifiedImageError

        try:
            image = ImageOps.exif_transpose(Image.open(io.BytesIO(photo))).convert(
                "RGB"
            )
        except (UnidentifiedImageError, OSError, ValueError):
            return None
        batch = self._transform(image).unsqueeze(0)
        with self._torch.no_grad():
            scores = self._network(batch)[0]
        probabilities = self._torch.softmax(scores / self._temperature, dim=0)
        return dict(zip(self.classes, probabilities.tolist(), strict=True))
