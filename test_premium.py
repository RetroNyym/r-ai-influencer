# -*- coding: utf-8 -*-
"""Premium GUI + alt barda vesikalık + kuyruğa ekleme screenshot test."""
import sys, os, time
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PIL import ImageGrab
from core import depolama, kisilik, uretim
depolama.kur()

TEST_KLASOR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_cikti")

# Mevcut bir gorsel bul (post veya onceki test ciktisi)
gorsel = None
posts = depolama.post_listele()
for p in posts:
    if p.get("gorsel_yol") and os.path.isfile(p["gorsel_yol"]):
        gorsel = p["gorsel_yol"]
        break
if not gorsel:
    print("Test postu uretiliyor...")
    try:
        yeni = uretim.toplu_uret(1, 1)
        gorsel = yeni[0]["gorsel_yol"] if yeni else None
    except Exception as e:
        print(f"  Uretim hatasi (devam): {e}")

# GUI ac
from gui.ana_pencere import AnaPencere
app = AnaPencere()
app.update_idletasks()
app.update()
time.sleep(0.5)
app.update()

def kaydet(isim):
    app.lift()
    app.attributes("-topmost", True)
    app.focus_force()
    app.update()
    time.sleep(0.5)
    app.attributes("-topmost", False)
    app.update()
    x, y = app.winfo_rootx(), app.winfo_rooty()
    w, h = app.winfo_width(), app.winfo_height()
    img = ImageGrab.grab(bbox=(x, y, x+w, y+h))
    yol = os.path.join(TEST_KLASOR, isim)
    img.save(yol)
    print(f"  {yol}")

# 1) Karakter sekmesi — ilk karakter secili gelmeli, alt barda vesikalik
karakter_sekme = app.sekme_kisilik
cocuklar = karakter_sekme.tree.get_children()
if cocuklar:
    karakter_sekme.tree.selection_set(cocuklar[0])
    karakter_sekme.tree.event_generate("<<TreeviewSelect>>")
app.update()
time.sleep(0.5)
app.update()
kaydet("premium_01_karakter_altbar.png")

# 2) Kuyruğa ekleme simülasyonu (varyasyon yoksa mevcut gorselle)
oncesi = len(depolama.post_listele("onay_bekliyor"))
if gorsel:
    karakter_sekme._varyasyon_pid = int(cocuklar[0]) if cocuklar else 1
    karakter_sekme._kuyruga_ekle(gorsel, 99)
    karakter_sekme.secili_yuz = [{"gorsel_yol": gorsel}]
sonrasi = len(depolama.post_listele("onay_bekliyor"))
print(f"  Kuyruk: {oncesi} -> {sonrasi} (beklenen +1)")
kaydet("premium_02_karakter_kuyruk.png")

# 3) Uretim & Onay — kuyruktaki yeni satir + alt barda vesikalik
app.sayfa_degistir("uretim")
app.update()
time.sleep(0.4)
uretim_sekme = app.sekme_uretim
uretim_sekme.filtre.set("onay_bekliyor")
uretim_sekme._yukle()
app.update()
if uretim_sekme.tree.get_children():
    ilk = uretim_sekme.tree.get_children()[0]
    uretim_sekme.tree.selection_set(ilk)
    uretim_sekme.tree.event_generate("<<TreeviewSelect>>")
    app.update()
    time.sleep(0.4)
kaydet("premium_03_uretim_altbar.png")

# 4) Video sekmesi
app.sayfa_degistir("video")
app.update()
time.sleep(0.3)
kaydet("premium_04_video.png")

# 5) Yayın & Analiz
app.sayfa_degistir("yayin")
app.update()
time.sleep(0.3)
yayin_sekme = app.sekme_yayin
if yayin_sekme.tree.get_children():
    yayin_sekme.tree.selection_set(yayin_sekme.tree.get_children()[0])
    yayin_sekme.tree.event_generate("<<TreeviewSelect>>")
    app.update()
kaydet("premium_05_yayin.png")

# 6) Takvim
app.sayfa_degistir("takvim")
app.update()
time.sleep(0.3)
kaydet("premium_06_takvim.png")

# 7) API
app.sayfa_degistir("api")
app.update()
time.sleep(0.3)
kaydet("premium_07_api.png")

# 8) Araçlar
app.sayfa_degistir("arac")
app.update()
time.sleep(0.3)
kaydet("premium_08_arac.png")

app.destroy()
print("Tamamlandi")
