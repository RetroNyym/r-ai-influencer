# -*- coding: utf-8 -*-
"""Karakter sekmesi: persona oluşturma + kendi yüzünden suret (offline)."""

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core import depolama, kisilik, sahne_kutuphanesi

ZEMIN = "#EDF4F3"
KART = "#FFFFFF"
CIZGI = "#C8D8D5"
METIN_KOYU = "#0F2A2C"
TEAL_KOYU = "#0A3D47"
TEAL_VURGU = "#20B89A"
YESIL = "#20B89A"
YESIL_ACIK = "#DFF5EE"
VESIKALIK_BOYUT = (160, 213)


class SekmeKisilik(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Govde.TFrame")
        self.secili_yuz = None  # kendi yüzünden üretilen varyasyon yolları
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
        ttk.Label(sol, text="Kendi Yüzünden Suret (Offline)",
                  style="Vurgu.TLabel",
                  font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=16, pady=(8, 4))
        ttk.Label(sol,
                  text="Fotoğrafınızı yükleyin; program API'siz, yerel\n"
                       "işlemle 8 farklı suret varyasyonu üretir.",
                  style="Kart.TLabel", justify="left").pack(anchor="w", padx=16)

        self.izin_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(sol, text="Bu fotoğraf bana ait / izinli",
                        variable=self.izin_var).pack(anchor="w", padx=16, pady=4)

        btn_yuz = ttk.Frame(sol, style="Kart.TFrame")
        btn_yuz.pack(fill="x", padx=16, pady=4)
        ttk.Button(btn_yuz, text="Fotoğraf Seç", style="Kart.TButton",
                   command=self._foto_sec).pack(side="left", padx=(0, 6))
        ttk.Button(btn_yuz, text="8 Varyasyon Üret", style="Yesil.TButton",
                   command=self._varyasyon).pack(side="left")

        self.yuz_durum = ttk.Label(sol, text="", style="Kart.TLabel",
                                   wraplength=340)
        self.yuz_durum.pack(anchor="w", padx=16, pady=4)

        # --- Sağ: liste + vesikalık ---
        sag = tk.Frame(paned, bg=KART, highlightthickness=1,
                       highlightbackground=CIZGI)
        paned.add(sag, width=650)

        ust = tk.Frame(sag, bg=KART)
        ust.pack(fill="x", padx=12, pady=(12, 4))
        tk.Label(ust, text="Karakterler", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 13, "bold")).pack(side="left")
        ttk.Button(ust, text="Yenile", style="Kart.TButton",
                   command=self._listeyi_yenile).pack(side="right")

        # Liste + vesikalık yan yana
        liste_f = tk.Frame(sag, bg=KART)
        liste_f.pack(fill="both", expand=True, padx=12, pady=4)

        self.tree = ttk.Treeview(liste_f, columns=("ad", "nis", "seed", "kaynak"),
                                 show="headings", height=10)
        for col, bas in [("ad", "Ad"), ("nis", "Niş"), ("seed", "Seed"),
                         ("kaynak", "Kaynak")]:
            self.tree.heading(col, text=bas)
            self.tree.column(col, width=100)
        self.tree.pack(side="left", fill="both", expand=True)
        self.tree.bind("<<TreeviewSelect>>", self._secim)

        # Vesikalık panel
        ves_f = tk.Frame(liste_f, bg=KART, width=220)
        ves_f.pack(side="right", fill="y", padx=(10, 0))
        ves_f.pack_propagate(False)

        tk.Label(ves_f, text="Vesikalık", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))

        self.vesikalik_kart = tk.Frame(ves_f, bg=ZEMIN, highlightthickness=2,
                                       highlightbackground=TEAL_VURGU, height=230)
        self.vesikalik_kart.pack(fill="x")
        self.vesikalik_kart.pack_propagate(False)
        self.vesikalik_label = tk.Label(
            self.vesikalik_kart, text="Karakter seçin",
            bg=ZEMIN, fg=METIN_KOYU, font=("Segoe UI", 9))
        self.vesikalik_label.pack(expand=True)

        self.vesikalik_bilgi = tk.Label(
            ves_f, text="", bg=KART, fg=METIN_KOYU,
            font=("Segoe UI", 9), justify="left")
        self.vesikalik_bilgi.pack(anchor="w", pady=(6, 0))

        # Varyasyon önizleme alanı
        self.onizleme = tk.Frame(sag, bg=KART)
        self.onizleme.pack(fill="x", padx=12, pady=(4, 12))
        tk.Label(self.onizleme, text="Varyasyonlar (canon seçmek için tıklayın)",
                 bg=KART, fg=METIN_KOYU, font=("Segoe UI", 9)).pack(anchor="w")
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

        self.yuz_durum.config(text="Yüz dönüştürülüyor (offline)...")
        threading.Thread(target=self._varyasyon_worker, args=(pid,),
                         daemon=True).start()

    def _varyasyon_worker(self, pid):
        try:
            from core import yuz_donusum
            import time
            klasor = depolama.URETILEN_KLASOR / "kanon" / str(pid)
            sonuclar = yuz_donusum.varyasyon_uret(
                self.secili_foto, klasor, sayi=8)
            # Persona'ya kaydet
            yollar = [s["gorsel_yol"] for s in sonuclar]
            meta = {"varyasyon_meta": [s["meta"] for s in sonuclar]}
            kisilik.kendi_yuzunden(pid, self.secili_foto, str(meta), yollar)
            self.after(0, lambda: self._varyasyon_bitti(sonuclar))
        except Exception as e:
            self.after(0, lambda: self._varyasyon_hata(str(e)))

    def _varyasyon_bitti(self, sonuclar):
        self.secili_yuz = sonuclar
        self.yuz_durum.config(text=f"{len(sonuclar)} varyasyon üretildi. Canon seçmek için tıklayın.")
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
        except Exception:
            for i, s in enumerate(sonuclar):
                ttk.Button(self.varyasyon_frame, text=f"Varyasyon {i+1}",
                           style="Kart.TButton",
                           command=lambda yol=s["gorsel_yol"]: self._canon_sec_yuz(yol)
                           ).pack(side="left", padx=2)

    def _varyasyon_hata(self, hata):
        self.yuz_durum.config(text=f"Hata: {hata}")

    def _canon_sec_yuz(self, yol):
        secili = self.tree.selection()
        if not secili:
            return
        pid = int(secili[0])
        kisilik.kanon_sec(pid, yol)
        messagebox.showinfo("Tamam", "Canon güncellendi")
        self._listeyi_yenile()

    # --- Liste ---
    def _listeyi_yenile(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for p in kisilik.persona_listele():
            self.tree.insert("", "end", iid=str(p["id"]),
                             values=(p["ad"], p["nis"], p["seed"], p["kaynak"]))

    def _secim(self, event):
        secili = self.tree.selection()
        if not secili:
            return
        pid = int(secili[0])
        persona = kisilik.persona_al(pid)
        if not persona:
            return
        # Vesikalık göster
        kanon = persona.get("kanon_gorsel")
        if kanon:
            self._vesikalik_goster(kanon)
        else:
            self.vesikalik_label.config(image="", text="Canon yüz yok")
            self.vesikalik_label.image = None
        # Bilgi
        self.vesikalik_bilgi.config(
            text=f"Ad: {persona['ad']}\nYaş: {persona.get('yas', '?')}\n"
                 f"Niş: {persona.get('nis', '?')}\n"
                 f"Seed: {persona.get('seed', '?')}\n"
                 f"Kaynak: {persona.get('kaynak', 'ai')}")

    def _vesikalik_goster(self, gorsel_yol):
        try:
            from PIL import Image, ImageTk
            img = Image.open(gorsel_yol)
            w, h = img.size
            oran = VESIKALIK_BOYUT[0] / VESIKALIK_BOYUT[1]
            mevcut = w / h
            if mevcut > oran:
                yeni_w = int(h * oran)
                x = (w - yeni_w) // 2
                img = img.crop((x, 0, x + yeni_w, h))
            else:
                yeni_h = int(w / oran)
                y = (h - yeni_h) // 2
                img = img.crop((0, y, w, y + yeni_h))
            img = img.resize(VESIKALIK_BOYUT, Image.LANCZOS)
            cerceve = Image.new("RGB", (VESIKALIK_BOYUT[0] + 10,
                                        VESIKALIK_BOYUT[1] + 10), (32, 184, 154))
            cerceve.paste(img, (5, 5))
            foto = ImageTk.PhotoImage(cerceve)
            self.vesikalik_label.config(image=foto, text="")
            self.vesikalik_label.image = foto
        except Exception as e:
            self.vesikalik_label.config(image="", text=f"Hata: {e}")
            self.vesikalik_label.image = None
