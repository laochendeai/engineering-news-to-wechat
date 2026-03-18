#!/usr/bin/env python3
"""
Get (and optionally cache) WeChat Official Account Access Token.
Usage: python3 get_token.py
Output: prints the access_token string to stdout
Config: reads APPID and APPSECRET from env vars WX_APPID / WX_APPSECRET only.
Security: this fork-safe variant intentionally does NOT read config.json.
"""

import json, os, sys, time, urllib.request
from pathlib import Path

CACHE_FILE = Path.home() / ".cache" / "wechat-publisher-safe" / "token.json"
TOKEN_URL = "https://api.weixin.qq.com/cgi-bin/stable_token"


def load_config():
    appid = os.environ.get("WX_APPID")
    secret = os.environ.get("WX_APPSECRET")
    if appid and secret:
        return appid, secret
    print("ERROR: Missing WX_APPID/WX_APPSECRET env vars. This fork-safe variant does not support config.json.", file=sys.stderr)
    sys.exit(1)


def get_cached_token():
    if not CACHE_FILE.exists():
        return None
    cache = json.loads(CACHE_FILE.read_text())
    # Expire 5 minutes early for safety
    if cache.get("expires_at", 0) > time.time() + 300:
        return cache["access_token"]
    return None


def fetch_token(appid, secret):
    payload = json.dumps({
        "grant_type": "client_credential",
        "appid": appid,
        "secret": secret,
        "force_refresh": False
    }).encode()
    req = urllib.request.Request(TOKEN_URL, data=payload,
                                  headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    if "errcode" in data and data["errcode"] != 0:
        errcode = data.get("errcode")
        errmsg = data.get("errmsg", "")
        print(f"ERROR: WeChat API error: errcode={errcode} errmsg={errmsg}", file=sys.stderr)
        sys.exit(1)
    token = data["access_token"]
    expires_in = data.get("expires_in", 7200)
    CACHE_FILE.parent.mkdir(parents=True, exist_ok=True)
    CACHE_FILE.write_text(json.dumps({
        "access_token": token,
        "expires_at": time.time() + expires_in
    }))
    return token


def main():
    appid, secret = load_config()
    token = get_cached_token()
    if not token:
        token = fetch_token(appid, secret)
    print(token, end="")


if __name__ == "__main__":
    main()
