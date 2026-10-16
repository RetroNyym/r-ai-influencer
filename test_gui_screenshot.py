# -*- coding: utf-8 -*-
"""GUI screenshot test — baslik + sekmeleri gorsel olarak kaydeder."""
import sys, os, time
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from PIL import ImageGrab

from core import depolama
depolama.kur()

from gui.ana_pencere import AnaPencere

TEST_KLASOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_cikti")
os.makedirs(TEST_KLASOR, exist_ok=True)

app = AnaPencere()
app.update_idletasks()
app.update()

def ekran_kaydet(isim):
    app.update()
    time.sleep(0.3)
    app.update()
    x = app.winfo_rootx()
    y = app.winfo_rooty()
    w = app.winfo_width()
    h = app.winfo_height()
    img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
    yol = os.path.join(TEST_KLASOR, isim)
    img.save(yol)
    print(f"Kaydedildi: {yol}")

# 1) Karakter sekmesi (varsayilan)
ekran_kaydet("gui_01_karakter.png")

# 2) Uretim sekmesi
app.notebook.select(1)
app.update()
time.sleep(0.2)
ekran_kaydet("gui_02_uretim.png")

# 3) Takvim sekmesi
app.notebook.select(2)
app.update()
time.sleep(0.2)
ekran_kaydet("gui_03_takvim.png")

# 4) Ayarlar sekmesi (IG/TT logolari)
app.notebook.select(3)
app.update()
time.sleep(0.2)
ekran_kaydet("gui_04_ayarlar.png")

app.destroy()
print("Tamamlandi")
