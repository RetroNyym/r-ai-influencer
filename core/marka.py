# -*- coding: utf-8 -*-
"""Marka kiti: persona için 1:1 profil görseli + biyografi + kapak/metin paketi.

Çıktı: uretilen/marka/<persona_id>/
  profil.png (1024x1024), kapak_onerisi.txt, biyografi.txt, MARKA-KITI.md
"""

import time
from pathlib import Path

from core import depolama, uretim
from core.atomik import atomik_yaz


def marka_kiti_uret(persona_id):
    persona = depolama.persona_al(persona_id)
    if not persona:
        raise ValueError(f"Persona yok: {persona_id}")

    klasor = Path(depolama.URETILEN_KLASOR) / "marka" / str(persona_id)
    klasor.mkdir(parents=True, exist_ok=True)

    # 1:1 profil görseli
    prompt = (
        f"professional headshot portrait of a virtual influencer, "
        f"{persona.get('anchor_prompt', persona.get('ad', 'AI influencer'))}, "
        f"square format, soft studio light, clean background, instagram profile photo, "
        f"photorealistic, high detail"
    )
    profil_yol = klasor / "profil.png"
    veri = uretim.gorsel_uret(prompt, persona.get("seed", 42),
                              genislik=1024, yukseklik=1024)
    profil_yol.write_bytes(veri)

    # biyografi
    bio = _biyografi(persona)
    atomik_yaz(klasor / "biyografi.txt", bio)

    # kapak önerisi (IG story / YT banner metni)
    kapak = _kapak_onerisi(persona)
    atomik_yaz(klasor / "kapak_onerisi.txt", kapak)

    md = (
        f"# Marka Kit — {persona.get('ad', '')}\n\n"
        f"- Niş: {persona.get('nis', '')}\n"
        f"- Marka sesi: {persona.get('marka_sesi', '')}\n"
        f"- Seed: {persona.get('seed', '')}\n\n"
        f"## Biyografi\n\n{bio}\n\n"
        f"## Kapak / banner önerisi\n\n{kapak}\n\n"
        f"## Profil görseli\n\n`{profil_yol}` (1024×1024)\n"
    )
    atomik_yaz(klasor / "MARKA-KITI.md", md)
    return {"klasor": str(klasor), "profil": str(profil_yol),
            "biyografi": bio, "kapak": kapak}


def _biyografi(p):
    ad = p.get("ad", "Ben")
    nis = (p.get("nis") or "lifestyle").lower()
    stil = (p.get("stil") or "").split(",")[0].strip()
    satirlar = [
        f"{ad} ✨ {nis.capitalize()} · {stil}",
        f"{p.get('yas', '')} · {p.get('marka_sesi', 'authentic').split(',')[0].strip()}",
        "Yeni içerik her gün 🔔",
        f"👇 {nis} ipuçları ve günlük ilham",
    ]
    return "\n".join(s for s in satirlar if s.strip() and s.strip() != "·")


def _kapak_onerisi(p):
    ad = p.get("ad", "")
    nis = (p.get("nis") or "lifestyle").capitalize()
    return (
        f"Kanal adı: {ad} · {nis}\n"
        f"Slogan: {ad} ile her gün bir adım daha ileri\n"
        f"Renk paleti: teal #20B89A · koyu #0A3D47 · açık #EDF4F3\n"
        f"Banner metni (güvenli alan): \"{nis} tutkunu | {ad}\"\n"
        f"Not: Gerçekçi AI görsel kullandıysan biosuna 'AI virtual influencer' yaz.\n"
    )
