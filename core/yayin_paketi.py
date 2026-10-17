# -*- coding: utf-8 -*-
"""Yayın paketi: caption, hashtag, en iyi saat, platform uyum notu, bölüm/metin.

Çıktı: uretilen/paket/post_<id>/YAYIN-PAKETI.md + yayin.json
"""

import time
from pathlib import Path

from core import depolama, skorlama
from core.atomik import atomik_json_yaz, atomik_yaz

# IG/TikTok için genel kabul görmüş saat aralıkları (yerel saat, hedef kitle TR varsayımı)
EN_IYI_SAHALAR = {
    "instagram": ["12:00-13:00 (öğle molası)", "19:00-21:00 (akşam yoğunluğu)",
                  "Pzt-Per en iyi; Pazar 11:00-13:00"],
    "tiktok": ["07:00-09:00 (sabah)", "12:00-14:00 (öğle)",
               "19:00-23:00 (akşam-zirve)"],
    "youtube": ["15:00-17:00 (ABD öğleden sonrası)", "18:00-21:00 (akşam)"],
}

UYUM_NOTLARI = [
    "Gerçekçi yapay görsel/ses kullandıysan platform ayarlarında "
    "\"sentetik/içerik\" etiketini işaretle.",
    "Başkasının içeriğini izinsiz yeniden yüklemek telif ihlalidir; "
    "kalıbı al, içeriği kendin üret.",
    "Aynı görsel setini art arda 3+ kez paylaşma; algoritma "
    "tekrarlayan içerik riski verir.",
    "AI etiketi kuralları platformdan platforma değişir; yayın öncesi "
    "kendi hesabından doğrula.",
]


def yayin_paketi_uret(post_id, platform="instagram"):
    """Seçili post için yayın paketi üretir (MD + JSON)."""
    post = depolama.post_al(post_id)
    if not post:
        raise ValueError(f"Post yok: {post_id}")
    persona = depolama.persona_al(post.get("persona_id")) if post.get("persona_id") else None

    caption = (post.get("caption") or "").strip()
    hashtags = (post.get("hashtags") or "").strip()
    # hashtagleri caption'ta yoksa ekle
    if hashtags and hashtags not in caption:
        tam_metin = f"{caption}\n\n{hashtags}".strip()
    else:
        tam_metin = caption

    skor = skorlama.caption_skoru(tam_metin, platform)
    alternatifler = skorlama.alternatif_oneriler(caption, adet=3, platform=platform)

    paket_klasor = Path(depolama.URETILEN_KLASOR) / "paket" / f"post_{post_id}"
    paket_klasor.mkdir(parents=True, exist_ok=True)

    # hashtag listesi
    import re
    hash_liste = re.findall(r"#\w+", tam_metin)
    if not hash_liste and persona:
        nis = (persona.get("nis") or "ai").lower()
        hash_liste = [f"#{nis}", "#ai", "#virtualinfluencer", "#aiart", "#ootd"]

    yayin = {
        "surum": 1,
        "post_id": post_id,
        "platform": platform,
        "olusturma": time.time(),
        "caption": caption,
        "caption_tam": tam_metin,
        "hashtagler": hash_liste[:15],
        "skor": skor,
        "alternatifler": alternatifler,
        "en_iyi_saatler": EN_IYI_SAHALAR.get(platform, EN_IYI_SAHALAR["instagram"]),
        "gorsel_yol": post.get("gorsel_yol"),
        "persona": (persona or {}).get("ad"),
        "uyum_notlari": UYUM_NOTLARI,
    }
    atomik_json_yaz(paket_klasor / "yayin.json", yayin)
    atomik_yaz(paket_klasor / "YAYIN-PAKETI.md", _md(yayin))
    return {"klasor": str(paket_klasor), "yayin": yayin}


def _md(y):
    sat = [
        "# Yayın Paketi",
        "",
        f"Post: #{y['post_id']} · Platform: {y['platform']} · "
        f"Persona: {y.get('persona') or '-'}",
        "",
        "## Caption (kopyala-yapıştır)",
        "",
        "```",
        y["caption_tam"],
        "```",
        "",
        f"## Skor: {y['skor']['puan']}/100 — {y['skor'].get('degerlendirme', '')}",
        "",
    ]
    for tip, metin in y["skor"]["maddeler"]:
        ikon = {"iyi": "✓", "orta": "~", "zayıf": "✗", "hata": "!"}.get(tip, "-")
        sat.append(f"- {ikon} {metin}")
    if y["skor"]["oneriler"]:
        sat += ["", "### Öneriler"]
        for o in y["skor"]["oneriler"]:
            sat.append(f"1. {o}")
    if y["alternatifler"]:
        sat += ["", "## Alternatif caption'lar"]
        for i, a in enumerate(y["alternatifler"], 1):
            sat += [f"", f"**{i})**", "```", a, "```"]
    sat += ["", "## Hashtagler", "", " ".join(y["hashtagler"]), "",
            "## En iyi paylaşım saatleri (yerel saat)"]
    for s in y["en_iyi_saatler"]:
        sat.append(f"- {s}")
    if y.get("gorsel_yol"):
        sat += ["", "## Görsel", "", f"`{y['gorsel_yol']}`"]
    sat += ["", "## Yayın öncesi uyum notları"]
    for n in y["uyum_notlari"]:
        sat.append(f"1. {n}")
    return "\n".join(sat) + "\n"
