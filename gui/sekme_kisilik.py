# -*- coding: utf-8 -*-
"""Karakter sekmesi: persona oluşturma + kendi yüzünden suret (offline)."""

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core import depolama, kisilik, sahne_kutuphanesi

ZEMIN = "#F0F6F5"
KART = "#FFFFFF"
CIZGI = "#D5E5E2"
METIN_KOYU = "#1A2E30"
TEAL_KOYU = "#0D4F5C"
TEAL_VURGU = "#2BB8A0"
YESIL = "#2BB8A0"
YESIL_ACIK = "#E0F5F0"
YESIL_METIN = "#0D5C50"


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
        sol = ttk.Frame(paned, style="Kart.TFrame")
        paned.add(sol, width=380)

        ttk.Label(sol, text="Yeni Karakter", style="Vurgu.TLabel",
                  font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(16, 8))

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

        # --- Sağ: liste + önizleme ---
        sag = ttk.Frame(paned, style="Kart.TFrame")
        paned.add(sag, width=650)

        ust = ttk.Frame(sag, style="Kart.TFrame")
        ust.pack(fill="x", padx=12, pady=(12, 4))
        ttk.Label(ust, text="Karakterler", style="Vurgu.TLabel",
                  font=("Segoe UI", 12, "bold")).pack(side="left")
        ttk.Button(ust, text="Yenile", style="Kart.TButton",
                   command=self._listeyi_yenile).pack(side="right")

        self.tree = ttk.Treeview(sag, columns=("ad", "nis", "seed", "kaynak"),
                                 show="headings", height=10)
        for col, bas in [("ad", "Ad"), ("nis", "Niş"), ("seed", "Seed"),
                         ("kaynak", "Kaynak")]:
            self.tree.heading(col, text=bas)
            self.tree.column(col, width=120)
        self.tree.pack(fill="both", expand=True, padx=12, pady=4)
        self.tree.bind("<<TreeviewSelect>>", self._secim)

        # Varyasyon önizleme alanı
        self.onizleme = ttk.Frame(sag, style="Kart.TFrame")
        self.onizleme.pack(fill="x", padx=12, pady=(4, 12))
        ttk.Label(self.onizleme, text="Varyasyonlar (canon seçmek için tıklayın)",
                  style="Kart.TLabel").pack(anchor="w")
        self.varyasyon_frame = ttk.Frame(self.onizleme, style="Kart.TFrame")
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
        # Önizleme butonları
        for w in self.varyasyon_frame.winfo_children():
            w.destroy()
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
        pass
