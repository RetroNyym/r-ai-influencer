# -*- coding: utf-8 -*-
"""Tüm yeni özellikleri smoke-test eder (B/C/D/E/F)."""
import os, sys, time
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core import (atomik, depolama, fotoroman, kisilik, marka, seslendirme,
                  skorlama, toplu, trend, video, yayin_paketi)
depolama.kur()
TEST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_cikti")
os.makedirs(TEST, exist_ok=True)
basarili, hatali = [], []

def kontrol(ad, fn):
    try:
        r = fn()
        print(f"  PASS  {ad} {('— ' + str(r)[:70]) if r else ''}")
        basarili.append(ad)
    except Exception as e:
        print(f"  FAIL  {ad}: {e}")
        hatali.append((ad, str(e)))

# --- F) atomik ---
def t_atomik():
    yol = os.path.join(TEST, "atomik_test.json")
    atomik.atomik_json_yaz(yol, {"a": 1})
    assert atomik.json_oku(yol)["a"] == 1
    assert not os.path.exists(yol + ".part")
    return "ok"
kontrol("F atomik yazma", t_atomik)

# --- B3) skorlama ---
def t_skor():
    zayif = skorlama.caption_skoru("bugün hava güzel")
    guclu = skorlama.caption_skoru(
        "🔥 Günlük 5 dakikalık ev antrenmanı! \n\nHemen dene ve sonucu yorumlara yaz "
        "👇 \n\n#fitness #evdeantrenman #sağlık #motivasyon #spor #gym")
    assert guclu["puan"] > zayif["puan"], f"{guclu['puan']} <= {zayif['puan']}"
    alt = skorlama.alternatif_oneriler("kahve molası", adet=2)
    return f"zayıf={zayif['puan']} güçlü={guclu['puan']} alt={len(alt)}"
kontrol("B3 skorlama", t_skor)

# --- B1) seslendirme (gtts fallback) ---
def t_ses():
    cikti = os.path.join(TEST, "ses_smoke")
    z = seslendirme.seslendir(["Bu bir test paragrafı."], cikti,
                              dil="tr", motor_secimi="gtts", yeniden=True)
    mp3 = os.path.join(cikti, "parts", "000.mp3")
    assert os.path.isfile(mp3) and os.path.getsize(mp3) > 200
    assert z["paragrafSayisi"] == 1
    return f"{z['motor']} {z['toplamSn']}sn"
kontrol("B1 seslendirme (gtts)", t_ses)

# --- B1) video (1 görsel + ses) ---
def t_video():
    gorsel = None
    for p in depolama.post_listele():
        if p.get("gorsel_yol") and os.path.isfile(p["gorsel_yol"]):
            gorsel = p["gorsel_yol"]; break
    if not gorsel:
        return "görsel yok, atlandı"
    ses = os.path.join(TEST, "ses_smoke", "parts", "000.mp3")
    cikti = os.path.join(TEST, "video_smoke.mp4")
    r = video.video_kur([(gorsel, 3.0)], cikti,
                        ses_yol=ses if os.path.isfile(ses) else None,
                        oran="9:16")
    assert os.path.isfile(r["cikti"])
    assert not os.path.exists(r["cikti"] + ".part")
    return f"{r['sureSn']}sn {r['boyut_mb']}MB"
kontrol("B1 video kur (ffmpeg)", t_video)

# --- B2) yayın paketi ---
def t_paket():
    posts = depolama.post_listele()
    if not posts:
        return "post yok"
    r = yayin_paketi.yayin_paketi_uret(posts[0]["id"])
    md = os.path.join(r["klasor"], "YAYIN-PAKETI.md")
    assert os.path.isfile(md)
    assert r["yayin"]["skor"]["puan"] > 0
    return f"post={posts[0]['id']} skor={r['yayin']['skor']['puan']}"
kontrol("B2 yayın paketi", t_paket)

# --- D6) performans ---
def t_perf():
    posts = depolama.post_listele()
    if not posts:
        return "post yok"
    depolama.performans_ekle(posts[0]["id"], "instagram",
                             goruntulenme=12500, begeni=830, yorum=45, paylasim=12)
    ist = depolama.performans_istatistik()
    assert ist["toplam"]["g"] >= 12500
    return f"toplam_g={ist['toplam']['g']}"
kontrol("D6 performans", t_perf)

# --- C5) toplu kuyruk ---
def t_toplu():
    tid = toplu.kuyruga_post_ekle(1, "test sahne", 1)
    liste = toplu.kuyruga_listele()
    assert any(k["id"] == tid for k in liste)
    return f"id={tid} toplam={len(liste)}"
kontrol("C5 toplu kuyruk", t_toplu)

# --- C4) trend (offline) ---
def t_trend():
    f = trend.trend_fikirleri("lifestyle", sayi=8, cevrimdisi=True)
    assert len(f) >= 8
    return f"{len(f)} fikir"
kontrol("C4 trend (offline şablon)", t_trend)

# --- D7) marka (Pollinations — ağır) ---
def t_marka():
    r = marka.marka_kiti_uret(1)
    assert os.path.isfile(r["profil"])
    assert len(r["biyografi"]) > 10
    return f"profil={os.path.getsize(r['profil'])//1024}KB"
kontrol("D7 marka kiti (Pollinations)", t_marka)

# --- E) fotoroman (Pollinations — 4 kare) ---
def t_fotoroman():
    posts = fotoroman.fotoroman_uret(1, "kahve molasi", kare_sayisi=4)
    assert len(posts) >= 1
    kuyruk = len(depolama.post_listele("onay_bekliyor"))
    return f"{len(posts)} kare, kuyruk={kuyruk}"
kontrol("E fotoroman (Pollinations)", t_fotoroman)

print(f"\nSonuç: {len(basarili)} PASS, {len(hatali)} FAIL")
if hatali:
    for a, e in hatali:
        print(f"  {a}: {e}")
    sys.exit(1)
