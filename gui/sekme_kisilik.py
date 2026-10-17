# -*- coding: utf-8 -*-
"""Karakter sekmesi: persona oluşturma + kendi yüzünden suret (offline)."""

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core import depolama, kisilik, sahne_kutuphanesi
from gui.palet import (CIZGI, KART, METIN_KOYU, METIN_SOLUK, TEAL, TEAL_KOYU,
                       TEAL_VURGU, YESIL, YESIL_ACIK, ZEMIN, vesikalik_foto)


class SekmeKisilik(ttk.Frame):
    def __init__(self, parent, on_karakter=None):
        super().__init__(parent, style="Govde.TFrame")
        self.secili_yuz = None  # kendi yüzünden üretilen varyasyon yolları
        self._varyasyon_pid = None
        self.on_karakter = on_karakter  # (gorsel_yol|None, baslik, alt) — alt barda vesikalık
        self._kur()
        self._listeyi_yenile()

    def _kur(self):
        paned = tk.PanedWindow(self, orient="horizontal", bg=ZEMIN,
                               sashwidth=6, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        # --- Sol: form ---
        sol = tk.Frame(paned, bg=KART, highlightthickness=1,
                       highlightbackground=CIZGI)
        paned.add(sol, width=380)

        tk.Label(sol, text="Yeni Karakter", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=18, pady=(18, 6))

        alanlar = [
            ("ad", "Ad", "Elif"),
            ("yas", "Yaş", "24"),
            ("nis", "Niş", "lifestyle"),
            ("ten", "Ten Rengi", "olive"),
            ("sac", "Saç", "long dark brown hair"),
            ("goz", "Göz", "brown eyes"),
            ("stil", "Stil", "casual chic"),
            ("kisilik", "Kişilik", "warm and adventurous"),
            ("marka_sesi", "Marka Sesi", "friendly, authentic, witty"),
        ]

        self.girdiler = {}
        for anahtar, etiket, varsayilan in alanlar:
            f = ttk.Frame(sol, style="Kart.TFrame")
            f.pack(fill="x", padx=16, pady=2)
            ttk.Label(f, text=etiket, style="Kart.TLabel", width=14,
                      anchor="w").pack(side="left")
            e = ttk.Entry(f)
            e.insert(0, varsayilan)
            e.pack(side="left", fill="x", expand=True)
            self.girdiler[anahtar] = e

        ttk.Button(sol, text="Karakteri Oluştur (AI Yüz)",
                   style="Yesil.TButton",
                   command=self._olustur).pack(fill="x", padx=16, pady=12)

        ttk.Separator(sol).pack(fill="x", padx=16, pady=4)
        ttk.Label(sol, text="Kendi Yüzünden Suret",
                  style="Vurgu.TLabel",
                  font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=16, pady=(8, 4))

        # Yöntem seçimi
        yontem_f = ttk.Frame(sol, style="Kart.TFrame")
        yontem_f.pack(fill="x", padx=16, pady=2)
        ttk.Label(yontem_f, text="Yöntem", style="Kart.TLabel",
                  width=14, anchor="w").pack(side="left")
        self.yontem = tk.StringVar(value="kimlik")
        yontem_sec = ttk.Combobox(yontem_f, textvariable=self.yontem,
                                  state="readonly", values=[
                                      "kimlik — Farklı bir kişi (AI, gerçekçi)",
                                      "varyasyon — Hafif varyasyon (eski, offline)"])
        yontem_sec.pack(side="left", fill="x", expand=True)

        ttk.Label(sol,
                  text="Fotoğrafınızı yükleyin. 'Kimlik' yöntemi yüzünüzü\n"
                       "farklı ama gerçekçi bir surete dönüştürür.",
                  style="Kart.TLabel", justify="left").pack(anchor="w", padx=16)

        self.izin_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(sol, text="Bu fotoğraf bana ait / izinli",
                        variable=self.izin_var).pack(anchor="w", padx=16, pady=4)

        btn_yuz = ttk.Frame(sol, style="Kart.TFrame")
        btn_yuz.pack(fill="x", padx=16, pady=4)
        ttk.Button(btn_yuz, text="Fotoğraf Seç", style="Kart.TButton",
                   command=self._foto_sec).pack(side="left", padx=(0, 6))
        ttk.Button(btn_yuz, text="8 Suret Üret", style="Yesil.TButton",
                   command=self._varyasyon).pack(side="left")

        self.yuz_durum = ttk.Label(sol, text="", style="Kart.TLabel",
                                   wraplength=340)
        self.yuz_durum.pack(anchor="w", padx=16, pady=4)

        ttk.Label(sol,
                  text="Not: Üretilen varyasyonlar alt bardaki vesikalık\n"
                       "panelinde görünür. '+' ile paylaşım kuyruğuna ekleyin.",
                  style="KartKucuk.TLabel", justify="left").pack(
            anchor="w", padx=16, pady=(6, 12))

        # --- Sağ: liste + bilgi ---
        sag = tk.Frame(paned, bg=KART, highlightthickness=1,
                       highlightbackground=CIZGI)
        paned.add(sag, width=650)

        ust = tk.Frame(sag, bg=KART)
        ust.pack(fill="x", padx=12, pady=(12, 4))
        tk.Label(ust, text="Karakterler", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        ttk.Button(ust, text="Yenile", style="Kart.TButton",
                   command=self._listeyi_yenile).pack(side="right")

        # Liste + karakter bilgisi yan yana (vesikalık artık alt barda)
        liste_f = tk.Frame(sag, bg=KART)
        liste_f.pack(fill="both", expand=True, padx=12, pady=4)

        self.tree = ttk.Treeview(liste_f, columns=("ad", "nis", "seed", "kaynak"),
                                 show="headings", height=10)
        for col, bas in [("ad", "Ad"), ("nis", "Niş"), ("seed", "Seed"),
                         ("kaynak", "Kaynak")]:
            self.tree.heading(col, text=bas)
            self.tree.column(col, width=110)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._secim)

        # Karakter bilgi paneli → profesyonel profil kartı
        bilgi_f = tk.Frame(liste_f, bg=KART, width=250,
                           highlightthickness=1, highlightbackground=CIZGI)
        bilgi_f.pack(side="right", fill="y", padx=(10, 0))
        bilgi_f.pack_propagate(False)

        tk.Label(bilgi_f, text="Karakter Profili", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 11, "bold")).pack(
            anchor="w", padx=12, pady=(12, 6))

        ust_profil = tk.Frame(bilgi_f, bg=KART)
        ust_profil.pack(fill="x", padx=12)
        self.profil_foto = tk.Label(ust_profil, text="👤", bg=ZEMIN,
                                    fg=METIN_SOLUK, width=8, height=5,
                                    font=("Segoe UI", 20),
                                    highlightthickness=1,
                                    highlightbackground=CIZGI)
        self.profil_foto.pack(side="left")
        sag_profil = tk.Frame(ust_profil, bg=KART)
        sag_profil.pack(side="left", fill="x", expand=True, padx=(10, 0))
        self.profil_ad = tk.Label(sag_profil, text="Seçilmedi", bg=KART,
                                  fg=METIN_KOYU, font=("Segoe UI", 13, "bold"),
                                  anchor="w")
        self.profil_ad.pack(anchor="w")
        self.profil_rozet = tk.Label(sag_profil, text=" TASLAK ", bg=TEAL,
                                     fg="#FFFFFF", font=("Segoe UI", 8, "bold"),
                                     padx=5, pady=2)
        self.profil_rozet.pack(anchor="w", pady=(4, 0))

        ttk.Separator(bilgi_f).pack(fill="x", padx=12, pady=8)
        self.profil_satirlar = tk.Frame(bilgi_f, bg=KART)
        self.profil_satirlar.pack(fill="x", padx=12)

        tk.Label(bilgi_f, text="KİŞİLİK", bg=KART, fg=METIN_SOLUK,
                 font=("Segoe UI", 8, "bold"), anchor="w").pack(
            fill="x", padx=12, pady=(10, 2))
        self.profil_kisilik = tk.Label(
            bilgi_f, text="—", bg=KART, fg=METIN_SOLUK,
            font=("Segoe UI", 9), justify="left", anchor="nw",
            wraplength=220)
        self.profil_kisilik.pack(fill="both", expand=True, padx=12,
                                 pady=(0, 12))

        # Varyasyon önizleme alanı
        self.onizleme = tk.Frame(sag, bg=KART)
        self.onizleme.pack(fill="x", padx=12, pady=(4, 12))
        ust_v = tk.Frame(self.onizleme, bg=KART)
        ust_v.pack(fill="x")
        tk.Label(ust_v, text="Varyasyonlar (canon seçmek için tıklayın)",
                 bg=KART, fg=METIN_KOYU, font=("Segoe UI", 9)).pack(side="left")
        ttk.Button(ust_v, text="Tümünü Kuyruğa Ekle", style="Teal.TButton",
                   command=self._tumunu_kuyruga_ekle).pack(side="right")
        self.varyasyon_frame = tk.Frame(self.onizleme, bg=KART)
        self.varyasyon_frame.pack(fill="x", pady=4)

    # --- AI persona ---
    def _olustur(self):
        ad = self.girdiler["ad"].get().strip()
        if not ad:
            messagebox.showwarning("Eksik", "Ad girin")
            return
        try:
            yas = int(self.girdiler["yas"].get())
        except ValueError:
            yas = 25
        pid = kisilik.yeni_kisilik(
            ad, yas,
            self.girdiler["nis"].get().strip(),
            self.girdiler["ten"].get().strip(),
            self.girdiler["sac"].get().strip(),
            self.girdiler["goz"].get().strip(),
            self.girdiler["stil"].get().strip(),
            self.girdiler["kisilik"].get().strip(),
            self.girdiler["marka_sesi"].get().strip())
        self._listeyi_yenile()
        messagebox.showinfo("Tamam", f"Karakter oluşturuldu (ID {pid}).\n"
                            "Canon yüz için 'AI Yüz Üret' veya kendi fotoğrafınızı kullanın.")

    # --- Kendi yüzünden ---
    def _foto_sec(self):
        yol = filedialog.askopenfilename(
            title="Fotoğraf seçin",
            filetypes=[("Görseller", "*.jpg *.jpeg *.png *.bmp")])
        if yol:
            self.secili_foto = yol
            self.yuz_durum.config(text=f"Seçildi: {yol.split('/')[-1]}")

    def _varyasyon(self):
        if not getattr(self, "secili_foto", None):
            messagebox.showwarning("Eksik", "Önce fotoğraf seçin")
            return
        if not self.izin_var.get():
            messagebox.showwarning("İzin", "Fotoğrafın size ait olduğunu onaylayın")
            return

        secili = self.tree.selection()
        if not secili:
            messagebox.showwarning("Seçim", "Önce bir karakter seçin")
            return
        pid = int(secili[0])
        self._varyasyon_pid = pid

        kimlik = self.yontem.get().startswith("kimlik")
        etiket = "farklı kişiye dönüştürülüyor" if kimlik else "varyasyon üretiliyor"
        self.yuz_durum.config(text=f"Yüz {etiket}...")
        threading.Thread(target=self._varyasyon_worker, args=(pid, kimlik),
                         daemon=True).start()

    def _varyasyon_worker(self, pid, kimlik=True):
        try:
            klasor = depolama.URETILEN_KLASOR / "kanon" / str(pid)
            persona = kisilik.persona_al(pid)
            if kimlik:
                # Sektör standardı: insightface inswapper + ArcFace kimlik harmanlama
                from core import yuz_degistir
                sonuclar = yuz_degistir.kanon_suretler(
                    self.secili_foto, persona, klasor, sayi=8)
                yontem = "inswapper+arcface kimlik"
            else:
                # Eski offline Delaunay warp (yedek)
                from core import yuz_donusum
                sonuclar = yuz_donusum.varyasyon_uret(
                    self.secili_foto, klasor, sayi=8)
                yontem = "delaunay warp"
            if not sonuclar:
                raise RuntimeError("Hiç suret üretilemedi.")
            yollar = [s["gorsel_yol"] for s in sonuclar]
            meta = {"yontem": yontem,
                    "varyasyon_meta": [s.get("meta", {}) for s in sonuclar]}
            kisilik.kendi_yuzunden(pid, self.secili_foto, str(meta), yollar)
            self.after(0, lambda: self._varyasyon_bitti(sonuclar))
        except Exception as e:
            self.after(0, lambda: self._varyasyon_hata(str(e)))

    def _varyasyon_bitti(self, sonuclar):
        self.secili_yuz = sonuclar
        self.yuz_durum.config(
            text=f"{len(sonuclar)} varyasyon üretildi. "
                 "Canon seçmek için tıklayın; '+' ile kuyruğa ekleyin.")
        # Görsel küçük resimler
        for w in self.varyasyon_frame.winfo_children():
            w.destroy()
        try:
            from PIL import Image, ImageTk
            for i, s in enumerate(sonuclar):
                thumb_f = tk.Frame(self.varyasyon_frame, bg=KART, cursor="hand2")
                thumb_f.pack(side="left", padx=3)
                try:
                    img = Image.open(s["gorsel_yol"])
                    img.thumbnail((70, 93), Image.LANCZOS)
                    foto = ImageTk.PhotoImage(img)
                    lbl = tk.Label(thumb_f, image=foto, bg=KART, cursor="hand2")
                    lbl.image = foto
                    lbl.pack()
                except Exception:
                    lbl = tk.Label(thumb_f, text=f"V{i+1}", bg=KART,
                                   font=("Segoe UI", 9), width=8, height=3)
                    lbl.pack()
                tk.Label(thumb_f, text=f"V{i+1}", bg=KART, fg=METIN_KOYU,
                         font=("Segoe UI", 8)).pack()
                yol = s["gorsel_yol"]
                thumb_f.bind("<Button-1>", lambda e, y=yol: self._canon_sec_yuz(y))
                lbl.bind("<Button-1>", lambda e, y=yol: self._canon_sec_yuz(y))
                # + kuyruk butonu
                ttk.Button(thumb_f, text="+", style="Teal.TButton",
                           command=lambda y=yol, n=i + 1: self._kuyruga_ekle(y, n)
                           ).pack(fill="x", pady=(2, 0))
        except Exception:
            for i, s in enumerate(sonuclar):
                ttk.Button(self.varyasyon_frame, text=f"Varyasyon {i+1}",
                           style="Kart.TButton",
                           command=lambda yol=s["gorsel_yol"], n=i + 1:
                               self._kuyruga_ekle(yol, n)
                           ).pack(side="left", padx=2)

    def _varyasyon_hata(self, hata):
        self.yuz_durum.config(text=f"Hata: {hata}")

    def _canon_sec_yuz(self, yol):
        secili = self.tree.selection()
        if not secili:
            return
        pid = int(secili[0])
        # Kimlik kilitle: aynı kişi tüm üretimlerde tutarlı çıksın
        try:
            kisilik.kimlik_kilitle(pid, yol)
            mesaj = "Canon + kimlik kilitlendi (stabil karakter)"
        except Exception as e:
            kisilik.kanon_sec(pid, yol)
            mesaj = f"Canon güncellendi (kimlik kilitlenemedi: {e})"
        messagebox.showinfo("Tamam", mesaj)
        self._listeyi_yenile()
        persona = kisilik.persona_al(pid)
        if persona:
            self._bar_bildir(persona)

    # --- Paylaşım kuyruğu ---
    def _kuyruga_ekle(self, yol, no):
        pid = self._varyasyon_pid
        if not pid and self.tree.selection():
            pid = int(self.tree.selection()[0])
        if not pid:
            messagebox.showwarning("Seçim", "Önce bir karakter seçin")
            return
        persona = kisilik.persona_al(pid)
        ad = persona["ad"] if persona else f"ID {pid}"
        depolama.post_ekle({
            "persona_id": pid,
            "sahne": f"Yüz varyasyonu V{no}",
            "prompt": "",
            "gorsel_yol": yol,
            "caption": f"{ad} — suret varyasyonu V{no}",
            "hashtags": "#ai #virtualinfluencer",
            "durum": "onay_bekliyor",
        })
        self.yuz_durum.config(
            text=f"V{no} kuyruğa eklendi → Üretim & Onay sekmesinden onaylayın.")

    def _tumunu_kuyruga_ekle(self):
        if not self.secili_yuz:
            messagebox.showwarning("Yok", "Önce varyasyon üretin")
            return
        for i, s in enumerate(self.secili_yuz):
            self._kuyruga_ekle(s["gorsel_yol"], i + 1)
        self.yuz_durum.config(
            text=f"{len(self.secili_yuz)} varyasyon kuyruğa eklendi → "
                 "Üretim & Onay sekmesinden onaylayın.")

    # --- Liste ---
    def _listeyi_yenile(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for p in kisilik.persona_listele():
            self.tree.insert("", "end", iid=str(p["id"]),
                             values=(p["ad"], p["nis"], p["seed"], p["kaynak"]))
        # İlk karakteri seç → alt bardaki vesikalık dolu gelsin
        cocuklar = self.tree.get_children()
        if cocuklar and not self.tree.selection():
            self.tree.selection_set(cocuklar[0])
            self.tree.event_generate("<<TreeviewSelect>>")

    def _secim(self, event):
        secili = self.tree.selection()
        if not secili:
            return
        pid = int(secili[0])
        persona = kisilik.persona_al(pid)
        if not persona:
            return
        self._varyasyon_pid = pid
        # Profil kartı
        kanon = persona.get("kanon_gorsel")
        kilitli = bool(persona.get("kimlik_embedding"))
        self.profil_ad.config(text=persona.get("ad", "?"))
        if kilitli and kanon:
            self.profil_rozet.config(text="  KİMLİK KİLİTLİ  ",
                                     bg=YESIL, fg="#062018")
        elif kanon:
            self.profil_rozet.config(text="  CANON  ", bg=TEAL_KOYU,
                                     fg="#062018")
        else:
            self.profil_rozet.config(text="  TASLAK  ", bg=METIN_SOLUK,
                                     fg=KART)
        for w in self.profil_satirlar.winfo_children():
            w.destroy()
        satirlar = [
            ("Seed", str(persona.get("seed", "—"))),
            ("Niş", str(persona.get("nis", "—"))),
            ("Yaş", str(persona.get("yas", "—"))),
            ("Kaynak", str(persona.get("kaynak", "ai"))),
            ("Yüz Tutarlılığı",
             "Kilitli ✓" if kilitli else "Kilitli değil"),
        ]
        for etiket, deger in satirlar:
            r = tk.Frame(self.profil_satirlar, bg=KART)
            r.pack(fill="x", pady=2)
            tk.Label(r, text=etiket, bg=KART, fg=METIN_SOLUK,
                     font=("Segoe UI", 9), width=13, anchor="w").pack(
                side="left")
            renk = TEAL_KOYU if etiket == "Yüz Tutarlılığı" else METIN_KOYU
            tk.Label(r, text=deger, bg=KART, fg=renk,
                     font=("Segoe UI", 9, "bold"), anchor="w").pack(
                side="left")
        self.profil_kisilik.config(
            text=f"{persona.get('kisilik', '—')}\n\n"
                 f"Marka sesi: {persona.get('marka_sesi', '—')}")
        try:
            if kanon:
                foto = vesikalik_foto(kanon, boyut=(74, 98))
                self.profil_foto.config(image=foto, text="",
                                        width=0, height=0)
                self.profil_foto.image = foto
            else:
                self.profil_foto.config(image="", text="👤",
                                        width=8, height=5)
                self.profil_foto.image = None
        except Exception:
            pass
        self._bar_bildir(persona)

    def _bar_bildir(self, persona):
        if not self.on_karakter:
            return
        kanon = persona.get("kanon_gorsel")
        baslik = f"{persona['ad']}  ·  {persona.get('nis', '')}"
        alt = (f"Seed {persona.get('seed', '?')} · "
               f"{'Canon hazır' if kanon else 'Canon yüz yok'}")
        self.after(0, lambda: self.on_karakter(kanon, baslik, alt))
