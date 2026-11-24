"""Model, preprocessing and dataset shared by training, evaluation and inference.

The preprocessing defined here (size, normalisation, RGB order, EXIF rotation)
is the contract that any client of the model must reproduce exactly. It is
also written to config.json next to the weights.
"""

from pathlib import Path

import torch
from PIL import Image, ImageOps
from torch.utils.data import Dataset
from torchvision import models, transforms

ARCH = "mobilenet_v3_large"
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)


def pick_device(name: str = "auto") -> torch.device:
    if name != "auto":
        return torch.device(name)
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_rgb(source) -> Image.Image:
    """Open a photo (path or file object), apply the EXIF rotation of phones, force RGB."""
    img = Image.open(source)
    img = ImageOps.exif_transpose(img)
    return img.convert("RGB")


def eval_transform(size: int) -> transforms.Compose:
    # Direct resize, no crop, so that a spot near the edge is not cut off.
    return transforms.Compose(
        [
            transforms.Resize((size, size)),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )


def train_transform(size: int) -> transforms.Compose:
    """Augmentation, applied to the training split ONLY."""
    return transforms.Compose(
        [
            transforms.RandomResizedCrop(size, scale=(0.6, 1.0), ratio=(0.75, 1.33)),
            transforms.RandomHorizontalFlip(),
            transforms.RandomRotation(20),
            transforms.ColorJitter(
                brightness=0.3, contrast=0.3, saturation=0.2, hue=0.02
            ),
            transforms.RandomApply(
                [transforms.GaussianBlur(5, sigma=(0.1, 1.5))], p=0.3
            ),
            transforms.ToTensor(),
            transforms.Normalize(IMAGENET_MEAN, IMAGENET_STD),
        ]
    )


class ManifestDataset(Dataset):
    """Photos listed in a manifest (rows with 'path' and 'label')."""

    def __init__(self, rows: list[dict], root: Path, classes: list[str], transform):
        self.rows, self.root, self.transform = rows, Path(root), transform
        self.cidx = {c: i for i, c in enumerate(classes)}

    def __len__(self) -> int:
        return len(self.rows)

    def __getitem__(self, i: int):
        r = self.rows[i]
        img = load_rgb(self.root / r["path"])
        return self.transform(img), self.cidx[r["label"]]


def build_model(num_classes: int, weights: str = "imagenet") -> torch.nn.Module:
    """MobileNetV3-Large with a new last layer; 'imagenet' downloads pre-trained weights."""
    w = (
        models.MobileNet_V3_Large_Weights.IMAGENET1K_V2
        if weights == "imagenet"
        else None
    )
    m = models.mobilenet_v3_large(weights=w)
    m.classifier[3] = torch.nn.Linear(m.classifier[3].in_features, num_classes)
    return m


@torch.no_grad()
def predict_logits(model: torch.nn.Module, loader, device: torch.device):
    model.eval()
    outs, labels = [], []
    for x, y in loader:
        outs.append(model(x.to(device)).cpu())
        labels.append(y)
    return torch.cat(outs), torch.cat(labels)


def load_checkpoint(path: Path, device: torch.device) -> tuple[torch.nn.Module, dict]:
    # weights_only: the checkpoint holds tensors and plain values, never code to run.
    ck = torch.load(path, map_location=device, weights_only=True)
    model = build_model(len(ck["classes"]), weights="none")
    model.load_state_dict(ck["state_dict"])
    return model.to(device).eval(), ck
