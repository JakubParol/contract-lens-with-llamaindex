"""Simulate scanned documents by degrading clean PDF quality.

Converts each PDF page to image, applies scan-like effects (rotation, noise,
contrast reduction), and re-assembles as a PDF.
Output: data/scans/*.pdf
"""

from __future__ import annotations

import random
from pathlib import Path

import numpy as np
from pdf2image import convert_from_path
from PIL import Image, ImageFilter, ImageEnhance

INPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "agreements"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "scans"

# Scan simulation parameters
DPI = 250
ROTATION_RANGE = (-1.5, 1.5)  # degrees
NOISE_INTENSITY = 12  # Gaussian noise std dev (0-255 scale)
CONTRAST_FACTOR = 0.85  # <1 = reduce contrast
BRIGHTNESS_FACTOR = 0.95  # slight darkening
BLUR_RADIUS = 0.3  # subtle blur to simulate scan optics


def degrade_page(img: Image.Image) -> Image.Image:
    """Apply scan-like degradation to a single page image."""
    # Random slight rotation
    angle = random.uniform(*ROTATION_RANGE)
    img = img.rotate(angle, resample=Image.BICUBIC, expand=False, fillcolor=(255, 255, 255))

    # Convert to numpy for noise
    arr = np.array(img, dtype=np.float32)

    # Add Gaussian noise
    noise = np.random.normal(0, NOISE_INTENSITY, arr.shape)
    arr = np.clip(arr + noise, 0, 255).astype(np.uint8)

    img = Image.fromarray(arr)

    # Reduce contrast
    img = ImageEnhance.Contrast(img).enhance(CONTRAST_FACTOR)

    # Slight brightness reduction
    img = ImageEnhance.Brightness(img).enhance(BRIGHTNESS_FACTOR)

    # Subtle blur (scan optics)
    img = img.filter(ImageFilter.GaussianBlur(radius=BLUR_RADIUS))

    return img


def simulate_scan(pdf_path: Path, output_path: Path) -> None:
    """Convert a clean PDF to a scan-like PDF."""
    pages = convert_from_path(str(pdf_path), dpi=DPI)
    degraded_pages = [degrade_page(page) for page in pages]

    # Save as PDF (first page saves, rest appended)
    degraded_pages[0].save(
        str(output_path),
        "PDF",
        save_all=True,
        append_images=degraded_pages[1:] if len(degraded_pages) > 1 else [],
        resolution=DPI,
    )


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    pdf_files = sorted(INPUT_DIR.glob("*.pdf"))
    if not pdf_files:
        print(f"No PDFs found in {INPUT_DIR}. Run generate_agreements.py first.")
        return

    for pdf_path in pdf_files:
        output_path = OUTPUT_DIR / pdf_path.name
        simulate_scan(pdf_path, output_path)
        print(f"  Scanned: {output_path.name}")

    print(f"\nAll {len(pdf_files)} scans generated in {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
