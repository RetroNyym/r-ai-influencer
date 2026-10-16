# -*- coding: utf-8 -*-
"""AI Influencer — Ana pencere (retro+ R+ paleti)."""

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from gui import sekme_api, sekme_kisilik, sekme_takvim, sekme_uretim

# --- retro+ R+ paleti (logo gradient'inden) ---
TEAL_KOYU = "#0D4F5C"      # logo sol üst
TEAL = "#147A7A"           # orta
TEAL_ACIK = "#1A9E8E"      # sağ alt
TEAL_VURGU = "#2BB8A0"     # parlak vurgu
ZEMIN = "#F0F6F5"          # camgöbeği açık zemin
KART = "#FFFFFF"
CIZGI = "#D5E5E2"
METIN_KOYU = "#1A2E30"
METIN_SOLUK = "#6B8A88"
BASLIK_ZEMIN = TEAL_KOYU
BASLIK_SOLUK = "#8FBFBC"
YESIL = "#2BB8A0"
YESIL_KOYU = "#1A9E8E"
YESIL_METIN = "#0D5C50"
YESIL_ACIK = "#E0F5F0"
AMBER = "#F5A623"
AMBER_ZEMIN = "#FFF4E0"

VARLIK = Path(__file__).resolve().parent.parent / "varlik"


