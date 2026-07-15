#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

echo "--- building frontend ---"
cd frontend
npm ci
npm run build
cd ..

echo "--- installing backend deps ---"
cd backend
pip install -r requirements.txt

echo "--- training model ---"
python -m ml.train_model
