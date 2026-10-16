# -*- coding: utf-8 -*-
"""Kapsamlı test: API tanıma, gerçekçi yüz dönüşümü, üretim yönlendirme."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

TEST_KLASOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_cikti")
os.makedirs(TEST_KLASOR, exist_ok=True)

def test_api_tanima():
    print("=== TEST: API Anahtar Tanima ===")
    from core import api_yonetici
    testler = [
        ("sk-proj-abc123def456ghi789jkl", "openai", "OpenAI"),
        ("sk-ant-api03-xyz123abc456def", "anthropic", "Anthropic"),
        ("r8_abcdef1234567890abcdef12", "replicate", "Replicate"),
        ("hf_abcdef1234567890abcdef", "huggingface", "HuggingFace"),
        ("gsk_abc123def456ghi789jklm", "groq", "Groq"),
        ("pk_pollinations123abc", "pollinations", "Pollinations"),
        ("sk-abcdefghijklmnopqrstuvwxyz0123456789", "openai", "OpenAI uzun"),
    ]
    basarili = 0
    for key, beklenen_id, aciklama in testler:
        api_id, api_adi = api_yonetici.key_tanima(key)
        durum = "PASS" if api_id == beklenen_id else "FAIL"
        print(f"  {durum}: {aciklama} -> {api_id} ({api_adi})")
        if api_id == beklenen_id:
            basarili += 1
    print(f"  Sonuc: {basarili}/{len(testler)}")
    return basarili == len(testler)

def test_api_kayit():
    print("\n=== TEST: API Kayit / Liste / Silme ===")
    from core import api_yonetici, depolama
    # Test key kaydet
    api_yonetici.api_kaydet("groq", "gsk_test123abc456def789ghi")
    kayitli = api_yonetici.kayitli_api_listesi()
    groq_var = any(k["id"] == "groq" for k in kayitli)
    print(f"  Kayit PASS: {groq_var}")
    # Aktif API
    aktif = api_yonetici.aktif_api()
    print(f"  Aktif API: {aktif['id'] if aktif else None}")
    # Sil
    api_yonetici.api_sil("groq")
    kayitli2 = api_yonetici.kayitli_api_listesi()
    groq_yok = not any(k["id"] == "groq" for k in kayitli2)
    print(f"  Silme PASS: {groq_yok}")
    return groq_var and groq_yok

def test_gercekchi_yuz():
    print("\n=== TEST: Gelistirilmis Yuz Donusum (Delaunay) ===")
    # Daha gerçekçi sentetik portre
    img = np.full((800, 800, 3), 220, dtype=np.uint8)
    # Yüz ovali
    cv2.ellipse(img, (400, 380), (160, 210), 0, 0, 360, (170, 195, 235), -1)
    # Alin
    cv2.ellipse(img, (400, 220), (100, 40), 0, 180, 360, (175, 200, 240), -1)
    # Sol-elmacik
    cv2.circle(img, (310, 360), 50, (175, 200, 240), -1)
    # Sag-elmacik
    cv2.circle(img, (490, 360), 50, (175, 200, 240), -1)
    # Cene
    cv2.ellipse(img, (400, 530), (80, 50), 0, 0, 180, (175, 200, 240), -1)
    # Sol goz beyazi
    cv2.ellipse(img, (340, 330), (28, 16), 0, 0, 360, (250, 250, 250), -1)
    # Sol goz bebeği
    cv2.circle(img, (340, 330), 11, (60, 80, 120), -1)
    cv2.circle(img, (343, 327), 4, (240, 240, 240), -1)
    # Sag goz beyazi
    cv2.ellipse(img, (460, 330), (28, 16), 0, 0, 360, (250, 250, 250), -1)
    # Sag goz bebeği
    cv2.circle(img, (460, 330), 11, (60, 80, 120), -1)
    cv2.circle(img, (463, 327), 4, (240, 240, 240), -1)
    # Kaslar
    cv2.ellipse(img, (340, 305), (32, 6), 0, 0, 360, (80, 60, 50), -1)
    cv2.ellipse(img, (460, 305), (32, 6), 0, 0, 360, (80, 60, 50), -1)
    # Burun
    cv2.ellipse(img, (400, 395), (14, 30), 0, 0, 180, (155, 180, 220), 2)
    cv2.circle(img, (388, 420), 5, (155, 180, 220), -1)
    cv2.circle(img, (412, 420), 5, (155, 180, 220), -1)
    # Agiz
    cv2.ellipse(img, (400, 470), (40, 14), 0, 0, 180, (120, 100, 140), 3)
    cv2.ellipse(img, (400, 465), (40, 10), 0, 0, 360, (200, 160, 170), -1)
    # Sac
    cv2.ellipse(img, (400, 200), (170, 120), 0, 180, 360, (60, 50, 45), -1)
    cv2.ellipse(img, (250, 350), (40, 120), 0, 0, 360, (60, 50, 45), -1)
    cv2.ellipse(img, (550, 350), (40, 120), 0, 0, 360, (60, 50, 45), -1)

    kaynak_yol = os.path.join(TEST_KLASOR, "portre.jpg")
    cv2.imwrite(kaynak_yol, img)

    from core import yuz_donusum
    ok, mesaj = yuz_donusum.test_yuz(kaynak_yol)
    print(f"  Yuz tespiti: {ok} - {mesaj}")
    if not ok:
        return False

    sonuclar = yuz_donusum.varyasyon_uret(kaynak_yol, TEST_KLASOR + "/gelismis", sayi=8)
    print(f"  Uretilen: {len(sonuclar)}")
    for s in sonuclar[:3]:
        print(f"    {os.path.basename(s['gorsel_yol'])} warp={s['meta']['warp_gucu']}")

    # Kontakt sheet
    gorseller = []
    for s in sonuclar:
        g = cv2.imread(s["gorsel_yol"])
        if g is not None:
            gorseller.append(cv2.resize(g, (200, 250)))
    if len(gorseller) >= 8:
        s1 = np.hstack(gorseller[:4])
        s2 = np.hstack(gorseller[4:8])
        kontakt = np.vstack([s1, s2])
        kontakt = cv2.copyMakeBorder(kontakt, 30, 5, 5, 5, cv2.BORDER_CONSTANT,
                                     value=(13, 79, 92))
        cv2.putText(kontakt, "R+ Gelismis Yuz Donusum: Delaunay + Bilateral (8 varyasyon)",
                    (10, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        yol = os.path.join(TEST_KLASOR, "gelismis_kontakt.jpg")
        cv2.imwrite(yol, kontakt)
        print(f"  Kontakt sheet: {yol}")
    return len(sonuclar) == 8

def test_uretim_yonlendirme():
    print("\n=== TEST: Uretim Yonlendirme (API yok -> Pollinations) ===")
    from core import uretim
    try:
        data = uretim.gorsel_uret("portrait test, woman, cafe", seed=7, genislik=384, yukseklik=512)
        yol = os.path.join(TEST_KLASOR, "yonlendirme_test.jpg")
        with open(yol, "wb") as f:
            f.write(data)
        print(f"  PASS: {len(data)} bytes")
        return True
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

if __name__ == "__main__":
    sonuclar = []
    sonuclar.append(("API Tanima", test_api_tanima()))
    sonuclar.append(("API Kayit", test_api_kayit()))
    sonuclar.append(("Gelismis Yuz", test_gercekchi_yuz()))
    sonuclar.append(("Uretim Yonlendirme", test_uretim_yonlendirme()))

    print("\n" + "="*50)
    basarili = sum(1 for _, ok in sonuclar if ok)
    for ad, ok in sonuclar:
        print(f"  {'PASS' if ok else 'FAIL'}: {ad}")
    print(f"\n{basarili}/{len(sonuclar)} basarili")
