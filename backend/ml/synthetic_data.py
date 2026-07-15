"""Synthetic labeled feature vectors used to train the demo classifier.

There is no HAM10000 / Vertex AI access available for this demo, so instead
of training on real lesion images we simulate class-conditional distributions
over the FEATURE_ORDER feature space (see features.py), loosely informed by
the dermoscopic ABCD rule and each class's typical appearance. Deliberate
overlap between classes keeps the resulting classifier probabilistic rather
than perfectly separable, like a real-world model would be. This is NOT
trained on real dermoscopy data and must not be used for medical decisions.
"""
from __future__ import annotations

import numpy as np

from ml.features import FEATURE_ORDER

assert FEATURE_ORDER == [
    "asymmetry_score", "border_irregularity", "color_variance",
    "diameter_ratio", "red_dominance", "mean_darkness",
]

# mean, std per feature, per class.
CLASS_PARAMS = {
    #           asymmetry     border        color        diameter      red_dom       darkness
    "akiec": [(0.45, 0.12), (0.50, 0.12), (0.45, 0.12), (0.25, 0.08), (0.25, 0.15), (0.45, 0.12)],
    "bcc":   [(0.30, 0.12), (0.50, 0.12), (0.25, 0.10), (0.20, 0.08), (0.30, 0.15), (0.30, 0.12)],
    "bkl":   [(0.25, 0.10), (0.35, 0.12), (0.45, 0.12), (0.30, 0.10), (0.05, 0.12), (0.50, 0.12)],
    "df":    [(0.15, 0.08), (0.20, 0.10), (0.20, 0.10), (0.12, 0.06), (0.05, 0.12), (0.40, 0.12)],
    "mel":   [(0.65, 0.12), (0.70, 0.12), (0.70, 0.12), (0.40, 0.12), (-0.05, 0.15), (0.60, 0.12)],
    "nv":    [(0.15, 0.10), (0.20, 0.10), (0.25, 0.10), (0.18, 0.08), (0.00, 0.12), (0.40, 0.12)],
    "vasc":  [(0.15, 0.10), (0.20, 0.10), (0.30, 0.12), (0.12, 0.06), (0.55, 0.15), (0.15, 0.10)],
}

FEATURE_BOUNDS = [(0, 1), (0, 1), (0, 1), (0, 1), (-1, 1), (0, 1)]

# HAM10000 is heavily imbalanced toward nv (~67%); mirror that so the demo
# model reflects realistic class priors instead of a uniform prior.
CLASS_WEIGHTS = {
    "akiec": 0.03, "bcc": 0.05, "bkl": 0.11, "df": 0.01,
    "mel": 0.11, "nv": 0.67, "vasc": 0.02,
}


def generate_dataset(n: int = 6000, seed: int = 7):
    rng = np.random.default_rng(seed)
    classes = list(CLASS_PARAMS.keys())
    weights = np.array([CLASS_WEIGHTS[c] for c in classes])
    labels = rng.choice(classes, size=n, p=weights / weights.sum())

    X = np.empty((n, len(FEATURE_ORDER)))
    for i, label in enumerate(labels):
        params = CLASS_PARAMS[label]
        row = [rng.normal(mean, std) for mean, std in params]
        row = [np.clip(v, lo, hi) for v, (lo, hi) in zip(row, FEATURE_BOUNDS)]
        X[i] = row

    return X, labels
