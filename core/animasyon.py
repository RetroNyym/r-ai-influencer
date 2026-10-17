# -*- coding: utf-8 -*-
"""Senaryo tabanlı kısa çizgi film / shorts üretimi.

Program önce konudan bir SENARYO yazar (Pollinations ücretsiz metin LLM,
şablon yedeği ile). Sonra her bölüm için:
  1) kilitli kimlikle görsel üretir (tutarlı karakter),
  2) repliği seslendirir (gTTS),
  3) ffmpeg ile dikey (9:16) senkron bir short'a birleştirir.
"""

import json
import re
import time
import urllib.parse
import urllib.request
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

_W, _H = 720, 1280  # 9:16 shorts
_FPS = 30


# --------------------------------------------------------------------------
# Ücretsiz metin LLM (Pollinations) + şablon yedeği
# --------------------------------------------------------------------------

def _text_llm(prompt, timeout=30):
    """Pollinations ücretsiz metin uç noktası; hata/dönüş yoksa None."""
    url = "https://text.pollinations.ai/" + urllib.parse.quote(prompt[:1800])
    istek = urllib.request.Request(url, headers={"User-Agent": "r-ai-influencer/1.0"})
    try:
        with urllib.request.urlopen(istek, timeout=timeout) as r:
            metin = r.read().decode("utf-8", "ignore")
        return metin if metin and len(metin.strip()) > 20 else None
    except Exception:
        return None


def _senaryo_parse(metin, sayi):
    """'BOLUM n | SAHNE: ... | REPLIK: ...' satırlarını sök."""
    beats = []
    for satir in metin.splitlines():
        s = satir.strip()
        if not s or "SAHNE" not in s.upper():
            continue
        sahne, replik = "", ""
        for parca in [p.strip() for p in s.split("|")]:
            pu = parca.upper()
            deger = parca.split(":", 1)[1].strip() if ":" in parca else ""
            if pu.startswith("SAHNE"):
                sahne = deger
            elif pu.startswith("REPLIK") or pu.startswith("REPL"):
                replik = deger
        if sahne and len(sahne.split()) >= 4:
            beats.append({"no": len(beats) + 1, "sahne_en": sahne,
                          "replik_tr": replik})
    return beats[:sayi] if len(beats) >= 2 else []


def _senaryo_sablon(konu, sayi):
    """LLM yoksa/kötü dönerse konuya örülmüş 4 bölümlük senaryo."""
    temel = [
        (f"{konu}, wide establishing shot, character greeting the audience "
         f"with a wave, bright cheerful outdoor scene",
         f"Merhaba herkes! Bugün size {konu} hakkında harika bir şey "
         f"göstereceğim."),
        (f"close-up of the character excitedly explaining {konu}, expressive "
         f"face, soft bokeh background, warm tones",
         f"Aslında {konu} sandığınızdan çok daha eğlenceli ve kolay."),
        (f"the character actively demonstrating {konu}, dynamic action pose, "
         f"motion blur on hands, vibrant colors, mid-shot",
         f"Hadi gelin birlikte deneyelim — görün, bu kadar basit!"),
        (f"the character smiling warmly at camera, {konu} subtly in "
         f"background, golden hour lighting, celebratory mood",
         f"Beğendiyseniz takip etmeyi unutun, {konu} serimiz devam edecek!"),
    ]
    return [{"no": i + 1, "sahne_en": t[0], "replik_tr": t[1]}
            for i, t in enumerate(temel[:max(2, min(sayi, 4))])]


