#!/bin/bash

echo "[INFO] Compiling report..."
pandoc report.md -o report.pdf

echo "[INFO] Compiling DOT diagrams..."

dot -Tsvg -O ./architecture.dot

echo "[INFO] Compiling slides..."
pandoc -t beamer slides.md -o slides.pdf
