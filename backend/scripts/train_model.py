"""Trains the skin-lesion classifier from the original HAM10000 dataset and saves it
as a scikit-learn .pkl for the backend to load directly (see
app/services/local_predictor.py) -- this replaces the GCP Vertex AI AutoML endpoint
the project used previously, so no GCP project/credits are needed to run inference.

Usage:
    python scripts/train_model.py --data-dir /path/to/Dermalyze_data/original

Expects that directory to contain `vertex_ai_import.csv` (columns: split, gs:// url,
label) and an `images/` folder holding the files the CSV's URLs point at by
basename -- the layout the dataset was originally exported from Vertex AI in.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
from PIL import Image
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, f1_score, precision_recall_fscore_support
from sklearn.utils.class_weight import compute_class_weight

# Allows running this script directly (`python scripts/train_model.py`) regardless of
# the caller's cwd, since it needs the `app` package for the shared feature extractor.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.ml.features import FEATURE_DIM, extract_features  # noqa: E402

DEFAULT_OUTPUT = Path(__file__).resolve().parent.parent / "app" / "ml_models" / "skin_lesion_model.pkl"

# Mirrors RISK_BY_CLASS in app/services/gemini_report.py -- the app only ever shows the
# user a Low/High risk tier, never the raw 7-way HAM10000 label, so that's the metric
# that actually matters. A plain "balanced" class_weight still leaves mel/bcc/akiec
# (the "high" tier) with poor recall because they're also individually rare within the
# already-rare high-risk group; HIGH_RISK_BOOST multiplies their weight further so the
# model is tuned to minimize missed-cancer false negatives, at a deliberate cost to
# precision (over-flagging low-risk lesions as high-risk just sends someone to a doctor
# who didn't strictly need to go -- the safe direction to err in for a screening tool).
HIGH_RISK_LABELS = {"mel", "bcc", "akiec"}
DEFAULT_HIGH_RISK_BOOST = 2.0


def _risk_tier(labels: np.ndarray) -> np.ndarray:
    return np.array(["high" if label in HIGH_RISK_LABELS else "low" for label in labels])


def _read_manifest(data_dir: Path) -> list[tuple[str, Path, str]]:
    rows = []
    with open(data_dir / "vertex_ai_import.csv", newline="") as f:
        for split, url, label in csv.reader(f):
            image_path = data_dir / "images" / url.rsplit("/", 1)[-1]
            rows.append((split, image_path, label))
    return rows


def _featurize(image_path: Path) -> np.ndarray:
    with Image.open(image_path) as img:
        return extract_features(img)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--data-dir", required=True, type=Path, help="Dermalyze_data/original directory")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, type=Path)
    parser.add_argument("--n-estimators", default=400, type=int)
    parser.add_argument("--workers", default=8, type=int)
    parser.add_argument("--limit", default=None, type=int, help="Use only the first N rows (smoke-testing)")
    parser.add_argument(
        "--high-risk-boost",
        default=DEFAULT_HIGH_RISK_BOOST,
        type=float,
        help="Extra weight multiplier on mel/bcc/akiec on top of balanced class weights",
    )
    args = parser.parse_args()

    rows = _read_manifest(args.data_dir)
    if args.limit:
        rows = rows[: args.limit]
    print(f"Loaded manifest: {len(rows)} images")

    paths = [path for _, path, _ in rows]
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=args.workers) as pool:
        features = list(pool.map(_featurize, paths, chunksize=32))
    print(f"Extracted features for {len(features)} images in {time.time() - t0:.1f}s")

    X = np.stack(features)
    y = np.array([label for _, _, label in rows])
    split = np.array([s for s, _, _ in rows])

    # TRAIN + VALIDATION both go into fitting (no early-stopping / hyperparameter
    # search here that would need a held-out validation set); TEST stays untouched
    # for the accuracy/F1 numbers reported below and saved into the artifact.
    train_mask = split != "TEST"
    test_mask = split == "TEST"
    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]
    print(f"Train: {len(X_train)}  Test: {len(X_test)}  Feature dim: {X.shape[1]} (expected {FEATURE_DIM})")

    classes = sorted(set(y_train))
    class_weight = dict(zip(classes, compute_class_weight("balanced", classes=np.array(classes), y=y_train)))
    for label in HIGH_RISK_LABELS:
        class_weight[label] *= args.high_risk_boost
    print(f"Class weights (high-risk boost x{args.high_risk_boost}): {class_weight}")

    clf = RandomForestClassifier(
        n_estimators=args.n_estimators,
        class_weight=class_weight,
        min_samples_leaf=2,
        n_jobs=-1,
        random_state=42,
    )
    t0 = time.time()
    clf.fit(X_train, y_train)
    print(f"Trained RandomForest ({args.n_estimators} trees) in {time.time() - t0:.1f}s")

    y_pred = clf.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    report = classification_report(y_test, y_pred)
    print(f"Test accuracy: {accuracy:.4f}  Macro F1: {macro_f1:.4f}")
    print(report)

    # The number that actually matters for this app: Low/High risk tier, not the raw
    # 7-way label (see HIGH_RISK_LABELS comment above).
    risk_true, risk_pred = _risk_tier(y_test), _risk_tier(y_pred)
    risk_precision, risk_recall, risk_f1, _ = precision_recall_fscore_support(
        risk_true, risk_pred, labels=["high", "low"], zero_division=0
    )
    risk_accuracy = float((risk_true == risk_pred).mean())
    print(
        f"Risk-tier accuracy: {risk_accuracy:.4f}  |  high-risk: precision={risk_precision[0]:.3f} "
        f"recall={risk_recall[0]:.3f} f1={risk_f1[0]:.3f}"
    )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    artifact = {
        "model": clf,
        "classes": clf.classes_.tolist(),
        "feature_dim": int(X.shape[1]),
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "test_accuracy": float(accuracy),
        "test_macro_f1": float(macro_f1),
        "test_risk_tier_accuracy": risk_accuracy,
        "test_high_risk_recall": float(risk_recall[0]),
        "test_high_risk_precision": float(risk_precision[0]),
        "n_train": int(len(X_train)),
        "n_test": int(len(X_test)),
    }
    joblib.dump(artifact, args.output, compress=3)
    print(f"Saved model to {args.output} ({args.output.stat().st_size / 1e6:.1f} MB)")

    metrics_path = args.output.parent / f"{args.output.stem}.metrics.json"
    metrics_path.write_text(
        json.dumps(
            {
                "test_accuracy": accuracy,
                "test_macro_f1": macro_f1,
                "test_risk_tier_accuracy": risk_accuracy,
                "test_high_risk_recall": float(risk_recall[0]),
                "test_high_risk_precision": float(risk_precision[0]),
                "n_train": len(X_train),
                "n_test": len(X_test),
                "classification_report": report,
                "trained_at": artifact["trained_at"],
            },
            indent=2,
        )
    )
    print(f"Saved metrics to {metrics_path}")


if __name__ == "__main__":
    main()