class AnaPencere(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("R+ AI Influencer Otomasyonu")
        self.geometry("1180x780")
        self.minsize(1000, 680)
        self.configure(bg=ZEMIN)

        # Pencere ikonu
        ico = VARLIK / "retro-logo.ico"
        if ico.is_file():
            try:
                self.iconbitmap(str(ico))
            except Exception:
                pass

        self._foto_yukle()
        self._stil_kur()
        self._baslik_cubugu()
        self._sekmeler()
        self._durum_cubugu()

        self.protocol("WM_DELETE_WINDOW", self._kapat)

    def _foto_yukle(self):
        """R+ logosu ve sosyal medya ikonlarını yükler."""
        self._logo_foto = None
        self._ig_foto = None
        self._tt_foto = None
        try:
            from PIL import Image, ImageTk
            logo_yol = VARLIK / "retro-logo.png"
            if logo_yol.is_file():
                img = Image.open(logo_yol).resize((48, 48), Image.LANCZOS)
                self._logo_foto = ImageTk.PhotoImage(img)
            for anahtar, dosya in [("_ig_foto", "ig.png"), ("_tt_foto", "tt.png")]:
                yol = VARLIK / dosya
                if yol.is_file():
                    img = Image.open(yol).resize((20, 20), Image.LANCZOS)
                    setattr(self, anahtar, ImageTk.PhotoImage(img))
        except Exception:
            pass

    def _stil_kur(self):
        style = ttk.Style(self)
        style.theme_use("clam")

        style.configure("Baslik.TFrame", background=BASLIK_ZEMIN)
        style.configure("Govde.TFrame", background=ZEMIN)
        style.configure("Kart.TFrame", background=KART, relief="flat")
        style.configure("Teal.TFrame", background=TEAL, relief="flat")

        style.configure("Baslik.TLabel", background=BASLIK_ZEMIN,
                        foreground="#FFFFFF", font=("Segoe UI", 17, "bold"))
        style.configure("AltBaslik.TLabel", background=BASLIK_ZEMIN,
                        foreground=BASLIK_SOLUK, font=("Segoe UI", 9))
        style.configure("Govde.TLabel", background=ZEMIN,
                        foreground=METIN_KOYU, font=("Segoe UI", 10))
        style.configure("Kart.TLabel", background=KART,
                        foreground=METIN_KOYU, font=("Segoe UI", 10))
        style.configure("Vurgu.TLabel", background=KART,
                        foreground=TEAL_KOYU, font=("Segoe UI", 10, "bold"))
        style.configure("VurguGovde.TLabel", background=ZEMIN,
                        foreground=TEAL_KOYU, font=("Segoe UI", 10, "bold"))
        style.configure("Hata.TLabel", background=KART,
                        foreground="#B00020", font=("Segoe UI", 9))
        style.configure("Amber.TLabel", background=AMBER_ZEMIN,
                        foreground="#8A5200", font=("Segoe UI", 9))

        style.configure("Yesil.TButton", background=TEAL_VURGU, foreground="#FFFFFF",
                        font=("Segoe UI", 10, "bold"), padding=(12, 6))
        style.map("Yesil.TButton",
                  background=[("active", TEAL_ACIK), ("disabled", "#CCCCCC")],
                  foreground=[("disabled", "#888888")])

        style.configure("Kart.TButton", background=KART, foreground=METIN_KOYU,
                        font=("Segoe UI", 10), padding=(10, 5))
        style.map("Kart.TButton", background=[("active", YESIL_ACIK)])

        style.configure("Teal.TButton", background=TEAL, foreground="#FFFFFF",
                        font=("Segoe UI", 10), padding=(10, 5))
        style.map("Teal.TButton", background=[("active", TEAL_ACIK)])

        style.configure("Notebook.TNotebook", background=ZEMIN, borderwidth=0)
        style.configure("Notebook.TNotebook.Tab", background=KART,
                        foreground=METIN_KOYU, padding=(18, 9),
                        font=("Segoe UI", 10, "bold"))
        style.map("Notebook.TNotebook.Tab",
                  background=[("selected", TEAL_VURGU)],
                  foreground=[("selected", "#FFFFFF")])

        style.configure("TProgressbar", troughcolor=CIZGI,
                        background=TEAL_VURGU, thickness=14)

        style.configure("Treeview", background=KART, fieldbackground=KART,
                        foreground=METIN_KOYU, rowheight=26,
                        font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=TEAL, foreground="#FFFFFF",
                        font=("Segoe UI", 9, "bold"))
        style.map("Treeview", background=[("selected", TEAL_VURGU)],
                  foreground=[("selected", "#FFFFFF")])

    def _baslik_cubugu(self):
        bar = tk.Frame(self, bg=BASLIK_ZEMIN, height=72)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        # R+ logosu
        if self._logo_foto:
            lbl_logo = tk.Label(bar, image=self._logo_foto, bg=BASLIK_ZEMIN)
            lbl_logo.pack(side="left", padx=(18, 10), pady=12)

        sol = tk.Frame(bar, bg=BASLIK_ZEMIN)
        sol.pack(side="left", pady=10)
        tk.Label(sol, text="R+ AI Influencer", bg=BASLIK_ZEMIN,
                 fg="#FFFFFF", font=("Segoe UI", 17, "bold")).pack(anchor="w")
        tk.Label(sol, text="retro+  ·  Ücretsiz sanal influencer üretim & paylaşım",
                 bg=BASLIK_ZEMIN, fg=BASLIK_SOLUK,
                 font=("Segoe UI", 9)).pack(anchor="w")

        # Sağ: rozet
        sag = tk.Frame(bar, bg=BASLIK_ZEMIN)
        sag.pack(side="right", padx=18)
        tk.Label(sag, text="R+", bg=TEAL_VURGU, fg="#FFFFFF",
                 font=("Segoe UI", 14, "bold"), width=4, height=1,
                 relief="flat").pack()

        # Gradient şerit
        serit = tk.Frame(self, bg=TEAL_VURGU, height=3)
        serit.pack(fill="x")

    def _sekmeler(self):
        self.notebook = ttk.Notebook(self, style="Notebook.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(8, 0))

        self.sekme_kisilik = sekme_kisilik.SekmeKisilik(self.notebook)
        self.sekme_uretim = sekme_uretim.SekmeUretim(self.notebook)
        self.sekme_takvim = sekme_takvim.SekmeTakvim(self.notebook)
        self.sekme_api = sekme_api.SekmeApi(self.notebook,
                                            ig_foto=self._ig_foto,
                                            tt_foto=self._tt_foto)

        self.notebook.add(self.sekme_kisilik, text="  Karakter  ")
        self.notebook.add(self.sekme_uretim, text="  Üretim & Onay  ")
        self.notebook.add(self.sekme_takvim, text="  Takvim  ")
        self.notebook.add(self.sekme_api, text="  API & Bağlantılar  ")

    def _durum_cubugu(self):
        self.durum = tk.StringVar(value="Hazır  ·  retro+")
        bar = tk.Frame(self, bg=TEAL_KOYU, height=28)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Label(bar, textvariable=self.durum, bg=TEAL_KOYU,
                 fg=BASLIK_SOLUK, anchor="w",
                 font=("Segoe UI", 9)).pack(fill="x", padx=16, pady=4)

    def _kapat(self):
        try:
            from core import zamanlayici
            zamanlayici.durdur()
        except Exception:
            pass
        self.destroy()


def calistir():
    from core import depolama
    depolama.kur()
    app = AnaPencere()
    app.mainloop()
