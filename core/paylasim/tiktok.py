# -*- coding: utf-8 -*-
"""TikTok Content Posting API.

Onaysız istemci: MEDIA_UPLOAD (taslak) veya DIRECT POST + SELF_ONLY.
Audit sonrası: DIRECT POST herkese açık.
"""

import base64
import time

import requests

from core import depolama
from core.paylasim import host

TT_BASE = "https://open.tiktokapis.com"
TIMEOUT = 30


def baglanti_testi():
    token = depolama.ayar_al("tt_token")
    if not token:
        return False, "TikTok token eksik"
    try:
        r = requests.post(
            f"{TT_BASE}/v2/oauth/token/",
            data={
                "client_key": depolama.ayar_al("tt_client_key", ""),
                "client_secret": depolama.ayar_al("tt_client_secret", ""),
                "code": "",
                "grant_type": "client_credentials",
            },
            timeout=TIMEOUT)
        # Basit test: creator_info query
        r2 = requests.post(
            f"{TT_BASE}/v2/post/publish/creator_info/query/",
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json; charset=UTF-8"},
            json={},
            timeout=TIMEOUT)
        if r2.status_code == 200:
            return True, "TikTok bağlı"
        return False, f"HTTP {r2.status_code}: {r2.text[:200]}"
    except Exception as e:
        return False, str(e)


def paylas(post):
    """Onaylı postu TikTok'a taslak (MEDIA_UPLOAD) olarak yükler."""
    token = depolama.ayar_al("tt_token")
    host_yontem = depolama.ayar_al("host_yontem", "catbox")
    mod = depolama.ayar_al("tt_mod", "taslak")  # taslak | self_only

    if not token:
        return False, "TikTok token eksik (Ayarlar sekmesi)"

    # Public URL
    try:
        url = host.public_url_yap(post["gorsel_yol"], yontem=host_yontem)
    except Exception as e:
        return False, f"Public URL hatası: {e}"

    # Creator info
    try:
        r = requests.post(
            f"{TT_BASE}/v2/post/publish/creator_info/query/",
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json; charset=UTF-8"},
            json={},
            timeout=TIMEOUT)
        r.raise_for_status()
    except Exception as e:
        return False, f"Creator info hatası: {e}"

    caption = post.get("caption", "")
    hashtags = post.get("hashtags", "")
    title = f"{caption} {hashtags}"[:90]

    privacy = "SELF_ONLY" if mod == "self_only" else "PUBLIC_TO_EVERYONE"
    post_mode = "MEDIA_UPLOAD" if mod == "taslak" else "DIRECT POST"

    body = {
        "post_info": {
            "title": title,
            "privacy_level": privacy,
            "disable_comment": False,
            "auto_add_music": True,
            "brand_content_toggle": False,
            "brand_organic_toggle": False,
        },
        "source_info": {
            "source": "PULL_FROM_URL",
            "video_url": url,
        },
        "media_type": "PHOTO",
        "post_mode": post_mode,
    }

    try:
        r = requests.post(
            f"{TT_BASE}/v2/post/publish/content/init/",
            headers={"Authorization": f"Bearer {token}",
                     "Content-Type": "application/json; charset=UTF-8"},
            json=body,
            timeout=TIMEOUT)
        r.raise_for_status()
        veri = r.json()
        publish_id = veri.get("data", {}).get("publish_id", "")
        if post_mode == "MEDIA_UPLOAD":
            return True, f"Taslak yüklendi: {publish_id}"
        return True, f"Yayınlandı: {publish_id}"
    except Exception as e:
        return False, f"Init hatası: {e}"
