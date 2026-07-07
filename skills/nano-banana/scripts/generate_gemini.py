#!/usr/bin/env python3
"""Generate a Nano Banana (Gemini) image from a dense prompt, via Google's own Gemini API.

Usage:
    export GEMINI_API_KEY=...            # from https://aistudio.google.com/apikey
    python generate_gemini.py PROMPT_FILE OUT.png [--model gemini-2.5-flash-image] [--ref img1.jpg ...]

PROMPT_FILE: a text file with the dense narrative prompt (see SKILL.md method).
Confirm the current image model id in AI Studio; Nano Banana = gemini-2.5-flash-image, Pro is a newer id.
Requires: pip install google-genai
"""
import os, sys, argparse
from google import genai
from google.genai import types


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt_file")
    ap.add_argument("out")
    ap.add_argument("--model", default=os.environ.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image"))
    ap.add_argument("--ref", nargs="*", default=[], help="optional reference image paths")
    args = ap.parse_args()

    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        print("error: set GEMINI_API_KEY (https://aistudio.google.com/apikey)", file=sys.stderr)
        return 2

    with open(args.prompt_file, "r", encoding="utf-8") as f:
        prompt = f.read().strip()

    # Prompt + optional reference images as multimodal contents.
    contents: list = [prompt]
    for r in args.ref:
        with open(r, "rb") as fh:
            mime = "image/png" if r.lower().endswith(".png") else "image/jpeg"
            contents.append(types.Part.from_bytes(data=fh.read(), mime_type=mime))

    client = genai.Client(api_key=key)
    resp = client.models.generate_content(model=args.model, contents=contents)

    # Pull the first inline image part out of the response.
    for part in resp.candidates[0].content.parts:
        inline = getattr(part, "inline_data", None)
        if inline and getattr(inline, "data", None):
            with open(args.out, "wb") as out:
                out.write(inline.data)
            print(f"wrote {args.out}")
            return 0

    print("error: no image in response (check model id / prompt / quota)", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
