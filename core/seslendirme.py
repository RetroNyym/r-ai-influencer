# -*- coding: utf-8 -*-
"""Seslendirme: edge-tts (ücretsiz, resmî değil) → gTTS (Google Translate) yedeği.

Çıktı: parts/NNN.mp3 + zamanlama.json (paragraf başına başlangıç/süre).
Dayanıklı: tmp klasöre yazılır, tamamı başarılıysa parts'a alınır.
"""

import asyncio
import json
import os
import subprocess
import time
from pathlib import Path

from core.atomik import atomik_json_yaz, json_oku

BOSLUK = 0.35  # paragraflar arası nefes payı (sn)

SESLER = {
    "tr": "tr-TR-AhmetNeural",
    "en": "en-US-GuyNeural",
    "de": "de-DE-ConradNeural",
    "fr": "fr-FR-HenriNeural",
    "es": "es-ES-AlvaroNeural",
}


def ffprobe_sure(dosya):
    """mp3 süresini ffprobe ile ölçer (sn)."""
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json",
             "-show_format", str(dosya)],
            capture_output=True, text=True, timeout=30)
        bilgi = json.loads(r.stdout or "{}")
        return float(bilgi.get("format", {}).get("duration", 0))
    except Exception:
        return 0.0


def _edge_uret(metin, hedef, ses, hiz):
    import edge_tts

    async def _run():
        c = edge_tts.Communicate(metin, ses, rate=hiz)
        await c.save(str(hedef))

    asyncio.run(_run())


def _gtts_uret(metin, hedef, dil):
    from gtts import gTTS
    t = gTTS(metin, lang=dil)
    t.save(str(hedef))


def motor_sirasi(motor_secimi="otomatik"):
    if motor_secimi == "edge":
        return ["edge"]
    if motor_secimi == "gtts":
        return ["gtts"]
    return ["edge", "gtts"]


def parca_uret(metin, hedef, ses="tr-TR-AhmetNeural", hiz="+0%",
               dil="tr", motor_secimi="otomatik"):
    """Tek paragrafı seslendirir. Başarılı motoru döner."""
    son_hata = None
    for motor in motor_sirasi(motor_secimi):
        try:
            if motor == "edge":
                _edge_uret(metin, hedef, ses, hiz)
            else:
                _gtts_uret(metin, hedef, dil)
            if os.path.getsize(hedef) > 100:
                return motor
            raise OSError("boş ses dosyası")
        except Exception as e:
            son_hata = e
            try:
                os.remove(hedef)
            except OSError:
                pass
    raise RuntimeError(f"Seslendirme başarısız: {son_hata}")


def seslendir(paragraflar, cikti_klasor, ses=None, hiz="+0%", dil="tr",
              motor_secimi="otomatik", ilerleme_cb=None, yeniden=False):
    """Paragrafları seslendirir; zamanlama.json döner.

    Dayanıklı: parts.tmp'ye yazar; hepsi başarılı olunca parts'a alır.
    Tamamlanan parçalar yeniden üretilmez (sha cache).
    """
    cikti_klasor = Path(cikti_klasor)
    parts = cikti_klasor / "parts"
    tmp = cikti_klasor / "parts.tmp"
    ses = ses or SESLER.get(dil, SESLER["tr"])
    n = len(paragraflar)
    if not n:
        raise ValueError("Seslendirilecek paragraf yok")

    zamanlama_yol = cikti_klasor / "zamanlama.json"
    if not yeniden and zamanlama_yol.is_file():
        eski = json_oku(zamanlama_yol)
        if eski and eski.get("paragrafSayisi") == n and \
                eski.get("metinOzeti") == _ozet(paragraflar):
            return eski

    tmp.mkdir(parents=True, exist_ok=True)
    if yeniden:
        import shutil
        shutil.rmtree(tmp, ignore_errors=True)
        tmp.mkdir(parents=True, exist_ok=True)

    sonuclar = []
    ardisik_hata = 0
    son_motor = None
    for i, p in enumerate(paragraflar):
        mp3 = tmp / f"{i:03d}.mp3"
        meta_yol = tmp / f"{i:03d}.json"
        meta = json_oku(meta_yol)
        metin_sade = " ".join(str(p).split())
        if not yeniden and meta and meta.get("metin") == metin_sade and \
                mp3.is_file() and mp3.stat().st_size > 100:
            sonuclar.append(meta)
        else:
            try:
                son_motor = parca_uret(metin_sade, mp3, ses, hiz, dil, motor_secimi)
                sure = ffprobe_sure(mp3) or 2.0
                meta = {"no": i, "metin": metin_sade, "sureSn": round(sure, 3),
                        "bayt": mp3.stat().st_size, "motor": son_motor}
                atomik_json_yaz(meta_yol, meta)
                sonuclar.append(meta)
                ardisik_hata = 0
            except Exception as e:
                ardisik_hata += 1
                sonuclar.append({"no": i, "metin": metin_sade, "sureSn": 2.0,
                                 "bayt": 0, "hata": str(e)})
                if ardisik_hata >= 3:
                    raise RuntimeError(
                        f"Ardışık {ardisik_hata} paragraf seslendirilemedi: {e}")
        if ilerleme_cb:
            ilerleme_cb(i + 1, n)

    # tmp → parts (atomik)
    if parts.exists():
        import shutil
        eski = cikti_klasor / "parts.eski"
        if eski.exists():
            shutil.rmtree(eski, ignore_errors=True)
        os.replace(parts, eski)
        shutil.rmtree(eski, ignore_errors=True)
    os.replace(tmp, parts)

    # zamanlama
    bas = 0.0
    satirlar = []
    for s in sonuclar:
        satirlar.append({"no": s["no"], "dosya": f"parts/{s['no']:03d}.mp3",
                         "sureSn": s["sureSn"], "baslangicSn": round(bas, 3),
                         "metin": s["metin"]})
        bas += s["sureSn"] + BOSLUK
    toplam = bas - BOSLUK if n else 0.0
    zamanlama = {
        "surum": 1, "olusturma": time.time(), "dil": dil, "ses": ses,
        "motor": son_motor or "gtts", "hiz": hiz, "bosluk": BOSLUK,
        "paragrafSayisi": n, "toplamSn": round(toplam, 2),
        "metinOzeti": _ozet(paragraflar), "paragraflar": satirlar,
    }
    atomik_json_yaz(zamanlama_yol, zamanlama)
    return zamanlama


def ornek_uret(cikti_yol, metin=None, ses=None, dil="tr", motor_secimi="otomatik"):
    """5 sn'lik ses örneği üretir."""
    metin = metin or "Bu, seçilen sesin kısa bir örneğidir. Sana nasıl geliyor?"
    ses = ses or SESLER.get(dil, SESLER["tr"])
    motor = parca_uret(metin, cikti_yol, ses, "+0%", dil, motor_secimi)
    return {"dosya": str(cikti_yol), "motor": motor,
            "sureSn": round(ffprobe_sure(cikti_yol), 2)}


def _ozet(paragraflar):
    import hashlib
    birlesik = "\n".join(" ".join(str(p).split()) for p in paragraflar)
    return hashlib.sha1(birlesik.encode("utf-8")).hexdigest()[:12]
