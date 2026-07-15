"""Train the demo lesion classifier on synthetic data and save the artifact.

Run from backend/: python -m ml.train_model
"""
from pathlib import Path

import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

from ml.synthetic_data import generate_dataset

ARTIFACT_PATH = Path(__file__).parent / "artifacts" / "lesion_model.joblib"


def main():
    X, y = generate_dataset()
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = RandomForestClassifier(n_estimators=200, max_depth=6, random_state=42)
    clf.fit(X_train, y_train)

    preds = clf.predict(X_test)
    print(f"lesion model  accuracy={accuracy_score(y_test, preds):.3f}  classes={list(clf.classes_)}")

    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(clf, ARTIFACT_PATH)
    print(f"saved {ARTIFACT_PATH}")


if __name__ == "__main__":
    main()