def senaryo_uret(konu, sayi=4, karakter="Karakter"):
    """Konudan kısa çizgi film senaryosu yazar (LLM + şablon yedeği).

    Dönen: [{"no", "sahne_en", "replik_tr"}, ...] — tutarlı ve oynanabilir.
    """
    konu = (konu or "").strip() or "güzel bir gün"
    sayi = max(2, min(int(sayi), 6))

    beklenen = "\n".join(
        f"BOLUM {i+1} | SAHNE: ... | REPLIK: ..."
        for i in range(sayi))
    istek = (
        "Sen bir sosyal medya (Reels/TikTok shorts) senaristisin.\n"
        f"Konu: {konu}\n"
        f"Karakter: {karakter} — genç, enerjik, dost canlısı bir influencer.\n"
        f"\nBu konuda {sayi} bölümlük çok kısa bir çizgi film senaryosu yaz.\n"
        "Her bölüm TEK satır ve tam şu formatta olsun:\n"
        f"{beklenen}\n"
        "\nKURALLAR:\n"
        "- SAHNE: İngilizce olacak (görsel üretim prompt'u olarak kullanılacak), "
        "12-20 kelime, karakterin ne yaptığı ve ortam.\n"
        "- REPLIK: Türkçe olacak, doğal, konuşma dili, en fazla 15 kelime.\n"
        f"- Toplam tam {sayi} satır. Başka hiçbir şey yazma (başlık/yorum yok).\n"
        "- Bölümler mantıklı bir akışta ilerlesin: giriş → gelişme → gelişme → kapanış.\n"
        f"\n{beklenen}"
    )

    metin = _text_llm(istek)
    beats = _senaryo_parse(metin, sayi) if metin else []
    if len(beats) < 2:
        beats = _senaryo_sablon(konu, sayi)
    return beats


# --------------------------------------------------------------------------
# Görsel + ses üretimi
# --------------------------------------------------------------------------

def bolum_gorseli_uret(persona, beat, stil, kimlik_embedding, seed):
    """Tek bölüm için kilitli kimlikli çizgi film görseli üretir (ndarray).

    Pollinations ara sıra 402/rate-limit döndürür; bu yüzden kısa bir
    deneme (retry) döngüsü vardır.
    """
    from core import uretim

    anchor = persona.get("anchor_prompt", "") if persona else ""
    if not anchor:
        anchor = "friendly cartoon character"
    stil_metin = STILLER.get(stil, STILLER["pixar"])

    prompt = (
        f"{anchor}, {stil_metin}, {beat['sahne_en']}, "
        f"same character consistent face, vertical 9:16 composition, "
        f"cinematic framing, high detail"
    )
    img = None
    son_hata = None
    for deneme in range(4):
        try:
            data = uretim.gorsel_uret(prompt, seed=seed + deneme,
                                      genislik=_W, yukseklik=_H)
            img = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
            if img is not None:
                break
        except Exception as e:
            son_hata = e
            time.sleep(3 + deneme * 2)
    if img is None:
        raise RuntimeError(f"Bölüm görseli üretilemedi: {son_hata}")

    if kimlik_embedding:
        try:
            from core import yuz_degistir
            degis = yuz_degistir.kimlik_uygula(img, kimlik_embedding)
            if degis is not None:
                img = degis
        except Exception:
            pass
    return img


def bolum_sesi_uret(replik, cikti_yol):
    """Bölüm repliğini gTTS ile seslendirir; olmazsa None."""
    if not replik:
        return None
    from core import seslendirme
    try:
        seslendirme.ornek_uret(str(cikti_yol), metin=replik)
        return str(cikti_yol) if Path(cikti_yol).is_file() else None
    except Exception:
        return None


# --------------------------------------------------------------------------
# Senkron short birleştirme
# --------------------------------------------------------------------------

def _font_yolu():
    for ad in ("segoeui.ttf", "arial.ttf", "calibri.ttf"):
        p = Path("C:/Windows/Fonts") / ad
        if p.is_file():
            return str(p).replace("\\", "/")
    return None


def _altyazi_sar(replik, max_satir=2, max_karakter=31):
    """Uzun repliği alt yazı için en fazla max_satir satıra sarmalar."""
    replik = (replik or "").strip()
    if not replik:
        return ""
    if len(replik) <= max_karakter:
        return replik

    kelimeler = replik.split()
    satirlar, mevcut = [], ""
    for k in kelimeler:
        aday = (mevcut + " " + k).strip()
        if len(aday) <= max_karakter or not mevcut:
            mevcut = aday
        else:
            satirlar.append(mevcut)
            mevcut = k
    if mevcut:
        satirlar.append(mevcut)

    # İlk max_satir satırı al; taşanı son satıra birleştir (kısalt)
    if len(satirlar) > max_satir:
        birlesik = " ".join(satirlar[max_satir - 1:])
        if len(birlesik) > max_karakter:
            birlesik = birlesik[:max_karakter - 1].rstrip() + "…"
        satirlar = satirlar[:max_satir - 1] + [birlesik]
    return "\n".join(satirlar)


