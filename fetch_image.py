#!/usr/bin/env python3
"""
Ubuntu-Inspired Image Fetcher
- Prompts the user for an image URL
- Creates "Fetched_Images" directory if it doesn't exist
- Downloads the image in binary mode and saves it with an appropriate filename
- Handles network and HTTP errors gracefully
"""

import os
import time
import uuid
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests

FETCH_DIR = Path("Fetched_Images")

# Common mapping for content-type -> extension
COMMON_IMAGE_EXT = {
    "image/jpeg": ".jpg",
    "image/pjpeg": ".jpg",
    "image/png": ".png",
    "image/gif": ".gif",
    "image/webp": ".webp",
    "image/bmp": ".bmp",
    "image/svg+xml": ".svg",
    "image/x-icon": ".ico",
}


def ensure_fetch_dir():
    """Create Fetched_Images directory if it doesn't exist."""
    FETCH_DIR.mkdir(parents=True, exist_ok=True)


def get_filename_from_url(url: str, response: requests.Response) -> str:
    """
    Try to extract a sensible filename:
    - Use the filename from the URL path if present and has an extension
    - Otherwise derive extension from Content-Type and generate a unique name
    """
    parsed = urlparse(url)
    path = unquote(parsed.path or "")
    name = os.path.basename(path)

    # If URL path gives a filename with extension, use it
    if name and "." in name:
        return name

    # Try content-type header for extension
    content_type = response.headers.get("Content-Type", "").split(";")[0].lower()
    ext = COMMON_IMAGE_EXT.get(content_type)

    # If still unknown but content-type startswith image/, create extension from subtype
    if not ext and content_type.startswith("image/"):
        ext = "." + content_type.split("/")[-1]

    # Fallback default extension
    if not ext:
        ext = ".jpg"

    timestamp = int(time.time())
    short_id = uuid.uuid4().hex[:6]
    return f"image_{timestamp}_{short_id}{ext}"


def download_image(url: str) -> Path | None:
    """Download the image and return the saved file path or None on failure."""
    try:
        # ask requests to stream the content (avoid loading all at once)
        resp = requests.get(url, stream=True, timeout=15)
        resp.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[Error] Network or request error: {e}")
        return None

    content_type = resp.headers.get("Content-Type", "").split(";")[0].lower()
    if not content_type.startswith("image"):
        print(f"[Error] The URL does not appear to be an image (Content-Type: {content_type}).")
        return None

    filename = get_filename_from_url(url, resp)
    filepath = FETCH_DIR / filename

    try:
        # Write binary content in chunks
        with open(filepath, "wb") as f:
            for chunk in resp.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        return filepath
    except OSError as e:
        print(f"[Error] Failed to save image: {e}")
        return None


def main():
    ensure_fetch_dir()
    url = input("Enter the image URL (http/https): ").strip()
    if not url:
        print("No URL entered. Exiting.")
        return

    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        print("Please enter a valid HTTP or HTTPS URL.")
        return

    print("Downloading... this may take a few seconds.")
    saved_path = download_image(url)
    if saved_path:
        print(f"✅ Image saved to: {saved_path}")
        print("You can share images from the Fetched_Images folder later.")
    else:
        print("❌ Image download failed. See error message above.")


if __name__ == "__main__":
    main()
