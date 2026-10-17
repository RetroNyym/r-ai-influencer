# -*- coding: utf-8 -*-
"""Çizgi film görseli üretimi + isteğe bağlı kısa klip.

Bu modül OTOMATİK senaryo YAZMAZ. Kullanıcı tam olarak hangi sahneyi
istediğini yazar; program o sahneyi (seçilen stilde) üretir ve mümkünse
kilitli kimliği uygular (tutarlı karakter).

Gerçek animasyonlu video (Kling, Runway, Pika vb.) ayrı bir video API'si
isterseniz API sekmesinden bağlayın; buradaki klip yalnızca üretilen
görsellerin yumuşak geçişli birleşimidir.
"""

import re
import time
from pathlib import Path

import cv2
import numpy as np

from core import depolama

# Çizgi film stilleri (Pollinations prompt ekleri)
STILLER = {
    "pixar": "3D pixar animation style, soft rounded features, cinematic lighting, vibrant colors",
    "anime": "anime style, cel shading, expressive eyes, clean line art, studio ghibli inspired",
    "cartoon": "2D cartoon style, bold outlines, flat colors, fun and playful",
    "watercolor": "soft watercolor illustration style, gentle brush strokes, pastel tones",
    "comic": "american comic book style, dynamic inking, halftone shading",
}

# Anchor'dan çıkarılacak ifadeler: sahneyi/STİLİ ezen çerçeveler.
# (Fiziksel tanım korunur; sadece "portrait/photorealistic" gibi
#  sahneyi portreye, stili gerçeğe çeken sözler atılır.)
_ANCHOR_AT = [
    r"\bphotorealistic(?:ly)?\b", r"\bhyperdetailed\b",
    r"\bportrait of\b", r"\bclose[- ]?up\b", r"\bheadshot\b",
    r"\bsame face identity across all images\b",
    r"\bnatural proportions\b", r"\brealistic\b", r"\bphoto\b",
    r"\bfilm grain\b", r"\bskin pores\b", r"\bno (?:doll|cgi|anime)\b",
    r"\bsony a7\w*\b", r"\b85mm\b", r"\bf/1\.4\b",
]


def _anchor_temizle(anchor):
    """Anchor'dan sahneyi/stili bozan çerçeveleri temizler (fiziksel tanım kalır)."""
    if not anchor:
        return ""
    a = anchor
    for kalip in _ANCHOR_AT:
        a = re.sub(kalip, " ", a, flags=re.IGNORECASE)
    a = re.sub(r"\s+", " ", a).strip(" ,")
    # "portrait of a 24..." → "a 24..." gibi artıkları da toparla
    a = re.sub(r"^(?:of|a|an)\s+", "", a)
    return a.strip(" ,")


