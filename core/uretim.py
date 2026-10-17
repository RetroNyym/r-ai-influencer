# -*- coding: utf-8 -*-
"""Pollinations.ai tabanlı ücretsiz görsel + caption üretimi."""

import time
import urllib.parse
from pathlib import Path

import requests

from core import depolama, kisilik, sahne_kutuphanesi

IMAGE_BASE = "https://image.pollinations.ai/prompt/"
TEXT_BASE = "https://text.pollinations.ai/"
TIMEOUT = 90
MAX_RETRY = 3


def gorsel_uret(prompt, seed, genislik=1024, yukseklik=1280):
    """Aktif API'ye göre görsel üretir. API yoksa Pollinations ücretsiz uç."""
    from core import api_yonetici
    data = api_yonetici.uretim_yonlendir(prompt, seed=seed,
                                         genislik=genislik, yukseklik=yukseklik)
    if data and len(data) > 500:
        return data
    raise RuntimeError("Gorsel uretimi basarisiz")


def tutarli_gorsel_uret(persona, prompt, seed, genislik=1024, yukseklik=1280):
    """Görsel üretir; persona'nın kilitli kimliği varsa yüze uygular.

    Böylece her sahnede AYNI kişi görünür (stabil karakter). Kimlik yoksa
    veya yüzsüz bir sahne üretilirse ham görsel döner.
    """
    import numpy as np
    import cv2
    data = gorsel_uret(prompt, seed=seed, genislik=genislik, yukseklik=yukseklik)
    kimlik = kisilik.kimlik_al(persona.get("id")) if persona else None
    if not kimlik:
        return data
    try:
        from core import yuz_degistir
        img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
        if img is None:
            return data
        sonuc = yuz_degistir.kimlik_uygula(img, kimlik)
        if sonuc is None:
            return data
        ok, buf = cv2.imencode(".jpg", sonuc, [cv2.IMWRITE_JPEG_QUALITY, 95])
        return buf.tobytes() if ok else data
    except Exception:
        return data


def caption_uret(persona, sahne):
    """Pollinations text ile caption + hashtag üretir."""
    prompt = (
        f"You are {persona['ad']}, a {persona.get('yas', 25)} year old "
        f"{persona.get('nis', 'lifestyle')} influencer. "
        f"Voice: {persona.get('marka_sesi', 'friendly and authentic')}. "
        f"Write a short Instagram caption (max 200 chars) for this scene: {sahne}. "
        f"End with 5 relevant hashtags. Reply ONLY with JSON: "
        f'{{"caption": "...", "hashtags": ["#tag1", "#tag2", "#tag3", "#tag4", "#tag5"]}}'
    )
    enc = urllib.parse.quote(prompt)
    url = f"{TEXT_BASE}{enc}?model=openai&json=true"

    for deneme in range(MAX_RETRY):
        try:
            r = requests.get(url, timeout=30)
            if r.status_code == 200:
                return _caption_parse(r.text, sahne)
            time.sleep(2)
        except requests.RequestException:
            if deneme == MAX_RETRY - 1:
                break
            time.sleep(2)

    # Fallback: şablondan caption
    return _fallback_caption(persona, sahne)


def _caption_parse(metin, sahne):
    import json
    import re
    try:
        m = re.search(r'\{.*\}', metin, re.DOTALL)
        if m:
            veri = json.loads(m.group(0))
            return {
                "caption": veri.get("caption", sahne),
                "hashtags": veri.get("hashtags", ["#ai", "#virtualinfluencer"])
            }
    except Exception:
        pass
    return _fallback_caption({"ad": "", "marka_sesi": ""}, sahne)


def _fallback_caption(persona, sahne):
    ad = persona.get("ad", "")
    hashtaglar = ["#ai", "#virtualinfluencer", "#digitalcreator", "#aicontent", "#instagood"]
    return {
        "caption": f"{ad}: {sahne} ✨",
        "hashtags": hashtaglar
    }


def toplu_uret(persona_id, sahne_sayisi=3, ilerleme_cb=None):
    """Belirli persona için toplu içerik üretir.

    Returns: list of post dicts (depolama'ya kaydedilir)
    """
    persona = kisilik.persona_al(persona_id)
    if not persona:
        raise ValueError("Persona bulunamadi")

    nis = persona.get("nis", "lifestyle")
    kanon = persona.get("kanon_gorsel")

    posts = []
    for i in range(sahne_sayisi):
        if ilerleme_cb:
            ilerleme_cb(i + 1, sahne_sayisi, f"Sahne {i+1}/{sahne_sayisi} uretiliyor...")

        sahne = sahne_kutuphanesi.sahne_sec(nis, seed=(persona.get("seed", 0) + i))
        prompt = kisilik.prompt_yap(sahne, persona)

        try:
            gorsel_bytes = tutarli_gorsel_uret(persona, prompt,
                                               seed=persona.get("seed", 0) + i)
        except Exception as e:
            if ilerleme_cb:
                ilerleme_cb(i + 1, sahne_sayisi, f"Sahne {i+1} HATA: {e}")
            continue

        # Dosyaya kaydet
        tarih = time.strftime("%Y%m%d")
        klasor = depolama.URETILEN_KLASOR / tarih
        klasor.mkdir(parents=True, exist_ok=True)
        dosya = klasor / f"post_{persona_id}_{int(time.time())}_{i}.jpg"
        dosya.write_bytes(gorsel_bytes)

        # Caption üret
        cap = caption_uret(persona, sahne)

        post_id = depolama.post_ekle({
            "persona_id": persona_id,
            "sahne": sahne,
            "prompt": prompt,
            "gorsel_yol": str(dosya),
            "caption": cap["caption"],
            "hashtags": " ".join(cap["hashtags"]),
            "durum": "onay_bekliyor"
        })

        posts.append({
            "id": post_id,
            "sahne": sahne,
            "gorsel_yol": str(dosya),
            "caption": cap["caption"],
            "hashtags": " ".join(cap["hashtags"])
        })

        # Rate limit: 5sn bekle
        if i < sahne_sayisi - 1:
            time.sleep(5)

    if ilerleme_cb:
        ilerleme_cb(sahne_sayisi, sahne_sayisi, f"Tamamlandi: {len(posts)} post")

    return posts


def kanon_uret(persona_id, sayi=8, ilerleme_cb=None):
    """Yeni persona için canon yüz adayları üretir (Pollinations)."""
    persona = kisilik.persona_al(persona_id)
    if not persona:
        raise ValueError("Persona bulunamadi")

    base_prompt = persona.get("anchor_prompt", "")
    adaylar = []
    seed = persona.get("seed", 0)

    for i in range(sayi):
        if ilerleme_cb:
            ilerleme_cb(i + 1, sayi, f"Aday {i+1}/{sayi}...")
        prompt = f"{base_prompt}, portrait headshot, neutral background, looking at camera"
        try:
            data = gorsel_uret(prompt, seed=seed + i, genislik=768, yukseklik=768)
        except Exception:
            continue
        tarih = time.strftime("%Y%m%d")
        klasor = depolama.URETILEN_KLASOR / tarih
        klasor.mkdir(parents=True, exist_ok=True)
        dosya = klasor / f"kanon_{persona_id}_{seed+i}.jpg"
        dosya.write_bytes(data)
        adaylar.append(str(dosya))
        time.sleep(5)

    return adaylar
