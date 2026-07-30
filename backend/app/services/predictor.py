"""Picks which lesion-classification backend to use at request time.

Default is the local scikit-learn model (app/services/local_predictor.py) -- no GCP
project, endpoint, or credits needed. Set PREDICTION_BACKEND=vertex to route through a
deployed Vertex AI AutoML endpoint instead (app/services/vertex_predictor.py) if one
gets provisioned again later; that path still needs VERTEX_PROJECT_ID,
VERTEX_LOCATION, VERTEX_ENDPOINT_ID, and GOOGLE_APPLICATION_CREDENTIALS set.
"""
from __future__ import annotations

import os

from PIL import Image

from app.schemas.gemini_report import ClassPrediction
from app.services import local_predictor, vertex_predictor


def classify(image: Image.Image) -> list[ClassPrediction]:
    backend = os.getenv("PREDICTION_BACKEND", "local").strip().lower()
    if backend == "vertex":
        return vertex_predictor.classify(image)
    return local_predictor.classify(image)
