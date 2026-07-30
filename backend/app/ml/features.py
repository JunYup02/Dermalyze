"""Classical computer-vision feature extraction for the skin lesion classifier.

Imported identically by training (scripts/train_model.py) and inference
(app/services/local_predictor.py) so a live request's feature vector always matches
the layout the model was fit on.

Deliberately classical (color/texture/edge statistics via scikit-image) instead of a
CNN: no torch/tensorflow at runtime. Those are heavy enough to risk OOM-killing a
Render free-tier instance -- the same reason this project talks to the classifier via
a plain REST call instead of the google-cloud-aiplatform SDK (see git history).
"""
from __future__ import annotations

import numpy as np
from PIL import Image
from skimage.color import rgb2gray, rgb2hsv
from skimage.feature import hog, local_binary_pattern
from skimage.util import img_as_ubyte

IMAGE_SIZE = (96, 96)
_HIST_BINS = 16
_LBP_POINTS = 8
_LBP_RADIUS = 1
_LBP_BINS = _LBP_POINTS + 2  # uniform LBP: P+1 uniform patterns + 1 non-uniform bucket


def extract_features(image: Image.Image) -> np.ndarray:
    """Turn a PIL image into a fixed-length feature vector.

    Concatenates RGB color moments, an HSV histogram, an LBP texture histogram, and
    HOG edge/shape features -- a compact, non-deep-learning descriptor set standard
    for this kind of skin-lesion image classification.
    """
    rgb = np.asarray(image.convert("RGB").resize(IMAGE_SIZE), dtype=np.float64) / 255.0

    color_moments = np.concatenate([rgb.mean(axis=(0, 1)), rgb.std(axis=(0, 1))])

    hsv = rgb2hsv(rgb)
    hsv_hist = np.concatenate(
        [
            np.histogram(hsv[..., channel], bins=_HIST_BINS, range=(0.0, 1.0), density=True)[0]
            for channel in range(3)
        ]
    )

    gray = rgb2gray(rgb)
    # LBP wants integer pixel values -- feeding it floats emits a scikit-image warning
    # and can behave oddly on near-identical adjacent float pixels.
    lbp = local_binary_pattern(img_as_ubyte(gray), P=_LBP_POINTS, R=_LBP_RADIUS, method="uniform")
    lbp_hist, _ = np.histogram(lbp, bins=_LBP_BINS, range=(0, _LBP_BINS), density=True)

    hog_features = hog(
        gray,
        orientations=9,
        pixels_per_cell=(24, 24),
        cells_per_block=(2, 2),
        feature_vector=True,
    )

    return np.concatenate([color_moments, hsv_hist, lbp_hist, hog_features]).astype(np.float32)


# Derived once at import time (rather than hand-computed) so it can never drift out
# of sync with extract_features -- used by the training script to sanity-check its
# feature matrix shape before an hours-long training run.
FEATURE_DIM = extract_features(Image.new("RGB", IMAGE_SIZE)).shape[0]
