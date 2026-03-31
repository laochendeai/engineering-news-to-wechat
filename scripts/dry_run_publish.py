#!/usr/bin/env python3
"""
Dry-run helper for wechat-publisher-safe.
- Converts Markdown to WeChat-compatible HTML
- Reports referenced local images
- Does NOT call WeChat APIs

Usage:
  python3 dry_run_publish.py article.md [--image-map images.json]
"""

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="Dry run Markdown -> WeChat HTML without API calls")
    parser.add_argument("article", help="Path to markdown article")
    parser.add_argument("--image-map", help="Optional image map json passed through to md_to_html.py")
    args = parser.parse_args()

    article = Path(args.article)
    if not article.exists():
        print(f"ERROR: Article not found: {article}", file=sys.stderr)
        sys.exit(1)

    cmd = [sys.executable, str(Path(__file__).parent / "md_to_html.py"), str(article)]
    if args.image_map:
        cmd += ["--image-map", args.image_map]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr)
        sys.exit(result.returncode)

    html = result.stdout
    image_refs = sorted(set(re.findall(r'src="([^"]+)"', html)))

    print("=== DRY RUN OK ===")
    print(f"Article: {article}")
    print(f"HTML length: {len(html)}")
    print(f"Referenced media count: {len(image_refs)}")
    if image_refs:
        print("Referenced media:")
        for ref in image_refs:
            print(f"- {ref}")
    print("\n=== HTML PREVIEW (first 1200 chars) ===")
    print(html[:1200])


if __name__ == "__main__":
    main()
