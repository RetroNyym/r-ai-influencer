# -*- coding: utf-8 -*-
"""API sekmesi screenshot."""
import sys, os, time
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import tkinter as tk
from PIL import ImageGrab
from core import depolama
depolama.kur()

from gui.ana_pencere import AnaPencere

TEST_KLASOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_cikti")

app = AnaPencere()
app.update_idletasks()
app.update()

# API sekmesi
app.sayfa_degistir("api")
app.update()
time.sleep(0.3)

x = app.winfo_rootx()
y = app.winfo_rooty()
w = app.winfo_width()
h = app.winfo_height()
img = ImageGrab.grab(bbox=(x, y, x + w, y + h))
yol = os.path.join(TEST_KLASOR, "gui_api_sekme.png")
img.save(yol)
print(f"Kaydedildi: {yol}")

app.destroy()
