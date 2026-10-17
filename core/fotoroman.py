# -*- coding: utf-8 -*-
"""Fotoroman: aynı karakterden 4-6 karelik hikâye serisi üretir.

Her kare bir sahne prompt'u + caption ile post kuyruğuna eklenir
(durum: onay_bekliyor). Anlatı yayı: giriş → doruk → sonuç.
"""

import time
from pathlib import Path

from core import depolama, uretim
from core.kisilik import persona_al, prompt_yap
from core.atomik import atomik_json_yaz

KARE_BEATLERI = [
    ("giris", "establishing shot, the character arrives, warm light"),
    ("gelisme", "the character in action, mid-motion, dynamic angle"),
    ("detay", "close-up detail shot, hands or object, shallow depth"),
    ("doruk", "climactic moment, dramatic light, emotional peak"),
    ("sonuc", "resolution, satisfied smile, golden hour, calm"),
    ("final", "walking away into distance, back view, cinematic"),
]


def fotoroman_uret(persona_id, konu, kare_sayisi=5, ilerleme_cb=None):
    """4-6 karelik fotoroman serisi üretir; post listesi döner."""
    persona = persona_al(persona_id)
    if not persona:
        raise ValueError("Persona yok")
    kare_sayisi = max(4, min(6, int(kare_sayisi)))

    klasor = Path(depolama.URETILEN_KLASOR) / "fotoroman" / str(persona_id)
    klasor.mkdir(parents=True, exist_ok=True)

    beatler = KARE_BEATLERI[:kare_sayisi]
    posts = []
    hatalar = []
    for i, (beat, istem) in enumerate(beatler):
        if ilerleme_cb:
            ilerleme_cb(i, kare_sayisi, f"Kare {i + 1}/{kare_sayisi}: {beat}")
        sahne = (f"{konu} — {beat}: {istem}")
        prompt = prompt_yap(sahne, persona)
        seed = (persona.get("seed") or 42) + i * 7
        gorsel = klasor / f"kare_{i + 1:02d}_{beat}.jpg"
        try:
            veri = uretim.gorsel_uret(prompt, seed, genislik=1024, yukseklik=1280)
            gorsel.write_bytes(veri)
        except Exception as e:
            hatalar.append(f"kare {i + 1}: {e}")
            if ilerleme_cb:
                ilerleme_cb(i + 1, kare_sayisi, f"Kare {i + 1} atlandı: {e}")
            continue
        caption = (f"{persona.get('ad', '')} — {konu} (kare {i + 1}/{kare_sayisi})\n"
                   f"#fotoroman #{beat} #{(persona.get('nis') or 'ai')}")
        pid = depolama.post_ekle({
            "persona_id": persona_id,
            "sahne": f"Fotoroman: {konu} — {beat}",
            "prompt": prompt,
            "gorsel_yol": str(gorsel),
            "caption": caption,
            "hashtags": f"#fotoroman #{(persona.get('nis') or 'ai')} #ai",
            "durum": "onay_bekliyor",
        })
        posts.append({"post_id": pid, "gorsel": str(gorsel), "beat": beat})
    if not posts:
        raise RuntimeError("Hiçbir kare üretilemedi: " + "; ".join(hatalar[:3]))

    meta = {"persona_id": persona_id, "konu": konu, "kareler": posts,
            "olusturma": time.time()}
    atomik_json_yaz(klasor / "fotoroman.json", meta)
    if ilerleme_cb:
        ilerleme_cb(kare_sayisi, kare_sayisi, f"Fotoroman tamam: {len(posts)} kare")
    return posts
