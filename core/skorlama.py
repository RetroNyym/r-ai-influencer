# -*- coding: utf-8 -*-
"""Caption/başlık skorlama — ücretsiz heuristik (vidIQ'suz).

0-100 arası puan + madde madde gerekçe + alternatif öneriler.
"""

import re

CTA_KELIMELER = {
    "tr": ["takip et", "abone ol", "yorum yaz", "kaydet", "paylaş", "dene",
           "deneyin", "bak", "bakın", "öğren", "keşfet", "hemen", "şimdi",
           "denemelisin", "kaçırma", "sonuna kadar"],
    "en": ["follow", "subscribe", "comment", "save", "share", "try",
           "learn", "discover", "now", "today", "don't miss", "watch"],
}

GUC_KELIMELER = {
    "tr": ["sır", "gizli", "ücretsiz", "kolay", "hızlı", "inanılmaz",
           "şok", "kesin", "garanti", "en iyi", "vip", "özel", "yeni",
           "viral", "patlama", "kazanç", "tasarruf"],
    "en": ["secret", "free", "easy", "fast", "insane", "shocking",
           "guaranteed", "best", "exclusive", "new", "viral", "win"],
}


def _emoji_say(metin):
    return len(re.findall(
        "[\U0001F300-\U0001FAFF☀-➿️]", metin))