def gorseller_uret(karakter_id, sahneler, stil="pixar", cikti_klasor=None,
                   genislik=768, yukseklik=1024, ilerleme_cb=None):
    """Kullanıcının yazdığı SAHNE(ler)i birebir üretir (kilitli kimlikle).

    sahneler: str (tek sahne) veya list[str] (her satır bir sahne).
    Dönen: [{"sahne", "gorsel_yol"}, ...] — başarısız olanlar atlanır.
    """
    from core import kisilik, uretim

    if isinstance(sahneler, str):
        sahneler = [s for s in sahneler.splitlines() if s.strip()]
    sahneler = [s.strip() for s in sahneler if s and s.strip()]
    if not sahneler:
        raise ValueError("En az bir sahne yazın")

    persona = kisilik.persona_al(karakter_id) if karakter_id else None
    kimlik = kisilik.kimlik_al(karakter_id) if karakter_id else None

    if cikti_klasor is None:
        cikti_klasor = depolama.URETILEN_KLASOR / "cizgfilm" / str(karakter_id or 0)
    cikti_klasor = Path(cikti_klasor)
    cikti_klasor.mkdir(parents=True, exist_ok=True)

    stil_metin = STILLER.get(stil, STILLER["pixar"])
    # SAHNE öncelikli: istenen sahne baskın, anchor sadece fiziksel tanım.
    anchor = _anchor_temizle((persona.get("anchor_prompt", "")
                              if persona else "")) or "friendly character"

    tohum = int(persona.get("seed", 0) or 0) if persona else int(time.time())

    sonuclar = []
    for i, sahne in enumerate(sahneler):
        if ilerleme_cb:
            ilerleme_cb(i + 1, len(sahneler), f"Sahne {i+1} üretiliyor...")
        prompt = (f"{sahne}, {stil_metin}, {anchor}, "
                  f"same character consistent face, full scene visible, "
                  f"cinematic composition, high detail")

        img = None
        son_hata = None
        for deneme in range(4):
            try:
                data = uretim.gorsel_uret(prompt, seed=tohum + i * 13 + deneme,
                                          genislik=genislik, yukseklik=yukseklik)
                img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
                if img is not None:
                    break
            except Exception as e:
                son_hata = e
                time.sleep(3 + deneme * 2)
        if img is None:
            ilerleme_cb and ilerleme_cb(i + 1, len(sahneler),
                                        f"Sahne {i+1} atlandı ({son_hata})")
            continue

        if kimlik:
            try:
                from core import yuz_degistir
                degis = yuz_degistir.kimlik_uygula(img, kimlik)
                if degis is not None:
                    img = degis
            except Exception:
                pass

        yol = cikti_klasor / f"sahne_{i+1}_{int(time.time())}.jpg"
        cv2.imwrite(str(yol), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        sonuclar.append({"sahne": sahne, "gorsel_yol": str(yol)})
        time.sleep(1.2)

    return sonuclar


def klip_yap(gorsel_yollar, cikti_yol, kare_sure=1.6, gecis=0.5):
    """Üretilen görsellerden yumuşak geçişli kısa bir MP4 klip kurar (sessiz).

    Gerçek animasyon DEĞİLDİR; sadece görsellerin geçişli birleşimidir.
    """
    import subprocess
    from core import video as video_mod

    if not video_mod.ffmpeg_var_mi():
        raise RuntimeError("ffmpeg bulunamadı.")
    gorsel_yollar = [str(g) for g in gorsel_yollar]
    n = len(gorsel_yollar)
    if n == 0:
        raise ValueError("Görsel listesi boş")
    for g in gorsel_yollar:
        if not Path(g).is_file():
            raise FileNotFoundError(f"Görsel yok: {g}")

    cikti_yol = Path(cikti_yol)
    cikti_yol.parent.mkdir(parents=True, exist_ok=True)

    W, H = 768, 1024
    gecis = max(0.1, min(gecis, kare_sure * 0.8))

    parcalar = []
    for i in range(n):
        parcalar.append(
            f"[{i}:v]scale={W}:{H}:force_original_aspect_ratio=increase,"
            f"crop={W}:{H},fps=30,zoompan=z='min(zoom+0.0006,1.08)':d=1:"
            f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':s={W}x{H},"
            f"format=yuv420p,settb=AVTB[f{i}]")

    if n == 1:
        filtre = ";".join(parcalar) + ";[f0]null[vout]"
    else:
        gecti = 0.0
        akis = "[f0]"
        for i in range(1, n):
            gecti += kare_sure - gecis
            cikti_et = "[vx]" if i == n - 1 else f"[x{i}]"
            parcalar.append(
                f"{akis}[f{i}]xfade=transition=fade:duration={gecis:.3f}:"
                f"offset={gecti:.3f}{cikti_et}")
            akis = cikti_et
        filtre = ";".join(parcalar) + ";[vx]format=yuv420p[vout]"

    toplam = kare_sure * n - gecis * (n - 1)

    komut = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for g in gorsel_yollar:
        komut += ["-loop", "1", "-t", f"{kare_sure:.3f}", "-i", g]
    komut += ["-filter_complex", filtre, "-map", "[vout]",
              "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
              "-movflags", "+faststart", "-t", f"{toplam:.3f}"]

    part = cikti_yol.with_suffix(cikti_yol.suffix + ".part")
    komut += ["-f", "mp4", str(part)]
    r = subprocess.run(komut, capture_output=True, text=True, timeout=600)
    if r.returncode != 0 or not part.is_file() or part.stat().st_size < 1000:
        hata = (r.stderr or "")[-600:]
        try:
            part.unlink()
        except OSError:
            pass
        raise RuntimeError(f"ffmpeg klip hatası: {hata}")

    import os
    os.replace(part, cikti_yol)
    return {"cikti": str(cikti_yol),
            "sureSn": round(video_mod.ffprobe_sure(cikti_yol), 2),
            "boyut_mb": round(cikti_yol.stat().st_size / 1e6, 2),
            "gorsel": n}
