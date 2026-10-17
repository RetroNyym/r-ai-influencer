# -*- coding: utf-8 -*-
"""Premium GUI + vesikalık önizleme screenshot test."""
import sys, os, time
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from PIL import ImageGrab
from core import depolama, kisilik, uretim
depolama.kur()

TEST_KLASOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_cikti")

# Test post'u üret (Pollinations)
print("Test postu uretiliyor...")
try:
    pid = 1  # mevcut Elif
    posts = uretim.toplu_uret(pid, 1)
    print(f"  Post: {posts[0]['gorsel_yol'] if posts else 'yok'}")
except Exception as e:
    print(f"  Uretim hatasi (devam): {e}")

# GUI ac
from gui.ana_pencere import AnaPencere
app = AnaPencere()
app.update_idletasks()
app.update()

def kaydet(isim):
    app.update()
    time.sleep(0.4)
    app.update()
    x, y = app.winfo_rootx(), app.winfo_rooty()
    w, h = app.winfo_width(), app.winfo_height()
    img = ImageGrab.grab(bbox=(x, y, x+w, y+h))
    yol = os.path.join(TEST_KLASOR, isim)
    img.save(yol)
    print(f"  {yol}")

# 1) Karakter sekmesi (vesikalık panel)
kaydet("premium_01_karakter.png")

# 2) Uretim & Onay (vesikalik onizleme)
app.notebook.select(1)
app.update()
time.sleep(0.3)
# Post listesinden birini sec
uretim_sekme = app.sekme_uretim
if uretim_sekme.tree.get_children():
    ilk = uretim_sekme.tree.get_children()[0]
    uretim_sekme.tree.selection_set(ilk)
    uretim_sekme.tree.event_generate("<<TreeviewSelect>>")
    app.update()
    time.sleep(0.5)
kaydet("premium_02_uretim_vesikalik.png")

# 3) API sekmesi
app.notebook.select(3)
app.update()
time.sleep(0.3)
kaydet("premium_03_api.png")

# 4) Takvim
app.notebook.select(2)
app.update()
time.sleep(0.3)
kaydet("premium_04_takvim.png")

app.destroy()
print("Tamamlandi")
