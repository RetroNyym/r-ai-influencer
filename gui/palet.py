# -*- coding: utf-8 -*-
"""Ortak ultra-premium DARK palet + vesikalık foto yardımcısı.

Not: Bu modül gui.ana_pencere'yi import ETMEMELİ (döngüsel import yok).
Değişken ADLARI açık temadan devralınmıştır; değerler gece laciverti /
antrasit / turkuaz karanlık temaya göre tanımlıdır.
"""

from pathlib import Path

VARLIK = Path(__file__).resolve().parent.parent / "varlik"

# --- retro+ ultra premium dark palet ---
SIDEBAR = "#0B1424"        # sidebar / üst bar / alt bar zemini
ZEMIN = "#0A1220"          # sayfa zemini (gece laciverti)
ZEMIN_KOYU = "#070C18"     # daha koyu zemin (trough, scroll alanı)
KART = "#131C2E"           # antrasit panel / kart zemini
KART_GOLGE = "#1A2540"     # kart kenarı / gölge
CIZGI = "#243149"          # ince kenarlık
METIN_KOYU = "#E8EEF9"     # ana metin (açık lacivert-beyaz)
METIN_SOLUK = "#8A9AB8"    # soluk/ikincil metin
TEAL_KOYU = "#3FD9BE"      # başlık/vurgu rengi (parlak turkuaz)
TEAL = "#0F766E"           # koyu turkuaz (beyaz metinli rozet/buton zemini)
TEAL_ORTA = "#148A7D"      # orta turkuaz (pressed)
TEAL_VURGU = "#20B89A"     # vurgu (yesil buton, seçili satır)
TEAL_PARLAK = "#3DDBB5"    # parlak (hover)
BASLIK_ZEMIN = "#0B1424"   # başlık/çubuk zemini (navy)
BASLIK_SOLUK = "#7A8CA8"   # çubuk üzerinde soluk metin
YESIL = TEAL_VURGU
YESIL_KOYU = TEAL_ORTA
YESIL_METIN = "#5FE3C0"    # koyu yeşil zemin üzerinde parlak metin
YESIL_ACIK = "#12312B"     # koyu yeşil vurgu zemini (ipucu/aktif)
AMBER = "#F0A830"
AMBER_KOYU = "#C07800"
AMBER_ZEMIN = "#2E2415"    # koyu amber vurgu zemini
HATA = "#FF6B6B"           # hata metni (dark zeminde okunur)

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
