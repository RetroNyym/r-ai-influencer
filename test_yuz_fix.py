# -*- coding: utf-8 -*-
"""Delaunay warp düzeltmesinin doğrulaması: gerçek portre → 8 varyasyon + kontakt sheet."""
import sys
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

import cv2
import numpy as np

from core.yuz_donusum import varyasyon_uret, yuz_bul

KAYNAK = Path("test_cikti/gercek_portre.jpg")
CIKTI = Path("test_cikti/gercek_yuz_fix")

# Kaynak portre var mı?
if not KAYNAK.is_file():
    print(f"KAYNAK YOK: {KAYNAK}")
    sys.exit(1)

# Yüz bulunuyor mu?
try:
    img, box, landmarklar = yuz_bul(KAYNAK)
    print(f"Yuz bulundu: {len(landmarklar)} landmark, box={box}")
except Exception as e:
    print(f"Yuz hatasi: {e}")
    sys.exit(1)

# Varyasyonları üret
sonuclar = varyasyon_uret(KAYNAK, CIKTI, sayi=8)
print(f"Uretilen varyasyon: {len(sonuclar)}")
for s in sonuclar:
    p = Path(s["gorsel_yol"])
    print(f"  {p.name}  {p.stat().st_size} byte  guc={s['meta']['warp_gucu']}")

# Kontakt sheet: orijinal + 8 varyasyon (4x3 grid)
kaynak_img = cv2.imread(str(KAYNAK))
kaynak_kucuk = cv2.resize(kaynak_img, (320, 400), interpolation=cv2.INTER_AREA)
hudut = np.full((400, 8, 3), 237, dtype=np.uint8)  # zemin rengi

kareler = [kaynak_kucuk]
for s in sonuclar:
    v = cv2.imread(s["gorsel_yol"])
    if v is not None:
        kareler.append(cv2.resize(v, (320, 400), interpolation=cv2.INTER_AREA))

satirlar = []
for i in range(0, len(kareler), 4):
    satir = kareler[i:i + 4]
    while len(satir) < 4:
        satir.append(np.full((400, 320, 3), 237, dtype=np.uint8))
    parcalar = []
    for j, k in enumerate(satir):
        if j:
            parcalar.append(hudut)
        parcalar.append(k)
    satirlar.append(np.hstack(parcalar))

bos = np.full((satirlar[0].shape[0], satirlar[0].shape[1], 3), 237, dtype=np.uint8)
while len(satirlar) < 3:
    satirlar.append(bos.copy())

sheet = np.vstack([
    satirlar[0],
    np.full((8, satirlar[0].shape[1], 3), 237, dtype=np.uint8),
    satirlar[1],
    np.full((8, satirlar[0].shape[1], 3), 237, dtype=np.uint8),
    satirlar[2],
])
sheet_yol = Path("test_cikti/gercek_yuz_fix_kontakt.jpg")
cv2.imwrite(str(sheet_yol), sheet, [cv2.IMWRITE_JPEG_QUALITY, 92])
print(f"Kontakt sheet: {sheet_yol}  {sheet_yol.stat().st_size} byte")
