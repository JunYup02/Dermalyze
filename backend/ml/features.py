"""Simple, dependency-light image features used as a stand-in for the ABCD
dermoscopy rule (Asymmetry, Border irregularity, Color variation, Diameter),
plus two color cues that help separate vascular/inflamed lesions.

This is NOT a validated dermoscopic feature extractor. It assumes the lesion
is roughly centered and darker than the surrounding skin, which holds for a
lot of casual lesion photos but not all. Good enough for a demo classifier;
a real deployment should extract features from a trained CNN backbone (or
call Vertex AI directly) instead.
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from scipy import ndimage

FEATURE_ORDER = [
    "asymmetry_score",
    "border_irregularity",
    "color_variance",
    "diameter_ratio",
    "red_dominance",
    "mean_darkness",
]

FEATURE_SIZE = 128


def _lesion_mask(gray: np.ndarray) -> np.ndarray:
    """Pixels darker than one std below the mean are treated as lesion."""
    threshold = gray.mean() - 0.5 * gray.std()
    mask = gray < threshold
    if mask.sum() < 16:
        # Fall back to the darkest 15% of pixels so the mask is never empty.
        threshold = np.percentile(gray, 15)
        mask = gray <= threshold
    # Keep only the largest connected component to ignore stray dark specks.
    labeled, n = ndimage.label(mask)
    if n > 1:
        sizes = ndimage.sum(mask, labeled, range(1, n + 1))
        mask = labeled == (np.argmax(sizes) + 1)
    return mask


def _asymmetry_score(mask: np.ndarray) -> float:
    if mask.sum() == 0:
        return 0.0
    h_diff = np.abs(mask.astype(int) - np.fliplr(mask).astype(int)).mean()
    v_diff = np.abs(mask.astype(int) - np.flipud(mask).astype(int)).mean()
    return float(np.clip((h_diff + v_diff) / 2, 0, 1))


def _border_irregularity(mask: np.ndarray) -> float:
    area = mask.sum()
    if area < 4:
        return 0.0
    eroded = ndimage.binary_erosion(mask)
    perimeter = mask.sum() - eroded.sum()
    circularity = (4 * np.pi * area) / (perimeter**2 + 1e-6)
    return float(np.clip(1 - circularity, 0, 1))


def extract_features(image: Image.Image) -> np.ndarray:
    """Resize, segment, and reduce an image to the FEATURE_ORDER vector."""
    rgb = np.asarray(image.convert("RGB").resize((FEATURE_SIZE, FEATURE_SIZE)), dtype=np.float64)
    gray = rgb.mean(axis=2)

    mask = _lesion_mask(gray)
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]

    asymmetry_score = _asymmetry_score(mask)
    border_irregularity = _border_irregularity(mask)
    color_variance = float(np.clip(rgb[mask].std() / 80, 0, 1)) if mask.any() else 0.0
    diameter_ratio = float(mask.sum() / mask.size)
    red_dominance = float(np.clip((r[mask].mean() - (g[mask].mean() + b[mask].mean()) / 2) / 128, -1, 1)) if mask.any() else 0.0
    mean_darkness = float(np.clip(1 - gray[mask].mean() / 255, 0, 1)) if mask.any() else 0.0

    return np.array([
        asymmetry_score,
        border_irregularity,
        color_variance,
        diameter_ratio,
        red_dominance,
        mean_darkness,
    ])
