# -*- coding: utf-8 -*-
"""Persona yönetimi: CRUD, seed kilidi, prompt anchor."""

import random

from core import depolama


def yeni_kisilik(ad, yas, nis, ten, sac, goz, stil, kisilik_tanimi, marka_sesi):
    """Yeni persona oluşturur; seed rastgele üretilir."""
    seed = random.randint(1, 2**31 - 1)
    anchor = _anchor_yap(ad, yas, ten, sac, goz, stil, kisilik_tanimi)
    pid = depolama.persona_ekle({
        "ad": ad, "yas": yas, "nis": nis, "ten": ten, "sac": sac,
        "goz": goz, "stil": stil, "kisilik": kisilik_tanimi,
        "marka_sesi": marka_sesi, "seed": seed, "anchor_prompt": anchor,
        "kaynak": "ai"
    })
    return pid


def kendi_yuzunden(persona_id, gorsel_yol, yuz_meta, varyasyonlar):
    """Kullanıcının kendi yüzünden dönüştürülmüş sureti persona'ya kaydeder."""
    depolama.persona_guncelle(persona_id, {
        "kaynak": "kendi_yuz",
        "kanon_gorsel": varyasyonlar[0] if varyasyonlar else None,
        "yuz_meta": yuz_meta
    })


def kanon_sec(persona_id, gorsel_yol):
    depolama.persona_guncelle(persona_id, {"kanon_gorsel": gorsel_yol})


def prompt_yap(sahne, persona):
    """Sahne + persona anchor'u birleştirir. Anchor her zaman başta."""
    anchor = persona.get("anchor_prompt", "")
    return f"{anchor}, {sahne}, social media photo, 9:16 aspect ratio, high detail, natural lighting"


def _anchor_yap(ad, yas, ten, sac, goz, stil, kisilik_tanimi):
    parcalar = [
        f"photorealistic portrait of a {yas} year old woman" if "kadın" in (stil or "").lower() or "kadin" in (stil or "").lower()
        else f"photorealistic portrait of a {yas} year old person",
        f"{ten} skin" if ten else "",
        f"{sac} hair" if sac else "",
        f"{goz} eyes" if goz else "",
        f"wearing {stil}" if stil else "",
        f"{kisilik_tanimi} vibe" if kisilik_tanimi else "",
        "same face identity across all images",
    ]
    return ", ".join(p for p in parcalar if p)


def persona_listele():
    return depolama.persona_listele()


def persona_al(pid):
    return depolama.persona_al(pid)
