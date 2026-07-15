"""Classifier backend abstraction.

Set PREDICTOR_BACKEND=local (default) to use the demo classifier trained on
synthetic data (see ml/synthetic_data.py). Set PREDICTOR_BACKEND=vertex to
route through Vertex AI once a real HAM10000-trained model is deployed there
(see VertexAIPredictor below for the env vars it needs and what's left to
wire up).
"""
from __future__ import annotations

import os
from abc import ABC, abstractmethod
from functools import lru_cache
from pathlib import Path

import joblib
from PIL import Image

from ml.features import extract_features

ARTIFACT_PATH = Path(__file__).resolve().parent.parent / "ml" / "artifacts" / "lesion_model.joblib"


class Predictor(ABC):
    @abstractmethod
    def predict(self, image: Image.Image) -> dict[str, float]:
        """Return a {class_code: probability} dict covering all 7 classes."""


class LocalDemoPredictor(Predictor):
    def __init__(self):
        if not ARTIFACT_PATH.exists():
            raise FileNotFoundError(
                f"{ARTIFACT_PATH} not found. Run `python -m ml.train_model` from backend/ first."
            )
        self.model = joblib.load(ARTIFACT_PATH)

    def predict(self, image: Image.Image) -> dict[str, float]:
        features = extract_features(image).reshape(1, -1)
        probs = self.model.predict_proba(features)[0]
        return dict(zip(self.model.classes_, (float(p) for p in probs)))


class VertexAIPredictor(Predictor):
    """Not implemented yet.

    To wire up a real Vertex AI endpoint trained on HAM10000:
    1. Deploy the trained model to a Vertex AI endpoint.
    2. Set env vars: VERTEX_PROJECT_ID, VERTEX_LOCATION, VERTEX_ENDPOINT_ID,
       and GOOGLE_APPLICATION_CREDENTIALS (service account key path).
    3. `pip install google-cloud-aiplatform` and add it to requirements.txt.
    4. Implement predict() below: send the image (as base64 or bytes) to
       aiplatform.Endpoint(endpoint_id).predict(...) and map the response
       into a {class_code: probability} dict using the same 7 class codes
       as CLASS_ORDER in app/classes.py.
    """

    def __init__(self):
        self.project_id = os.environ["VERTEX_PROJECT_ID"]
        self.location = os.environ["VERTEX_LOCATION"]
        self.endpoint_id = os.environ["VERTEX_ENDPOINT_ID"]

    def predict(self, image: Image.Image) -> dict[str, float]:
        raise NotImplementedError(
            "Vertex AI integration is not implemented yet. See VertexAIPredictor's docstring."
        )


@lru_cache
def get_predictor() -> Predictor:
    backend = os.environ.get("PREDICTOR_BACKEND", "local")
    if backend == "vertex":
        return VertexAIPredictor()
    return LocalDemoPredictor()
