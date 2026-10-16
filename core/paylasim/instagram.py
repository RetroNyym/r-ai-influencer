# -*- coding: utf-8 -*-
"""Instagram Graph API Content Publishing."""

import time

import requests

from core import depolama
from core.paylasim import host

GRAPH = "https://graph.facebook.com/v21.0"
TIMEOUT = 30


def baglanti_testi():
    """Token geçerli mi, IG user id alınıyor mu test eder."""
    token = depolama.ayar_al("ig_token")
    ig_user = depolama.ayar_al("ig_user_id")
    if not token or not ig_user:
        return False, "Token veya IG User ID eksik"
    try:
        r = requests.get(
            f"{GRAPH}/{ig_user}",
            params={"fields": "id,username", "access_token": token},
            timeout=TIMEOUT)
        if r.status_code == 200:
            veri = r.json()
            return True, f"Bağlı: @{veri.get('username', ig_user)}"
        return False, r.text
    except Exception as e:
        return False, str(e)


def paylas(post):
    """Onaylı postu Instagram'a yayınlar. (basarili, mesaj) döner."""
    token = depolama.ayar_al("ig_token")
    ig_user = depolama.ayar_al("ig_user_id")
    host_yontem = depolama.ayar_al("host_yontem", "catbox")

    if not token or not ig_user:
        return False, "IG yapılandırması eksik (Ayarlar sekmesi)"

    # Public URL üret
    try:
        url = host.public_url_yap(post["gorsel_yol"], yontem=host_yontem)
    except Exception as e:
        return False, f"Public URL hatası: {e}"

    caption = post.get("caption", "")
    hashtags = post.get("hashtags", "")
    full_caption = f"{caption}\n\n{hashtags}" if hashtags else caption

    # 1. Container oluştur
    try:
        r = requests.post(
            f"{GRAPH}/{ig_user}/media",
            data={
                "image_url": url,
                "caption": full_caption,
                "access_token": token
            },
            timeout=TIMEOUT)
        r.raise_for_status()
        container_id = r.json().get("id")
    except Exception as e:
        return False, f"Container hatası: {e}"

    if not container_id:
        return False, "Container ID alınamadı"

    # 2. Status poll (FINISHED bekle)
    for _ in range(20):
        time.sleep(2)
        try:
            r = requests.get(
                f"{GRAPH}/{container_id}",
                params={"fields": "status_code", "access_token": token},
                timeout=TIMEOUT)
            durum = r.json().get("status_code")
            if durum == "FINISHED":
                break
            if durum == "ERROR":
                return False, "Container ERROR"
        except Exception:
            continue
    else:
        return False, "Container timeout (FINISHED olmadı)"

    # 3. Publish
    try:
        r = requests.post(
            f"{GRAPH}/{ig_user}/media_publish",
            data={
                "creation_id": container_id,
                "access_token": token
            },
            timeout=TIMEOUT)
        r.raise_for_status()
        media_id = r.json().get("id")
        return True, f"Yayınlandı: {media_id}"
    except Exception as e:
        return False, f"Publish hatası: {e}"
