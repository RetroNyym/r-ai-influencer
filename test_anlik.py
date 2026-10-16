# -*- coding: utf-8 -*-
"""Acik GUI'nin anlik ekran görüntüsünü alır."""
import sys, time
sys.stdout.reconfigure(encoding="utf-8")
import tkinter as tk
from PIL import ImageGrab

# Mevcut pencereyi bul
root = tk.Tk()
root.withdraw()
root.update()

time.sleep(1)

# Tüm ekranı yakala
img = ImageGrab.grab()
yol = r"C:\Users\Ekomak\Documents\Default Project\ai-influencer\test_cikti\acik_pencere.png"
img.save(yol)
print(f"Kaydedildi: {yol}")
root.destroy()
