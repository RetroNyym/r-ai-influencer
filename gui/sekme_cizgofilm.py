# -*- coding: utf-8 -*-
"""Çizgi Film sekmesi: kullanıcının istediği SAHNEYİ birebir üretir.

Otomatik senaryo YAZMAZ — kullanıcı tam olarak ne görmek istediğini yazar,
program o sahneyi seçilen stilde üretir ve kilitli kimliği uygular
(tutarlı karakter). Gerçek animasyonlu video ayrı bir video API'si
isterseniz API sekmesinden (Kling, Runway, Pika vb.) bağlayın.
"""

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core import animasyon, kisilik
from gui.palet import (CIZGI, HATA, KART, METIN_KOYU, METIN_SOLUK,
                       TEAL_KOYU, TEAL_VURGU, ZEMIN)

STILLER = [("Pixar 3D", "pixar"), ("Anime", "anime"),
           ("2D Cartoon", "cartoon"), ("Watercolor", "watercolor"),
           ("Comic", "comic")]


class SekmeCizgiFilm(ttk.Frame):
    def __init__(self, parent, on_karakter=None):
        super().__init__(parent, style="Govde.TFrame")
        self.on_karakter = on_karakter
        self._sonuc = None
        self._gorseller = []
        self._pid_map = {}
        self._kur()
        self._karakterleri_yukle()

    def _kur(self):
        paned = tk.PanedWindow(self, orient="horizontal", bg=ZEMIN,
                               sashwidth=6, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        # --- Sol: sahne girişi + ayarlar ---
        sol = tk.Frame(paned, bg=KART, highlightthickness=1,
                       highlightbackground=CIZGI)
        paned.add(sol, width=400)

        tk.Label(sol, text="Çizgi Film Görseli", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=18, pady=(18, 4))
        tk.Label(sol,
                 text="İstediğiniz sahneyi TAM olarak yazın (her satır\n"
                      "ayrı bir görsel olur). Program sadece o sahneyi\n"
                      "üretir; kilitli kimlikle aynı kişi korunur.\n"
                      "Gerçek animasyon için API sekmesinden video\n"
                      "API'si (Kling/Runway) bağlayın.",
                 bg=KART, fg=METIN_SOLUK, font=("Segoe UI", 9),
                 wraplength=360, justify="left").pack(anchor="w", padx=18)

        # Karakter
        f = ttk.Frame(sol, style="Kart.TFrame")
        f.pack(fill="x", padx=16, pady=(12, 2))
        ttk.Label(f, text="Karakter", style="Kart.TLabel", width=10,
                  anchor="w").pack(side="left")
        self.karakter_cb = ttk.Combobox(f, state="readonly", width=22)
        self.karakter_cb.pack(side="left", fill="x", expand=True)

        # Stil
        f2 = ttk.Frame(sol, style="Kart.TFrame")
        f2.pack(fill="x", padx=16, pady=2)
        ttk.Label(f2, text="Stil", style="Kart.TLabel", width=10,
                  anchor="w").pack(side="left")
        self.stil_cb = ttk.Combobox(f2, values=[s[0] for s in STILLER],
                                    state="readonly", width=22)
        self.stil_cb.current(0)
        self.stil_cb.pack(side="left", fill="x", expand=True)

        # Sahne girişi
        ttk.Label(sol, text="Sahne(ler) — her satır bir görsel",
                  style="Kart.TLabel",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16,
                                                      pady=(10, 2))
        self.sahne = tk.Text(sol, height=6, width=44, font=("Segoe UI", 10),
                             bg=ZEMIN, fg=METIN_KOYU,
                             insertbackground=METIN_KOYU,
                             selectbackground=TEAL_VURGU,
                             selectforeground="#FFFFFF",
                             relief="solid", bd=0,
                             highlightthickness=1,
                             highlightbackground=CIZGI)
        self.sahne.pack(fill="x", padx=16)
        self.sahne.insert("1.0",
                          "otantik bir kahve dükkanında latte yapan karakter,\n"
                          "gün batımında sahilde yürüyen karakter")

        # Butonlar
        ttk.Button(sol, text="Görselleri Üret", style="Yesil.TButton",
                   command=self._uret).pack(fill="x", padx=16, pady=10)

        self.durum = ttk.Label(sol, text="", style="Kart.TLabel",
                               wraplength=360, justify="left")
        self.durum.pack(anchor="w", padx=16, pady=(0, 6))

        # İpucu: klip butonu (çoklu görsel varsa)
        self.klip_btn = ttk.Button(sol, text="Görsellerden Sessiz Klip Kur",
                                   style="Kart.TButton", command=self._klip)
        self.klip_btn.pack(fill="x", padx=16, pady=(2, 12))

        # --- Sağ: önizleme ---
        sag = tk.Frame(paned, bg=KART, highlightthickness=1,
                       highlightbackground=CIZGI)
        paned.add(sag, width=620)

        tk.Label(sag, text="Üretilen Görseller", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(12, 4))

        # Kaydırılabilir görsel alanı
        import tkinter as tkmod
        self.kutu = tk.Canvas(sag, bg=KART, highlightthickness=0)
        self.kaydir = ttk.Scrollbar(sag, orient="vertical",
                                    command=self.kutu.yview)
        self.ic = tk.Frame(self.kutu, bg=KART)
        self.ic.bind("<Configure>",
                     lambda e: self.kutu.configure(scrollregion=self.kutu.bbox("all")))
        self.kutu.create_window((0, 0), window=self.ic, anchor="nw")
        self.kutu.configure(yscrollcommand=self.kaydir.set)
        self.kaydir.pack(side="right", fill="y")
        self.kutu.pack(fill="both", expand=True, padx=(12, 0), pady=4)

        # Mouse tekerleği ile kaydırma
        def _teker(e):
            self.kutu.yview_scroll(int(-1 * (e.delta / 120)), "units")
        self.kutu.bind_all("<MouseWheel>", _teker)

    # ------------------------------------------------------------------
    def _karakterleri_yukle(self):
        personalar = kisilik.persona_listele()
        self._pid_map = {p["ad"]: p["id"] for p in personalar}
        self.karakter_cb["values"] = list(self._pid_map.keys())
        if personalar:
            self.karakter_cb.current(0)

    def _uret(self):
        secili = self.karakter_cb.get()
        if not secili or secili not in self._pid_map:
            messagebox.showwarning("Seçim", "Bir karakter seçin")
            return
        pid = self._pid_map[secili]
        sahneler = self.sahne.get("1.0", "end")
        if not sahneler.strip():
            messagebox.showwarning("Eksik", "Sahne yazın")
            return
        stil = STILLER[self.stil_cb.current()][1]

        self.durum.config(text="Üretiliyor...")
        threading.Thread(target=self._worker, args=(pid, sahneler, stil),
                         daemon=True).start()

    def _worker(self, pid, sahneler, stil):
        try:
            sonuclar = animasyon.gorseller_uret(pid, sahneler, stil=stil,
                                                ilerleme_cb=lambda a, b, m:
                                                self.after(0, lambda: self.durum.config(text=m)))
            self.after(0, lambda: self._bitti(sonuclar))
        except Exception as e:
            self.after(0, lambda: self._hata(str(e)))

    def _bitti(self, sonuclar):
        self._gorseller = sonuclar
        self._sonuc = sonuclar
        self.durum.config(text=f"Tamamlandı: {len(sonuclar)} görsel üretildi")

        for w in self.ic.winfo_children():
            w.destroy()
        try:
            from PIL import Image, ImageTk
            for s in sonuclar:
                img = Image.open(s["gorsel_yol"])
                img.thumbnail((280, 373), Image.LANCZOS)
                foto = ImageTk.PhotoImage(img)
                kart = tk.Frame(self.ic, bg=KART)
                lbl = tk.Label(kart, image=foto, bg=KART)
                lbl.image = foto
                lbl.pack()
                tk.Label(kart, text=s["sahne"][:60], bg=KART, fg=METIN_SOLUK,
                         font=("Segoe UI", 8), wraplength=270,
                         justify="left").pack(pady=(2, 8))
                kart.pack(pady=6)
        except Exception as e:
            self.durum.config(text=f"Önizleme hatası: {e}")

        if self.on_karakter and sonuclar:
            self.on_karakter(sonuclar[0]["gorsel_yol"], "Çizgi Film",
                             f"{len(sonuclar)} görsel")

    def _klip(self):
        if len(self._gorseller) < 2:
            messagebox.showinfo("Bilgi", "Klip için en az 2 görsel üretin")
            return
        yol = filedialog.asksaveasfilename(defaultextension=".mp4",
                                           filetypes=[("MP4 video", "*.mp4")],
                                           initialfile="klip.mp4")
        if not yol:
            return
        self.durum.config(text="Klip kuruluyor...")
        gorseller = [g["gorsel_yol"] for g in self._gorseller]
        threading.Thread(target=self._klip_worker, args=(gorseller, yol),
                         daemon=True).start()

    def _klip_worker(self, gorseller, yol):
        try:
            sonuc = animasyon.klip_yap(gorseller, yol)
            self.after(0, lambda: self.durum.config(
                text=f"Klip hazır: {sonuc['sureSn']}sn · {sonuc['boyut_mb']}MB\n{yol}"))
        except Exception as e:
            self.after(0, lambda: self._hata(str(e)))

    def _hata(self, hata):
        self.durum.config(text=f"Hata: {hata}", fg=HATA)
