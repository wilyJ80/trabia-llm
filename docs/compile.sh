#!/bin/bash

echo "[INFO] Compiling report..."
pandoc report.md -o report.pdf

echo "[INFO] Compiling slides..."
pandoc -t beamer slides.md -o slides.pdf
