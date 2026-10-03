"""Activity 1.3 - validate Gemini connectivity (text-only and text + image).

Usage:  python check_gemini.py [optional_image.jpg]
Needs GOOGLE_API_KEY in .env. Tries the configured model, then the fallback chain.
"""
import sys

from PIL import Image, ImageDraw

import config
from gemini_utils import _model_chain, gemini_configured


def main() -> int:
    if not gemini_configured():
        print("FAIL: GOOGLE_API_KEY is not set. Copy .env.example to .env and add your key.")
        return 1
    from google import genai

    client = genai.Client(api_key=config.GEMINI_API_KEY)

    image_path = sys.argv[1] if len(sys.argv) > 1 else None
    image = Image.open(image_path) if image_path else _sample_image()

    for model in _model_chain():
        try:
            text = client.models.generate_content(model=model, contents="Reply with the single word: ready").text
            print(f"[text ] {model}: {text.strip()[:60]}")
            vision = client.models.generate_content(
                model=model, contents=["Name the dominant color of this image in one word.", image]).text
            print(f"[image] {model}: {vision.strip()[:60]}")
            print(f"\nOK: set GEMINI_MODEL={model} in .env")
            return 0
        except Exception as exc:
            print(f"[skip ] {model}: {str(exc)[:120]}")
    print("FAIL: no model responded. Check the API key, quota and network.")
    return 1


def _sample_image() -> Image.Image:
    img = Image.new("RGB", (128, 128), (200, 30, 40))
    ImageDraw.Draw(img).ellipse((32, 32, 96, 96), fill=(250, 220, 220))
    return img


if __name__ == "__main__":
    raise SystemExit(main())
