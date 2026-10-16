# -*- coding: utf-8 -*-
"""AI Influencer - gorsel test scripti."""
import sys, os
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cv2
import numpy as np

TEST_KLASOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_cikti")
os.makedirs(TEST_KLASOR, exist_ok=True)

def test1_yuz_donusum():
    print("=== TEST 1: Yuz Donusum (8 varyasyon) ===")
    # Synthetic test portrait
    img = np.full((600, 600, 3), 210, dtype=np.uint8)
    cv2.ellipse(img, (300, 280), (140, 180), 0, 0, 360, (180, 200, 230), -1)
    cv2.circle(img, (250, 240), 18, (50, 50, 50), -1)
    cv2.circle(img, (350, 240), 18, (50, 50, 50), -1)
    cv2.ellipse(img, (300, 340), (40, 20), 0, 0, 180, (80, 80, 120), 3)
    cv2.ellipse(img, (300, 300), (12, 20), 0, 0, 180, (160, 180, 210), 2)
    kaynak_yol = os.path.join(TEST_KLASOR, "kaynak.jpg")
    cv2.imwrite(kaynak_yol, img)
    print(f"  Kaynak portrait: {kaynak_yol}")

    from core import yuz_donusum
    ok, mesaj = yuz_donusum.test_yuz(kaynak_yol)
    print(f"  Yuz tespiti: {ok} - {mesaj}")
    if not ok:
        return False

    sonuclar = yuz_donusum.varyasyon_uret(kaynak_yol, TEST_KLASOR, sayi=8)
    print(f"  Uretilen varyasyon: {len(sonuclar)}")
    for s in sonuclar:
        ad = os.path.basename(s["gorsel_yol"])
        print(f"    {ad}  seed={s['meta']['seed']}  warp={s['meta']['warp_gucu']}  ten={s['meta']['ten_kaydirma']}  mirror={s['meta']['mirror']}")

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
        # Baslik ekle
        kontakt = cv2.copyMakeBorder(kontakt, 30, 5, 5, 5, cv2.BORDER_CONSTANT, value=(13, 79, 92))
        cv2.putText(kontakt, "R+ Yuz Donusum: 8 Varyasyon (Offline)", (10, 22),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
        yol = os.path.join(TEST_KLASOR, "kontakt_sheet.jpg")
        cv2.imwrite(yol, kontakt)
        print(f"  Kontakt sheet: {yol}")
    return len(sonuclar) == 8

def test2_pollinations_gorsel():
    print("\n=== TEST 2: Pollinations Gorsel Uretimi ===")
    from core import uretim
    prompt = "photorealistic portrait of a 24 year old woman with olive skin, long dark brown hair, brown eyes, wearing casual chic, warm vibe, cafe background, social media photo"
    try:
        data = uretim.gorsel_uret(prompt, seed=42, genislik=512, yukseklik=640)
        yol = os.path.join(TEST_KLASOR, "pollinations_gorsel.jpg")
        with open(yol, "wb") as f:
            f.write(data)
        print(f"  OK - {len(data)} bytes -> {yol}")
        return True
    except Exception as e:
        print(f"  HATA: {e}")
        return False

def test3_pollinations_caption():
    print("\n=== TEST 3: Pollinations Caption Uretimi ===")
    from core import uretim
    persona = {"ad": "Elif", "yas": 24, "nis": "lifestyle", "marka_sesi": "friendly, authentic, witty"}
    try:
        cap = uretim.caption_uret(persona, "sitting in a cozy cafe reading a book by the window")
        print(f"  Caption: {cap['caption']}")
        print(f"  Hashtags: {cap['hashtags']}")
        return True
    except Exception as e:
        print(f"  HATA: {e}")
        return False

def test4_veritabani():
    print("\n=== TEST 4: SQLite Depolama ===")
    from core import depolama, kisilik
    pid = kisilik.yeni_kisilik("Elif", 24, "lifestyle", "olive", "long dark hair",
                                "brown eyes", "casual chic", "warm and adventurous",
                                "friendly, authentic, witty")
    p = kisilik.persona_al(pid)
    print(f"  Persona olusturuldu: ID={pid} ad={p['ad']} seed={p['seed']}")
    print(f"  Anchor: {p['anchor_prompt'][:80]}...")
    post_id = depolama.post_ekle({
        "persona_id": pid, "sahne": "cafe scene", "prompt": "test",
        "gorsel_yol": "test.jpg", "caption": "test caption",
        "hashtags": "#ai #test", "durum": "onay_bekliyor"})
    print(f"  Post eklendi: ID={post_id}")
    depolama.post_durum(post_id, "onayli")
    p2 = depolama.post_al(post_id)
    print(f"  Durum guncellendi: {p2['durum']}")
    sid = depolama.schedule_ekle(0, "19:00")
    print(f"  Schedule eklendi: ID={sid} gun=Pazartesi saat=19:00")
    return True

def test5_prompt():
    print("\n=== TEST 5: Prompt & Sahne Kutuphanesi ===")
    from core import kisilik, sahne_kutuphanesi as sk
    print(f"  Nisler: {sk.nisler()}")
    for nis in sk.nisler():
        s = sk.sahne_sec(nis, seed=42)
        print(f"    {nis}: {s[:60]}")
    p = kisilik.prompt_yap("walking in park", {"anchor_prompt": "photorealistic portrait of a woman"})
    print(f"  Ornek prompt: {p[:100]}")
    return True

if __name__ == "__main__":
    sonuclar = []
    sonuclar.append(("Yuz Donusum", test1_yuz_donusum()))
    sonuclar.append(("Pollinations Gorsel", test2_pollinations_gorsel()))
    sonuclar.append(("Pollinations Caption", test3_pollinations_caption()))
    sonuclar.append(("Veritabani", test4_veritabani()))
    sonuclar.append(("Prompt/Sahne", test5_prompt()))

    print("\n" + "="*50)
    print("TEST SONUCLARI:")
    basarili = 0
    for ad, ok in sonuclar:
        print(f"  {'PASS' if ok else 'FAIL'}: {ad}")
        if ok:
            basarili += 1
    print(f"\n{basarili}/{len(sonuclar)} test basarili")
