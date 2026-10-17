# -*- coding: utf-8 -*-
"""Toplu üretim kuyruğu: manifest → sırayla post/video işleri.

Durumlar: bekliyor → calisiyor → bitti | hata | duraklatildi
Dayanıklı: DB'de saklanır; duraklat/devam; bittiler atlanır.
"""

import threading
import time

from core import depolama

_durum = {"calisiyor": False, "durdur": False, "thread": None, "son_mesaj": ""}


def kuyruga_post_ekle(persona_id, sahne, sayi=1):
    return depolama.toplu_ekle("post", {
        "persona_id": persona_id, "sahne": sahne, "sayi": sayi})


def kuyruga_video_ekle(post_id, oran="9:16"):
    return depolama.toplu_ekle("video", {"post_id": post_id, "oran": oran})


def kuyruga_listele():
    return depolama.toplu_listele()


def kuyruga_temizle():
    depolama.toplu_temizle()


def durum():
    return dict(_durum, bekliyor=len(
        [k for k in depolama.toplu_listele() if k["durum"] == "bekliyor"]))


def calistir(ilerleme_cb=None):
    """Kuyruktaki bekleyen işleri sırayla çalıştırır (daemon thread)."""
    if _durum["calisiyor"]:
        return False
    _durum["calisiyor"] = True
    _durum["durdur"] = False
    t = threading.Thread(target=_worker, args=(ilerleme_cb,), daemon=True)
    _durum["thread"] = t
    t.start()
    return True


def duraklat():
    _durum["durdur"] = True


def _worker(ilerleme_cb=None):
    try:
        isler = [k for k in depolama.toplu_listele() if k["durum"] in ("bekliyor", "duraklatildi")]
        toplam = len(isler)
        for i, is_ in enumerate(isler):
            if _durum["durdur"]:
                depolama.toplu_durum_guncelle(is_["id"], "duraklatildi")
                _durum["son_mesaj"] = "Duraklatıldı"
                continue
            tid = is_["id"]
            depolama.toplu_durum_guncelle(tid, "calisiyor")
            _durum["son_mesaj"] = f"{i + 1}/{toplam}: {is_['tip']} işleniyor"
            if ilerleme_cb:
                ilerleme_cb(i, toplam, _durum["son_mesaj"])
            try:
                _is_calistir(is_)
                depolama.toplu_durum_guncelle(tid, "bitti")
            except Exception as e:
                depolama.toplu_durum_guncelle(tid, "hata", str(e))
        _durum["son_mesaj"] = "Kuyruk tamamlandı"
        if ilerleme_cb:
            ilerleme_cb(toplam, toplam, _durum["son_mesaj"])
    finally:
        _durum["calisiyor"] = False


def _is_calistir(is_):
    tip = is_["tip"]
    p = is_.get("parametre") or {}
    if tip == "post":
        from core import uretim
        uretim.toplu_uret(p["persona_id"], int(p.get("sayi", 1)))
    elif tip == "video":
        # onaylı postlardan video kur
        from core import seslendirme, video as video_mod
        post = depolama.post_al(p["post_id"])
        if not post or not post.get("gorsel_yol"):
            raise ValueError("Post görseli yok")
        klasor = depolama.URETILEN_KLASOR / "video" / f"post_{p['post_id']}"
        klasor.mkdir(parents=True, exist_ok=True)
        metin = (post.get("caption") or "").strip() or "Yeni içerik yakında."
        zamanlama = seslendirme.seslendir([metin], klasor / "ses")
        ses_yol = klasor / "ses" / "parts" / "000.mp3"
        video_mod.video_kur(
            [(post["gorsel_yol"], zamanlama["toplamSn"])],
            klasor / "video.mp4",
            ses_yol=str(ses_yol) if ses_yol.is_file() else None,
            oran=p.get("oran", "9:16"))
    else:
        raise ValueError(f"Bilinmeyen iş tipi: {tip}")
