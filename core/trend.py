# -*- coding: utf-8 -*-
"""Trend konu fikirleri — ücretsiz: Pollinations text + yerel şablon motoru.

Otopilot vidIQ kullanır (ücretli); burada anahtarsız yedek: niş + format
şablonlarını birleştirir, isteğe bağlı Pollinations text ile zenginleştirir.
"""

import json
import urllib.parse
import urllib.request

FORMAT_SABLONLARI = [
    {"ad": "Günlük rutin", "kalip": "{nis} rutinim — sabah{detay}",
     "detay": "15 sn'de 5 adım", "platform": "tiktok"},
    {"ad": "Öncesi/Sonrası", "kalip": "{nis} transformasyon: öncesi vs sonrası",
     "detay": "görsel karşılaştırma", "platform": "instagram"},
    {"ad": "3 İpucu", "kalip": "{nis} için bilmen gereken 3 şey",
     "detay": "liste formatı", "platform": "reels"},
    {"ad": "Sık yapılan hata", "kalip": "{nis}'de en sık yapılan hata",
     "detay": "düzeltme ile birlikte", "platform": "tiktok"},
    {"ad": "7 Gün Challenge", "kalip": "7 günde {nis} challenge",
     "detay": "günlük kısa klipler", "platform": "reels"},
    {"ad": "Gizli mekan", "kalip": "{nis} için gizli mekan/ürün",
     "detay": "keşif tonu", "platform": "instagram"},
    {"ad": "Mitos vs Gerçek", "kalip": "{nis} hakkında doğru bilinen yanlış",
     "detay": "mit yıkma", "platform": "youtube"},
    {"ad": "Bütçe dostu", "kalip": "{nis} — ₺100 altı başlangıç",
     "detay": "satın alma listesi", "platform": "tiktok"},
    {"ad": "POV", "kalip": "POV: {nis} ile yeni başlıyorsun",
     "detay": "empati kancası", "platform": "tiktok"},
    {"ad": "Haftalık özet", "kalip": "Bu haftanın {nis} özetı",
     "detay": "sıcak gündem", "platform": "instagram"},
]


def _pollinations_fikir(nis, dil="tr", sayi=5):
    """Pollinations text (ücretsiz, anahtarsız) ile konu fikri üretir."""
    prompt = (f"{dil} dilinde {nis} nişi için {sayi} viral Instagram/TikTok "
              f"içerik fikri ver. Her satır: başlık — kısa açıklama. "
              f"Sadece liste, başka metin yok.")
    url = "https://text.pollinations.ai/" + urllib.parse.quote(prompt)
    with urllib.request.urlopen(url, timeout=25) as r:
        metin = r.read().decode("utf-8", "replace")
    fikirler = []
    for satir in metin.splitlines():
        satir = satir.strip().lstrip("0123456789.-)* ").strip()
        if len(satir) < 15:
            continue
        parca = [p.strip() for p in satir.split("—") ]
        baslik = parca[0][:90]
        aciklama = parca[1][:140] if len(parca) > 1 else ""
        fikirler.append({"baslik": baslik, "aciklama": aciklama,
                         "kaynak": "pollinations"})
        if len(fikirler) >= sayi:
            break
    return fikirler


def trend_fikirleri(nis, dil="tr", sayi=8, cevrimdisi=False):
    """Niş için trend konu fikirleri listesi döner.

    Önce şablon motoru (her zaman çalışır), istenirse Pollinations ile
    zenginleştirme eklenir.
    """
    nis = (nis or "lifestyle").strip().lower()
    fikirler = []
    for s in FORMAT_SABLONLARI:
        fikirler.append({
            "baslik": s["kalip"].format(nis=nis.capitalize(), detay=""),
            "aciklama": f"{s['detay']} · format: {s['ad']}",
            "platform": s["platform"],
            "kaynak": "sablon",
        })
    if not cevrimdisi:
        try:
            zengin = _pollinations_fikir(nis, dil, sayi=6)
            # şablonların arasına serpiştir
            for i, z in enumerate(zengin):
                z["platform"] = "reels" if i % 2 else "tiktok"
                fikirler.insert(min(len(fikirler), 2 + i * 2), z)
        except Exception:
            pass  # çevrimdışı/engelli: şablonlar yeter
    return fikirler[:sayi]


def fikri_post_uret(persona_id, fikir):
    """Bir trend fikrinden post üretir (Pollinations görsel + caption)."""
    from core import uretim
    from core.kisilik import prompt_yap, persona_al
    persona = persona_al(persona_id)
    if not persona:
        raise ValueError("Persona yok")
    sahne = f"{fikir['baslik']} — {fikir.get('aciklama', '')}"
    post = uretim.uretim_yap(persona_id, sahne) if hasattr(uretim, "uretim_yap") else None
    if post is None:
        # toplu_uret tekil kullan
        posts = uretim.toplu_uret(persona_id, 1)
        if not posts:
            raise RuntimeError("Post üretilemedi")
        post = posts[0]
    return post
