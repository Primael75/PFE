"""Photo diagnosis (EF-15, H-T2): turn the model's probabilities into a sourced value.

Domain code: no MCP, no HTTP. The neural network sits behind the
`Classifier` protocol, so that this logic is tested without PyTorch.
"""

from collections.abc import Mapping
from datetime import date
from typing import Protocol

from agritech.core.tool_output import Source, SourcedValue

# Values returned instead of a class name. The model abstains below its
# calibrated threshold (EF-16); "off_topic" needs a trained off-topic class.
UNCERTAIN = "uncertain"
OFF_TOPIC = "off_topic"

# Name of the off-topic class in the training code.
OFF_TOPIC_CLASS = "hors_sujet"


class Classifier(Protocol):
    """Anything that gives class probabilities for the bytes of a photo."""

    name: str  # model name and version, cited as the source
    threshold: float | None  # calibrated abstention threshold, if any

    def probabilities(self, photo: bytes) -> Mapping[str, float] | None:
        """Probability of each class, or None if the bytes are not a readable image."""
        ...


def decide(
    probabilities: Mapping[str, float], threshold: float | None
) -> tuple[str, float]:
    """Label to report and the confidence of the most likely class."""
    best_class = max(probabilities, key=probabilities.__getitem__)
    confidence = probabilities[best_class]
    if best_class == OFF_TOPIC_CLASS:
        return OFF_TOPIC, confidence
    if threshold is not None and confidence < threshold:
        return UNCERTAIN, confidence
    return best_class, confidence


def diagnose_photo(
    classifier: Classifier, photo: bytes, as_of: date
) -> SourcedValue | None:
    """Suspected disease on a photo, or None if the photo cannot be read.

    The other likely classes are dropped for now: the common output format
    carries a single value.
    """
    probabilities = classifier.probabilities(photo)
    if probabilities is None:
        return None
    label, confidence = decide(probabilities, classifier.threshold)
    return SourcedValue(
        value=label,
        unit="label",
        source=Source(name=classifier.name),
        as_of=as_of,
        uncertainty=round(confidence, 4),
    )