def senaryo_video_yap(kareler, sesler, cikti_yol, altyazilar=None,
                      min_sure=2.4, max_sure=6.0):
    """Bölüm kareleri + bölüm seslerini SENKRON dikey short'a birleştirir.

    Her bölüm kendi süresinde oynar (ses süresi kadar), aralarında sert
    geçiş (shorts'a uygun) ve hafif Ken Burns zoom olur. Altyazı isteğe
    bağlı olarak videoya gömülür.
    """
    import subprocess
    from core import seslendirme, video as video_mod

    if not video_mod.ffmpeg_var_mi():
        raise RuntimeError("ffmpeg bulunamadı.")
    kareler = [str(k) for k in kareler]
    n = len(kareler)
    if n == 0:
        raise ValueError("Kare listesi boş")

    cikti_yol = Path(cikti_yol)
    cikti_yol.parent.mkdir(parents=True, exist_ok=True)

    # Bölüm süreleri = ses süresi (+nefes payı), sınırlar içinde
    sureler = []
    for i in range(n):
        s = min_sure
        sp = sesler[i] if sesler else None
        if sp and Path(sp).is_file():
            try:
                s = max(seslendirme.ffprobe_sure(sp) + 0.35, 2.0)
            except Exception:
                pass
        sureler.append(min(s, max_sure))

    font = _font_yolu()
    komut = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error"]
    for i in range(n):
        komut += ["-loop", "1", "-t", f"{sureler[i]:.3f}", "-i", kareler[i]]
    for i in range(n):
        sp = sesler[i] if sesler else None
        if sp and Path(sp).is_file():
            komut += ["-i", str(sp)]
        else:
            komut += ["-f", "lavfi", "-t", f"{sureler[i]:.3f}",
                      "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]

    filtreler = []
    v_etiketler = []
    for i in range(n):
        parca = (f"[{i}:v]scale={_W}:{_H}:force_original_aspect_ratio=increase,"
                 f"crop={_W}:{_H},"
                 f"zoompan=z='min(zoom+0.0005,1.08)':d=1:"
                 f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
                 f"s={_W}x{_H},fps={_FPS},format=yuv420p,settb=AVTB")

        if (altyazilar and i < len(altyazilar) and altyazilar[i]
                and font and Path(font.replace("/", "\\")).is_file()):
            tf = (cikti_yol.parent / f"altyazi_{i}.txt").resolve()
            tf.write_text(_altyazi_sar(str(altyazilar[i])), encoding="utf-8")
            # ffmpeg filtre sözdizimi için: / kullan, : ve \ ' kaçır
            tf_esc = str(tf).replace("\\", "/").replace(":", "\\:").replace("'", "\\'")
            f_esc = font.replace(":", "\\:")
            parca += (
                f",drawtext=fontfile='{f_esc}':textfile='{tf_esc}'"
                f":fontcolor=white:fontsize=30:line_spacing=4"
                f":box=1:boxcolor=black@0.45:boxborderw=12"
                f":x=(w-text_w)/2:y=h-250"
                f":text_shaping=1")

        parca += f"[v{i}]"
        filtreler.append(parca)
        v_etiketler.append(f"[v{i}]")

    filtreler.append("".join(v_etiketler) + f"concat=n={n}:v=1:a=0[vout]")

    a_etiketler = []
    for i in range(n):
        filtreler.append(
            f"[{n+i}:a]aresample=44100,aformat=channel_layouts=stereo,"
            f"apad,atrim=0:{sureler[i]:.3f},asetpts=PTS-STARTPTS[a{i}]")
        a_etiketler.append(f"[a{i}]")
    filtreler.append("".join(a_etiketler) + f"concat=n={n}:v=0:a=1[aout]")

    toplam = sum(sureler)
    komut += ["-filter_complex", ";".join(filtreler),
              "-map", "[vout]", "-map", "[aout]",
              "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
              "-c:a", "aac", "-b:a", "128k", "-ar", "44100", "-ac", "2",
              "-movflags", "+faststart", "-t", f"{toplam:.3f}"]

    part = cikti_yol.with_suffix(cikti_yol.suffix + ".part")
    komut += ["-f", "mp4", str(part)]
    r = subprocess.run(komut, capture_output=True, text=True, timeout=900)
    if r.returncode != 0 or not part.is_file() or part.stat().st_size < 1000:
        hata = (r.stderr or "")[-700:]
        try:
            part.unlink()
        except OSError:
            pass
        raise RuntimeError(f"ffmpeg short hatası: {hata}")

    import os
    os.replace(part, cikti_yol)
    return {"cikti": str(cikti_yol),
            "sureSn": round(video_mod.ffprobe_sure(cikti_yol), 2),
            "boyut_mb": round(cikti_yol.stat().st_size / 1e6, 2),
            "bolum": n,
            "bolum_sureleri": [round(s, 2) for s in sureler]}


# --------------------------------------------------------------------------
# Uçtan uca short
# --------------------------------------------------------------------------

def short_yap(persona_id, konu, stil="pixar", sayi=4, ses_acik=True,
              altyazi=True, cikti_klasor=None, ilerleme_cb=None):
    """Uçtan uca: senaryo yaz → her bölüm görsel+ses → senkron short.

    Program senaryoyu ve görsel eklemelerini KENDİSİ yapar; kullanıcı sadece
    konu verir. Kimlik kilidi varsa her bölümde aynı kişi görünür.
    """
    from core import kisilik

    persona = kisilik.persona_al(persona_id)
    if not persona:
        raise ValueError("Persona bulunamadı")
    kimlik = kisilik.kimlik_al(persona_id)

    if cikti_klasor is None:
        cikti_klasor = depolama.URETILEN_KLASOR / "shorts" / str(persona_id)
    cikti_klasor = Path(cikti_klasor)
    cikti_klasor.mkdir(parents=True, exist_ok=True)

    # 1) Senaryo
    if ilerleme_cb:
        ilerleme_cb(1, 4, "Senaryo yazılıyor...")
    senaryo = senaryo_uret(konu, sayi=sayi,
                           karakter=persona.get("ad", "Karakter"))
    (cikti_klasor / "senaryo.json").write_text(
        json.dumps(senaryo, ensure_ascii=False, indent=2), encoding="utf-8")

    base_seed = int(persona.get("seed", 0) or 0)

    # 2) Her bölüm için görsel + ses
    kareler, sesler, altyazilar = [], [], []
    toplam = len(senaryo)
    for i, beat in enumerate(senaryo):
        if ilerleme_cb:
            ilerleme_cb(2, 4, f"Bölüm {i+1}/{toplam}: görsel üretiliyor...")

        img = bolum_gorseli_uret(persona, beat, stil, kimlik,
                                 seed=base_seed + i * 13)
        kare_yol = cikti_klasor / f"bolum_{i+1}.jpg"
        cv2.imwrite(str(kare_yol), img, [cv2.IMWRITE_JPEG_QUALITY, 95])
        kareler.append(str(kare_yol))

        ses_yol = None
        if ses_acik and beat.get("replik_tr"):
            if ilerleme_cb:
                ilerleme_cb(3, 4, f"Bölüm {i+1}/{toplam}: seslendirme...")
            ses_yol = bolum_sesi_uret(beat["replik_tr"],
                                      cikti_klasor / f"ses_{i+1}.mp3")
        sesler.append(ses_yol)
        altyazilar.append(beat.get("replik_tr", "") if altyazi else "")

        time.sleep(1.2)  # rate limit

    if not kareler:
        raise RuntimeError("Hiç bölüm görseli üretilemedi (ağ hatası?).")

    # 3) Senkron short
    if ilerleme_cb:
        ilerleme_cb(4, 4, "Short birleştiriliyor...")
    video_cikti = cikti_klasor / "short.mp4"
    video_sonuc = senaryo_video_yap(kareler, sesler, video_cikti,
                                    altyazilar=altyazilar)

    return {"senaryo": senaryo, "kareler": kareler, "sesler": sesler,
            "video": video_sonuc, "klasor": str(cikti_klasor)}


# Geriye dönük uyumluluk (eski ad)
def cizgfilm_yap(persona_id, sahne, **kwargs):
    return short_yap(persona_id, sahne, **kwargs)
