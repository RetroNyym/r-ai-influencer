# -*- coding: utf-8 -*-
"""Farklı harmanlama oranları ile dönüşüm aralığını göster."""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

import cv2
import numpy as np
from core.yuz_degistir import suret_degistir

KULLANICI = "test_cikti/gercek_portre.jpg"
HEDEF = "test_cikti/gercekci_test2.jpg"  # uretilmis farkli persona

oranlar = [0.3, 0.5, 0.7, 0.9]
sonuclar = []
for o in oranlar:
    s = suret_degistir(KULLANICI, HEDEF, oran=o, mod="kullanici")
    yol = Path(f"test_cikti/suret_o{int(o*100)}.jpg")
    cv2.imwrite(str(yol), s, [cv2.IMWRITE_JPEG_QUALITY, 95])
    sonuclar.append((o, s))
    print(f"oran={o} -> {yol.name} {yol.stat().st_size}byte")

# Kontak: kullanici | hedef | o0.3 | o0.5 | o0.7 | o0.9
k_img = cv2.imread(KULLANICI)
h_img = cv2.imread(HEDEF)

def k(img, h=440):
    return cv2.resize(img, (int(img.shape[1] * h / img.shape[0]), h), interpolation=cv2.INTER_AREA)

b = np.full((440, 6, 3), 255, np.uint8)
parcalar = [k(k_img), b, k(h_img), b]
for i, (o, s) in enumerate(sonuclar):
    parcalar.append(k(s))
    if i < len(sonuclar) - 1:
        parcalar.append(b)
satir = np.hstack(parcalar)
cv2.imwrite("test_cikti/suret_oran_kontakt.jpg", satir, [cv2.IMWRITE_JPEG_QUALITY, 90])
print("Kontak: test_cikti/suret_oran_kontakt.jpg", satir.shape)
