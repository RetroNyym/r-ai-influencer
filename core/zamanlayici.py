# -*- coding: utf-8 -*-
"""Basit threading zamanlayıcı: onaylı postlar saati gelince paylaşılır."""

import threading
import time

from core import depolama

_durduur = threading.Event()
_thread = None


def baslat():
    global _thread
    if _thread and _thread.is_alive():
        return
    _durduur.clear()
    _thread = threading.Thread(target=_dongu, daemon=True)
    _thread.start()


def durdur():
    _durduur.set()


def _dongu():
    while not _durduur.is_set():
        try:
            _kontrol()
        except Exception:
            pass
        _durduur.wait(60)  # her dakika kontrol


def _kontrol():
    """Saat gelen onaylı postları paylaşır."""
    from core.paylasim import instagram, tiktok

    simdi = time.localtime()
    gun = simdi.tm_wday  # 0=Pzt
    saat_str = time.strftime("%H:%M", simdi)

    # Bugünün schedule kayıtları
    with depolama.baglanti() as c:
        satirlar = c.execute(
            "SELECT * FROM schedule WHERE gun=? AND aktif=1 AND saat=?",
            (gun, saat_str)).fetchall()

    if not satirlar:
        return

    # Onay bekleyen en eski postu al
    posts = depolama.post_listele("onayli")
    if not posts:
        return

    post = posts[0]
    ig_aktif = depolama.ayar_al("ig_aktif") == "1"
    tt_aktif = depolama.ayar_al("tt_aktif") == "1"

    if ig_aktif:
        try:
            basarili, mesaj = instagram.paylas(post)
            depolama.log_ekle(post["id"], "instagram", basarili, mesaj)
        except Exception as e:
            depolama.log_ekle(post["id"], "instagram", False, str(e))

    if tt_aktif:
        try:
            basarili, mesaj = tiktok.paylas(post)
            depolama.log_ekle(post["id"], "tiktok", basarili, mesaj)
        except Exception as e:
            depolama.log_ekle(post["id"], "tiktok", False, str(e))

    if ig_aktif or tt_aktif:
        depolama.post_durum(post["id"], "paylasildi")
