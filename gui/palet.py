# -*- coding: utf-8 -*-
"""Ortak premium palet + vesikalık foto yardımcısı.

Not: Bu modül gui.ana_pencere'yi import ETMEMELİ (döngüsel import yok).
"""

from pathlib import Path

VARLIK = Path(__file__).resolve().parent.parent / "varlik"

# --- retro+ premium palet ---
TEAL_KOYU = "#0A3D47"
TEAL = "#0F6B6B"
TEAL_ORTA = "#148A7D"
TEAL_VURGU = "#20B89A"
TEAL_PARLAK = "#3DDBB5"
ZEMIN = "#EDF4F3"
ZEMIN_KOYU = "#E2ECEA"
KART = "#FFFFFF"
KART_GOLGE = "#D0DEDC"
CIZGI = "#C8D8D5"
METIN_KOYU = "#0F2A2C"
METIN_SOLUK = "#5A7A78"
BASLIK_ZEMIN = TEAL_KOYU
BASLIK_SOLUK = "#7AB5AE"
YESIL = TEAL_VURGU
YESIL_KOYU = TEAL_ORTA
YESIL_METIN = "#0A5C4E"
YESIL_ACIK = "#DFF5EE"
AMBER = "#F0A830"
AMBER_KOYU = "#C07800"
AMBER_ZEMIN = "#FFF6E5"

VESIKALIK_ORAN = 3 / 4  # 3:4 vesikalık oranı


def vesikalik_foto(gorsel_yol, boyut=(160, 213)):
    """Görseli vesikalık oranında kırpıp teal çerçeveli PhotoImage döner."""
    from PIL import Image, ImageTk
    img = Image.open(gorsel_yol).convert("RGB")
    w, h = img.size
    mevcut = w / h
    if mevcut > VESIKALIK_ORAN:
        yeni_w = int(h * VESIKALIK_ORAN)
        x = (w - yeni_w) // 2
        img = img.crop((x, 0, x + yeni_w, h))
    else:
        yeni_h = int(w / VESIKALIK_ORAN)
        y = (h - yeni_h) // 2
        img = img.crop((0, y, w, y + yeni_h))
    img = img.resize(boyut, Image.LANCZOS)
    cerceve = Image.new("RGB", (boyut[0] + 10, boyut[1] + 10),
                        (32, 184, 154))
    cerceve.paste(img, (5, 5))
    return ImageTk.PhotoImage(cerceve)
