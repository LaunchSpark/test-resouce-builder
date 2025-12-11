#!/usr/bin/env bash
# Helper script to install dependencies and run OCR over available exam images.
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Install Python dependencies for OCR processing.
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

# Gather image inputs. Use provided arguments when available; otherwise, scan the
# project root for common image types.
if [[ "$#" -gt 0 ]]; then
  inputs=("$@")
else
  readarray -t inputs < <(find "$PROJECT_DIR" -maxdepth 1 -type f \( \
    -iname '*.png' -o \
    -iname '*.jpg' -o \
    -iname '*.jpeg' -o \
    -iname '*.tiff' -o \
    -iname '*.bmp' -o \
    -iname '*.gif' \
  \) | sort)
fi

if [[ "${#inputs[@]}" -eq 0 ]]; then
  echo "No image files provided or found. Add images or pass paths to run.sh." >&2
  exit 1
fi

python3 ocr_to_json.py "${inputs[@]}"