def caption_skoru(metin, platform="instagram", dil="tr"):
    """Caption/başlık skoru. platform: instagram|tiktok|youtube."""
    metin = (metin or "").strip()
    sonuc = {"puan": 0, "maddeler": [], "oneriler": [], "platform": platform}
    if not metin:
        sonuc["maddeler"].append(("hata", "Caption boş"))
        return sonuc

    kucuk = metin.lower()
    kelime_sayisi = len(metin.split())
    karakter = len(metin)
    emoji = _emoji_say(metin)
    hashtagler = re.findall(r"#\w+", metin)
    harfler = re.findall(r"[a-zA-ZçğıöşüÇĞİÖŞÜ]", metin)

    puan = 0

    # 1) Uzunluk (30 puan)
    if platform == "instagram":
        hedef = (120, 220)
    elif platform == "tiktok":
        hedef = (60, 150)
    else:
        hedef = (40, 100)
    if hedef[0] <= karakter <= hedef[1]:
        puan += 30
        sonuc["maddeler"].append(("iyi", f"Uzunluk ideal ({karakter} karakter)"))
    elif karakter < hedef[0]:
        puan += 12
        sonuc["maddeler"].append(("orta", f"Kısa ({karakter} karakter); "
                                          f"hedef {hedef[0]}+"))
        sonuc["oneriler"].append("Detay/hikaye ekleyerek uzat")
    else:
        puan += 16
        sonuc["maddeler"].append(("orta", f"Uzun ({karakter} karakter); "
                                          f"hedef ≤{hedef[1]}"))
        sonuc["oneriler"].append("İlk 2-3 cümleyi daha çarpıcı yap, gerisini kısalt")

    # 2) Emoji (15 puan)
    if 2 <= emoji <= 6:
        puan += 15
        sonuc["maddeler"].append(("iyi", f"{emoji} emoji — dengeli"))
    elif emoji == 1:
        puan += 8
        sonuc["maddeler"].append(("orta", "Tek emoji; 2-4 dene"))
    elif emoji > 8:
        puan += 8
        sonuc["maddeler"].append(("orta", f"{emoji} emoji — fazla, 2-6'ya düşür"))
    else:
        puan += 3
        sonuc["maddeler"].append(("zayıf", "Emoji yok; 2-4 tane ekle"))
        sonuc["oneriler"].append("İlgili 2-4 emoji ekle")

    # 3) Hashtag (15 puan)
    n_hash = len(hashtagler)
    if 3 <= n_hash <= 10:
        puan += 15
        sonuc["maddeler"].append(("iyi", f"{n_hash} hashtag — dengeli"))
    elif 1 <= n_hash <= 2:
        puan += 8
        sonuc["maddeler"].append(("orta", "Az hashtag; 3-8 dene"))
    elif n_hash > 12:
        puan += 6
        sonuc["maddeler"].append(("orta", f"{n_hash} hashtag — fazla"))
    else:
        puan += 2
        sonuc["maddeler"].append(("zayıf", "Hashtag yok"))
        sonuc["oneriler"].append("Nişine uygun 5-8 hashtag ekle")

    # 4) CTA (15 puan)
    cta = CTA_KELIMELER.get(dil, CTA_KELIMELER["tr"]) + CTA_KELIMELER["en"]
    if any(k in kucuk for k in cta):
        puan += 15
        sonuc["maddeler"].append(("iyi", "Eyleme çağrı var (CTA)"))
    else:
        puan += 3
        sonuc["maddeler"].append(("zayıf", "CTA yok"))
        sonuc["oneriler"].append('"Kaydet ve dene!" gibi bir CTA ekle')

    # 5) Güç kelimesi (10 puan)
    guc = GUC_KELIMELER.get(dil, GUC_KELIMELER["tr"]) + GUC_KELIMELER["en"]
    bulunan = [k for k in guc if k in kucuk]
    if bulunan:
        puan += 10
        sonuc["maddeler"].append(("iyi", f"Güç kelimesi: {', '.join(bulunan[:3])}"))
    else:
        puan += 3
        sonuc["maddeler"].append(("orta", "Güç kelimesi yok"))
        sonuc["oneriler"].append('"gizli", "ücretsiz", "en iyi" gibi güç kelimesi ekle')

    # 6) Soru / hook (10 puan)
    if "?" in metin or any(k in kucuk for k in ["nasıl", "neden", "hangi",
                                                "how", "why", "what"]):
        puan += 10
        sonuc["maddeler"].append(("iyi", "Soru/hook var — merak uyandırır"))
    else:
        puan += 3
        sonuc["maddeler"].append(("orta", "Soru/hook yok"))
        sonuc["oneriler"].append("İlk satıra merak uyandıran bir soru ekle")

    # 7) İlk satır gücü (5 puan)
    ilk = metin.split("\n")[0][:80]
    if ilk and ilk[0].isdigit() or any(x in ilk for x in ["!", "?", "💰", "🔥", "✨"]):
        puan += 5
        sonuc["maddeler"].append(("iyi", "İlk satır dikkat çekici"))
    else:
        puan += 2
        sonuc["maddeler"].append(("orta", "İlk satır daha çarpıcı olabilir"))

    sonuc["puan"] = min(100, puan)
    if sonuc["puan"] >= 75:
        sonuc["degerlendirme"] = "Güçlü"
    elif sonuc["puan"] >= 50:
        sonuc["degerlendirme"] = "Orta — geliştirilebilir"
    else:
        sonuc["degerlendirme"] = "Zayıf — önerileri uygula"
    return sonuc


def alternatif_oneriler(metin, adet=3, platform="instagram", dil="tr"):
    """Mevcut caption'tan şablon rotasyonuyla alternatif üretir (API'siz)."""
    temel = (metin or "").split("\n")[0].strip()
    if not temel:
        return []
    sonuclar = []
    sablonlar = [
        f"{'🔥 ' if dil == 'tr' else '🔥 '}{temel} — sonuna kadar kaydet!",
        f"{'✨ '}{temel}\n\nNeden mi? Aşağıda adım adım anlattım 👇",
        f"{'💡 '}{temel}\n\nSen de dene ve sonucu yorumlara yaz!",
        f"{temel} {'(ve çoğu kişi bunu bilmiyor 🤫)'}",
        f"{'Yeni keşif: '}{temel} {'✨'}",
    ]
    for s in sablonlar[:adet]:
        s = s.strip()
        if s != metin.strip():
            sonuclar.append(s)
    return sonuclar
