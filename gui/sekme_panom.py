# -*- coding: utf-8 -*-
"""Genel Bakış (Overview) — premium kontrol paneli.

Stat kartları + karakter profili + karakter kütüphanesi + son üretimler +
sistem/API durumu tek ekranda.
"""

import time
import tkinter as tk
from tkinter import ttk

from core import api_yonetici, depolama, kisilik, video
from gui.palet import (CIZGI, HATA, KART, METIN_KOYU, METIN_SOLUK, TEAL,
                       TEAL_KOYU, TEAL_VURGU, YESIL_ACIK, ZEMIN, ZEMIN_KOYU,
                       vesikalik_foto)

IKON = "Segoe MDL2 Assets"
GLIF = {"karakter": "\ue77b", "gonder": "\ue72d",
        "gorsel": "\ue91b", "ev": "\ue80f", "duyuru": "\ue7ed"}


def _ikon(anahtar, boyut=16, renk=TEAL_KOYU):
    return (IKON, boyut), GLIF.get(anahtar, "")


class SekmePanom(ttk.Frame):
    """Overview: üretim/yayın durumu ve sistem sağlığı tek bakışta."""

    def __init__(self, parent, git=None):
        super().__init__(parent, style="Govde.TFrame")
        self.git = git or (lambda anahtar: None)
        self._foto_on = None
        self._thumb_on = []
        self._kur()

    # ------------------------------------------------------------------
    def _kur(self):
        kok = tk.Frame(self, bg=ZEMIN)
        kok.pack(fill="both", expand=True, padx=22, pady=18)

        # --- Başlık satırı ---
        ust = tk.Frame(kok, bg=ZEMIN)
        ust.pack(fill="x")
        tk.Label(ust, text="Genel Bakış", bg=ZEMIN, fg=METIN_KOYU,
                 font=("Segoe UI", 22, "bold")).pack(side="left")
        tk.Label(ust, text="Üretim ve yayın durumunuz tek bakışta",
                 bg=ZEMIN, fg=METIN_SOLUK,
                 font=("Segoe UI", 10)).pack(side="left", padx=(14, 0),
                                             pady=(8, 0))
        ttk.Button(ust, text="+  Yeni Karakter", style="Yesil.TButton",
                   command=lambda: self.git("kisilik")).pack(side="right")

        # --- Stat kartları (3'lü) ---
        stat_f = tk.Frame(kok, bg=ZEMIN)
        stat_f.pack(fill="x", pady=(18, 14))
        stat_f.columnconfigure(0, weight=1)
        stat_f.columnconfigure(1, weight=1)
        stat_f.columnconfigure(2, weight=1)
        self.stat_karakter = self._stat_kart(stat_f, "karakter",
                                             "Karakterler", "0",
                                             "kişilik profili")
        self.stat_karakter["frame"].grid(row=0, column=0, sticky="ew",
                                          padx=(0, 10))
        self.stat_hazir = self._stat_kart(stat_f, "gonder", "Yayına Hazır",
                                          "0", "onaylı post")
        self.stat_hazir["frame"].grid(row=0, column=1, sticky="ew", padx=10)
        self.stat_varlik = self._stat_kart(stat_f, "gorsel",
                                           "Üretilen İçerik", "0",
                                           "toplam görsel/varlık")
        self.stat_varlik["frame"].grid(row=0, column=2, sticky="ew",
                                       padx=(10, 0))

        # --- Alt gövde: profil | kütüphane + son üretimler ---
        alt = tk.Frame(kok, bg=ZEMIN)
        alt.pack(fill="both", expand=True)
        alt.columnconfigure(1, weight=3)
        alt.columnconfigure(0, weight=2)
        alt.rowconfigure(0, weight=3)
        alt.rowconfigure(1, weight=2)

        self._profil_karti(alt).grid(row=0, column=0, rowspan=2,
                                     sticky="nsew", padx=(0, 12))
        self._kutuphane_karti(alt).grid(row=0, column=1, sticky="nsew",
                                        pady=(0, 12))
        self._son_uretim_karti(alt).grid(row=1, column=1, sticky="nsew")

        # --- Sistem durumu şeridi ---
        self.sistem = tk.Label(kok, text="", bg=ZEMIN, fg=METIN_SOLUK,
                               font=("Segoe UI", 9), anchor="w")
        self.sistem.pack(fill="x", pady=(12, 0))

        self.yenile()

    # ------------------------------------------------------------------
    def _stat_kart(self, parent, ikon, etiket, deger, trend):
        kart = tk.Frame(parent, bg=KART, highlightthickness=1,
                        highlightbackground=CIZGI)
        ic = tk.Frame(kart, bg=KART)
        ic.pack(fill="x", padx=16, pady=(14, 0))
        rozet = tk.Frame(ic, bg=ZEMIN_KOYU, width=42, height=42)
        rozet.pack(side="left")
        rozet.pack_propagate(False)
        tk.Label(rozet, text=GLIF.get(ikon, ""), bg=ZEMIN_KOYU,
                 fg=TEAL_KOYU, font=(IKON, 17)).pack(expand=True)
        tk.Label(ic, text=etiket, bg=KART, fg=METIN_SOLUK,
                 font=("Segoe UI", 11)).pack(side="left", padx=(12, 0))

        deger_lbl = tk.Label(kart, text=deger, bg=KART, fg=METIN_KOYU,
                             font=("Segoe UI", 30, "bold"), anchor="w")
        deger_lbl.pack(fill="x", padx=16)
        trend_lbl = tk.Label(kart, text="↑  " + trend, bg=KART, fg=TEAL_KOYU,
                             font=("Segoe UI", 9), anchor="w")
        trend_lbl.pack(fill="x", padx=16, pady=(0, 14))
        return {"frame": kart, "deger": deger_lbl, "trend": trend_lbl,
                "etiket": etiket}

    def _profil_karti(self, parent):
        kart = tk.Frame(parent, bg=KART, highlightthickness=1,
                        highlightbackground=CIZGI)
        bas = tk.Frame(kart, bg=KART)
        bas.pack(fill="x", padx=16, pady=(14, 8))
        tk.Label(bas, text="Karakter Profili", bg=KART, fg=METIN_KOYU,
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        ttk.Button(bas, text="Düzenle", style="Kart.TButton",
                   command=lambda: self.git("kisilik")).pack(side="right")

        govde = tk.Frame(kart, bg=KART)
        govde.pack(fill="both", expand=True, padx=16, pady=(0, 14))

        self.profil_foto = tk.Label(govde, text="📷", bg=ZEMIN_KOYU,
                                    fg=METIN_SOLUK, width=14, height=7,
                                    font=("Segoe UI", 22))
        self.profil_foto.pack(side="left", anchor="n")

        sag = tk.Frame(govde, bg=KART)
        sag.pack(side="left", fill="both", expand=True, padx=(14, 0))

        satir1 = tk.Frame(sag, bg=KART)
        satir1.pack(fill="x")
        self.profil_ad = tk.Label(satir1, text="—", bg=KART, fg=METIN_KOYU,
                                  font=("Segoe UI", 17, "bold"))
        self.profil_ad.pack(side="left")
        self.profil_rozet = tk.Label(satir1, text=" TASLAK ", bg=TEAL,
                                     fg="#FFFFFF", font=("Segoe UI", 8, "bold"),
                                     padx=6, pady=2)
        self.profil_rozet.pack(side="left", padx=(10, 0))

        self.profil_nis = tk.Label(sag, text="", bg=KART, fg=TEAL_KOYU,
                                   font=("Segoe UI", 10), anchor="w")
        self.profil_nis.pack(fill="x", pady=(2, 0))
        self.profil_aciklama = tk.Label(sag, text="", bg=KART,
                                        fg=METIN_SOLUK, font=("Segoe UI", 9),
                                        justify="left", anchor="w",
                                        wraplength=330)
        self.profil_aciklama.pack(fill="x", pady=(6, 0))

        ttk.Separator(sag).pack(fill="x", pady=8)
        self.profil_satirlar = tk.Frame(sag, bg=KART)
        self.profil_satirlar.pack(fill="x")

        tk.Label(sag, text="ETİKETLER", bg=KART, fg=METIN_SOLUK,
                 font=("Segoe UI", 8, "bold"), anchor="w").pack(
            fill="x", pady=(10, 4))
        self.profil_etiketler = tk.Frame(sag, bg=KART)
        self.profil_etiketler.pack(fill="x")
        return kart

    def _kutuphane_karti(self, parent):
        kart = tk.Frame(parent, bg=KART, highlightthickness=1,
                        highlightbackground=CIZGI)
        bas = tk.Frame(kart, bg=KART)
        bas.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(bas, text="Karakter Kütüphanesi", bg=KART, fg=METIN_KOYU,
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        ttk.Button(bas, text="Tümü ›", style="Kart.TButton",
                   command=lambda: self.git("kisilik")).pack(side="right")

        self.kutuphane = ttk.Treeview(
            kart, columns=("ad", "nis", "kaynak", "durum", "olusturma"),
            show="headings", height=5)
        for col, bas2, gen in [("ad", "Ad", 130), ("nis", "Niş", 120),
                               ("kaynak", "Kaynak", 110),
                               ("durum", "Durum", 110),
                               ("olusturma", "Oluşturma", 110)]:
            self.kutuphane.heading(col, text=bas2)
            self.kutuphane.column(col, width=gen)
        self.kutuphane.pack(fill="x", padx=16, pady=(0, 14))
        return kart

    def _son_uretim_karti(self, parent):
        kart = tk.Frame(parent, bg=KART, highlightthickness=1,
                        highlightbackground=CIZGI)
        bas = tk.Frame(kart, bg=KART)
        bas.pack(fill="x", padx=16, pady=(12, 6))
        tk.Label(bas, text="Son Üretimler", bg=KART, fg=METIN_KOYU,
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        ttk.Button(bas, text="Üretim ›", style="Kart.TButton",
                   command=lambda: self.git("uretim")).pack(side="right")
        self.son_satir = tk.Frame(kart, bg=KART)
        self.son_satir.pack(fill="x", padx=16, pady=(0, 14))
        return kart

    # ------------------------------------------------------------------
    def yenile(self):
        """Tüm panel verilerini tazeler (sayfa gösterilince çağrılır)."""
        try:
            personalar = kisilik.persona_listele()
        except Exception:
            personalar = []
        try:
            postlar = depolama.post_listele()
        except Exception:
            postlar = []

        hazir = sum(1 for p in postlar if p.get("durum") == "onayli")
        bekleyen = sum(1 for p in postlar if p.get("durum") == "onay_bekliyor")

        self.stat_karakter["deger"].config(text=f"{len(personalar):02d}")
        self.stat_karakter["trend"].config(
            text=f"↑  {sum(1 for p in personalar if p.get('kanon_gorsel'))} "
                 "canon yüz")
        self.stat_hazir["deger"].config(text=f"{hazir:02d}")
        self.stat_hazir["trend"].config(
            text=f"↑  {bekleyen} onay bekliyor")
        self.stat_varlik["deger"].config(text=f"{len(postlar):03d}")
        haftalik = sum(1 for p in postlar
                       if time.time() - (p.get("olusturma") or 0) < 7 * 86400)
        self.stat_varlik["trend"].config(text=f"↑  +{haftalik} bu hafta")

        self._profilu_doldur(personalar)
        self._kutuphane_doldur(personalar)
        self._son_uretimleri_doldur()
        self._sistem_durumu()

    def _profilu_doldur(self, personalar):
        for w in self.profil_satirlar.winfo_children():
            w.destroy()
        for w in self.profil_etiketler.winfo_children():
            w.destroy()

        persona = None
        for p in personalar:
            if p.get("kimlik_embedding") and p.get("kanon_gorsel"):
                persona = p
                break
        if not persona and personalar:
            persona = personalar[0]
        if not persona:
            self.profil_ad.config(text="Karakter yok")
            self.profil_nis.config(text="")
            self.profil_aciklama.config(
                text="Karakterler sekmesinden ilk karakterinizi oluşturun.")
            self.profil_rozet.config(text=" BOŞ ", bg=TEAL)
            self.profil_foto.config(image="", text="📷")
            self.profil_foto.image = None
            return

        self.profil_ad.config(text=persona.get("ad", "?"))
        kilitli = bool(persona.get("kimlik_embedding"))
        kanon = bool(persona.get("kanon_gorsel"))
        if kilitli and kanon:
            self.profil_rozet.config(text="  KİMLİK KİLİTLİ  ",
                                     bg=TEAL_VURGU, fg="#062018")
        elif kanon:
            self.profil_rozet.config(text="  CANON  ", bg=TEAL, fg="#FFFFFF")
        else:
            self.profil_rozet.config(text="  TASLAK  ", bg=METIN_SOLUK,
                                     fg=KART)
        self.profil_nis.config(
            text=(persona.get("nis", "") or "").upper())
        self.profil_aciklama.config(
            text=f"{persona.get('kisilik', '')}. "
                 f"Marka sesi: {persona.get('marka_sesi', '')}.")

        satirlar = [
            ("Seed", str(persona.get("seed", "—"))),
            ("Niş", persona.get("nis", "—")),
            ("Kaynak", persona.get("kaynak", "ai")),
            ("Yüz Tutarlılığı", "Kilitli ✓" if kilitli else "Kilitli değil"),
            ("Yaş", str(persona.get("yas", "—"))),
        ]
        for etiket, deger in satirlar:
            r = tk.Frame(self.profil_satirlar, bg=KART)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=etiket, bg=KART, fg=METIN_SOLUK,
                     font=("Segoe UI", 9), width=16, anchor="w").pack(
                side="left")
            deger_renk = TEAL_KOYU if etiket == "Yüz Tutarlılığı" else METIN_KOYU
            tk.Label(r, text=deger, bg=KART, fg=deger_renk,
                     font=("Segoe UI", 9, "bold"), anchor="w").pack(
                side="left")

        kelimeler = [k.strip() for k in
                     (persona.get("kisilik", "") or "").replace(",", " ").split()
                     if len(k.strip()) > 2][:5]
        for kelime in kelimeler:
            tk.Label(self.profil_etiketler, text=kelime, bg=ZEMIN_KOYU,
                     fg=TEAL_KOYU, font=("Segoe UI", 8), padx=8,
                     pady=3).pack(side="left", padx=(0, 6))

        foto_yol = persona.get("kanon_gorsel")
        try:
            if foto_yol:
                foto = vesikalik_foto(foto_yol, boyut=(110, 146))
                self.profil_foto.config(image=foto, text="",
                                        width=0, height=0)
                self.profil_foto.image = foto
            else:
                self.profil_foto.config(image="", text="👤",
                                        width=14, height=7)
                self.profil_foto.image = None
        except Exception:
            pass

    def _kutuphane_doldur(self, personalar):
        for i in self.kutuphane.get_children():
            self.kutuphane.delete(i)
        for p in personalar:
            if p.get("kimlik_embedding"):
                durum = "● Kilitli"
            elif p.get("kanon_gorsel"):
                durum = "● Hazır"
            else:
                durum = "○ Taslak"
            olusturma = p.get("olusturma")
            tarih = (time.strftime("%d.%m.%Y", time.localtime(olusturma))
                     if olusturma else "—")
            self.kutuphane.insert("", "end", iid=str(p["id"]), values=(
                p.get("ad", "?"), p.get("nis", "—"),
                p.get("kaynak", "ai"), durum, tarih))

    def _son_uretimleri_doldur(self):
        for w in self.son_satir.winfo_children():
            w.destroy()
        self._thumb_on = []
        try:
            adaylar = [y for y in depolama.URETILEN_KLASOR.rglob("*")
                       if y.suffix.lower() in (".jpg", ".jpeg", ".png")
                       and y.is_file()]
            adaylar.sort(key=lambda y: y.stat().st_mtime, reverse=True)
        except Exception:
            adaylar = []

        if not adaylar:
            tk.Label(self.son_satir, text="Henüz üretim yok — Üretim "
                     "sekmesinden ilk görselinizi oluşturun.", bg=KART,
                     fg=METIN_SOLUK, font=("Segoe UI", 9)).pack(anchor="w")
            return

        try:
            from PIL import Image, ImageTk
            for yol in adaylar[:4]:
                kutu = tk.Frame(self.son_satir, bg=KART)
                kutu.pack(side="left", padx=(0, 12))
                img = Image.open(yol)
                img.thumbnail((132, 176), Image.LANCZOS)
                foto = ImageTk.PhotoImage(img)
                lbl = tk.Label(kutu, image=foto, bg=ZEMIN_KOYU)
                lbl.image = foto
                self._thumb_on.append(foto)
                lbl.pack()
                gecen = time.time() - yol.stat().st_mtime
                if gecen < 3600:
                    sure = f"{int(gecen // 60)}dk önce"
                elif gecen < 86400:
                    sure = f"{int(gecen // 3600)}sa önce"
                else:
                    sure = f"{int(gecen // 86400)}g önce"
                alt = tk.Frame(kutu, bg=KART)
                alt.pack(fill="x", pady=(4, 0))
                tk.Label(alt, text="🖼 Görsel", bg=KART, fg=METIN_SOLUK,
                         font=("Segoe UI", 8)).pack(side="left")
                tk.Label(alt, text=sure, bg=KART, fg=METIN_SOLUK,
                         font=("Segoe UI", 8)).pack(side="right")
        except Exception as e:
            tk.Label(self.son_satir, text=f"Önizleme hatası: {e}", bg=KART,
                     fg=HATA, font=("Segoe UI", 9)).pack(anchor="w")

    def _sistem_durumu(self):
        try:
            aktif = api_yonetici.aktif_api()
            api_ad = aktif["ad"] if aktif else "Pollinations (ücretsiz)"
        except Exception:
            api_ad = "Pollinations (ücretsiz)"
        try:
            ff = "✓" if video.ffmpeg_var_mi() else "✗"
        except Exception:
            ff = "?"
        self.sistem.config(
            text=f"●  API: {api_ad}      "
                 f"●  FFmpeg: {ff}      "
                 f"●  Yerel üretim: açık      "
                 f"●  Veritabanı: bağlı")
