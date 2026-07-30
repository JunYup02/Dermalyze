"""Classifies a skin lesion image with a local scikit-learn model loaded from a .pkl
file, instead of calling a hosted GCP Vertex AI AutoML endpoint.

The model is trained offline by scripts/train_model.py from the HAM10000 dataset and
committed to the repo at the path below (MODEL_PATH) -- there is nothing to deploy or
pay for separately; the backend just loads the file on first use.
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

import joblib
from fastapi import HTTPException
from PIL import Image

from app.ml.features import extract_features
from app.schemas.gemini_report import ClassPrediction

MODEL_PATH = Path(__file__).resolve().parent.parent / "ml_models" / "skin_lesion_model.pkl"


@lru_cache
def _load_model() -> dict[str, Any]:
    if not MODEL_PATH.exists():
        raise HTTPException(
            status_code=503,
            detail=(
                f"Classifier model not found at {MODEL_PATH}. Run "
                "backend/scripts/train_model.py to generate it."
            ),
        )
    return joblib.load(MODEL_PATH)


def classify(image: Image.Image) -> list[ClassPrediction]:
    artifact = _load_model()
    model = artifact["model"]

    features = extract_features(image).reshape(1, -1)
    try:
        probabilities = model.predict_proba(features)[0]
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Local model prediction failed: {exc}") from exc

    predictions = [
        ClassPrediction(id=class_id, name=class_id, probability=float(probability))
        for class_id, probability in zip(model.classes_, probabilities)
    ]
    predictions.sort(key=lambda p: p.probability, reverse=True)
    return predictions
