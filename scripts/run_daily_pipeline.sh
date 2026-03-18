#!/usr/bin/env bash
set -euo pipefail

# Unified entrypoint for: dry-run -> upload thumb -> md_to_html -> upload draft
# Required env:
#   WX_APPID / WX_APPSECRET
# Required args:
#   --article PATH
#   --cover PATH
#   --title TEXT
# Optional args:
#   --author TEXT
#   --digest TEXT
#   --html-out PATH

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

ARTICLE=""
COVER=""
TITLE=""
AUTHOR=""
DIGEST=""
HTML_OUT=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --article) ARTICLE="$2"; shift 2 ;;
    --cover) COVER="$2"; shift 2 ;;
    --title) TITLE="$2"; shift 2 ;;
    --author) AUTHOR="$2"; shift 2 ;;
    --digest) DIGEST="$2"; shift 2 ;;
    --html-out) HTML_OUT="$2"; shift 2 ;;
    *) echo "Unknown arg: $1" >&2; exit 1 ;;
  esac
done

[[ -n "$ARTICLE" ]] || { echo "ERROR: --article is required" >&2; exit 1; }
[[ -n "$COVER" ]] || { echo "ERROR: --cover is required" >&2; exit 1; }
[[ -n "$TITLE" ]] || { echo "ERROR: --title is required" >&2; exit 1; }
[[ -n "${WX_APPID:-}" ]] || { echo "ERROR: WX_APPID is missing" >&2; exit 1; }
[[ -n "${WX_APPSECRET:-}" ]] || { echo "ERROR: WX_APPSECRET is missing" >&2; exit 1; }
[[ -f "$ARTICLE" ]] || { echo "ERROR: article not found: $ARTICLE" >&2; exit 1; }
[[ -f "$COVER" ]] || { echo "ERROR: cover not found: $COVER" >&2; exit 1; }

if [[ -z "$HTML_OUT" ]]; then
  HTML_OUT="/tmp/$(basename "$ARTICLE" .md).html"
fi

python3 "$SCRIPT_DIR/dry_run_publish.py" "$ARTICLE" >/tmp/engineering-news-to-wechat.dryrun.txt
THUMB_ID="$(python3 "$SCRIPT_DIR/upload_thumb.py" "$COVER")"
python3 "$SCRIPT_DIR/md_to_html.py" "$ARTICLE" > "$HTML_OUT"
MEDIA_ID="$(python3 "$SCRIPT_DIR/upload_draft.py" --title "$TITLE" --html "$HTML_OUT" --thumb-media-id "$THUMB_ID" --author "$AUTHOR" --digest "$DIGEST")"

printf 'ARTICLE=%s\nHTML=%s\nTHUMB_ID=%s\nMEDIA_ID=%s\n' "$ARTICLE" "$HTML_OUT" "$THUMB_ID" "$MEDIA_ID"
