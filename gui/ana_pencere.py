# -*- coding: utf-8 -*-
"""R+ AI Influencer — Premium ana pencere."""

import sys
import tkinter as tk
from pathlib import Path
from tkinter import ttk

from gui import sekme_api, sekme_kisilik, sekme_takvim, sekme_uretim

# --- retro+ premium palet ---
TEAL_KOYU = "#0A3D47"
TEAL = "#0F6B6B"
TEAL_ORTA = "#148A7D"
TEAL_VURGU = "#20B89A"
TEAL_PARLAK = "#3DDBB5"
ZEMIN = "#EDF4F3"
ZEMIN_KOYU = "#E2ECEA"
KART = "#FFFFFF"
KART_GOLGE = "#D0DEDC"
CIZGI = "#C8D8D5"
METIN_KOYU = "#0F2A2C"
METIN_SOLUK = "#5A7A78"
BASLIK_ZEMIN = TEAL_KOYU
BASLIK_SOLUK = "#7AB5AE"
YESIL = TEAL_VURGU
YESIL_KOYU = TEAL_ORTA
YESIL_METIN = "#0A5C4E"
YESIL_ACIK = "#DFF5EE"
AMBER = "#F0A830"
AMBER_KOYU = "#C07800"
AMBER_ZEMIN = "#FFF6E5"

VARLIK = Path(__file__).resolve().parent.parent / "varlik"

FONT_BASLIK = ("Segoe UI", 18, "bold")
FONT_ALT = ("Segoe UI", 9)
FONT_KART_BASLIK = ("Segoe UI", 12, "bold")
FONT_NORMAL = ("Segoe UI", 10)
FONT_KUCUK = ("Segoe UI", 9)
FONT_BUTON = ("Segoe UI", 10, "bold")


def varlik_foto(ad, boyut=None):
    """varlik/ klasöründen foto yükle."""
    try:
        from PIL import Image, ImageTk
        yol = VARLIK / ad
        if not yol.is_file():
            return None
        img = Image.open(yol)
        if boyut:
            img = img.resize(boyut, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


class PremiumFrame(tk.Frame):
    """Gölgeli kart çerçevesi."""
    def __init__(self, parent, bg=KART, **kw):
        super().__init__(parent, bg=KART, highlightthickness=1,
                         highlightbackground=CIZGI, **kw)


class AnaPencere(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("R+ AI Influencer Otomasyonu")
        self.geometry("1280x820")
        self.minsize(1100, 720)
        self.configure(bg=ZEMIN)

        ico = VARLIK / "retro-logo.ico"
        if ico.is_file():
            try:
                self.iconbitmap(str(ico))
            except Exception:
                pass

        self._foto_on_yukle()
        self._stil_kur()
        self._baslik_cubugu()
        self._sekmeler()
        self._durum_cubugu()

        self.protocol("WM_DELETE_WINDOW", self._kapat)

    def _foto_on_yukle(self):
        self._logo = varlik_foto("retro-logo.png", (52, 52))
        self._ig = varlik_foto("ig.png", (22, 22))
        self._tt = varlik_foto("tt.png", (22, 22))

    def _stil_kur(self):
        s = ttk.Style(self)
        s.theme_use("clam")

        s.configure("Baslik.TFrame", background=BASLIK_ZEMIN)
        s.configure("Govde.TFrame", background=ZEMIN)
        s.configure("Kart.TFrame", background=KART)
        s.configure("KartVurgu.TFrame", background=YESIL_ACIK)

        s.configure("Baslik.TLabel", background=BASLIK_ZEMIN,
                    foreground="#FFFFFF", font=FONT_BASLIK)
        s.configure("AltBaslik.TLabel", background=BASLIK_ZEMIN,
                    foreground=BASLIK_SOLUK, font=FONT_ALT)
        s.configure("Govde.TLabel", background=ZEMIN,
                    foreground=METIN_KOYU, font=FONT_NORMAL)
        s.configure("Kart.TLabel", background=KART,
                    foreground=METIN_KOYU, font=FONT_NORMAL)
        s.configure("KartKucuk.TLabel", background=KART,
                    foreground=METIN_SOLUK, font=FONT_KUCUK)
        s.configure("Vurgu.TLabel", background=KART,
                    foreground=TEAL_KOYU, font=FONT_KART_BASLIK)
        s.configure("VurguGovde.TLabel", background=ZEMIN,
                    foreground=TEAL_KOYU, font=FONT_KART_BASLIK)
        s.configure("BaslikBeyaz.TLabel", background=BASLIK_ZEMIN,
                    foreground="#FFFFFF", font=FONT_KART_BASLIK)
        s.configure("Hata.TLabel", background=KART,
                    foreground="#C62828", font=FONT_KUCUK)
        s.configure("Basari.TLabel", background=KART,
                    foreground=TEAL_VURGU, font=("Segoe UI", 10, "bold"))

        # Butonlar
        s.configure("Yesil.TButton", background=TEAL_VURGU, foreground="#FFFFFF",
                    font=FONT_BUTON, padding=(16, 8), borderwidth=0)
        s.map("Yesil.TButton",
              background=[("active", TEAL_PARLAK), ("pressed", TEAL_ORTA),
                          ("disabled", "#B0C4C0")],
              foreground=[("disabled", "#6A8A88")])

        s.configure("Kart.TButton", background=KART, foreground=METIN_KOYU,
                    font=FONT_NORMAL, padding=(12, 6), borderwidth=1,
                    relief="solid", bordercolor=CIZGI)
        s.map("Kart.TButton",
              background=[("active", YESIL_ACIK), ("pressed", "#C8EBE0")])

        s.configure("Teal.TButton", background=TEAL, foreground="#FFFFFF",
                    font=FONT_NORMAL, padding=(12, 6), borderwidth=0)
        s.map("Teal.TButton", background=[("active", TEAL_ORTA)])

        s.configure("Tehlike.TButton", background="#E85D5D", foreground="#FFFFFF",
                    font=FONT_NORMAL, padding=(12, 6), borderwidth=0)
        s.map("Tehlike.TButton", background=[("active", "#D14343")])

        # Notebook
        s.configure("Notebook.TNotebook", background=ZEMIN, borderwidth=0)
        s.configure("Notebook.TNotebook.Tab", background=KART,
                    foreground=METIN_SOLUK, padding=(20, 10),
                    font=("Segoe UI", 10, "bold"), borderwidth=0)
        s.map("Notebook.TNotebook.Tab",
              background=[("selected", TEAL_VURGU)],
              foreground=[("selected", "#FFFFFF")])

        s.configure("TProgressbar", troughcolor=ZEMIN_KOYU,
                    background=TEAL_VURGU, thickness=16)

        s.configure("Treeview", background=KART, fieldbackground=KART,
                    foreground=METIN_KOYU, rowheight=30,
                    font=("Segoe UI", 10), borderwidth=0)
        s.configure("Treeview.Heading", background=TEAL, foreground="#FFFFFF",
                    font=("Segoe UI", 10, "bold"), borderwidth=0)
        s.map("Treeview",
              background=[("selected", TEAL_VURGU)],
              foreground=[("selected", "#FFFFFF")])

        s.configure("Horizontal.TScale", background=ZEMIN, troughcolor=CIZGI)

    def _baslik_cubugu(self):
        bar = tk.Frame(self, bg=BASLIK_ZEMIN, height=76)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        sol = tk.Frame(bar, bg=BASLIK_ZEMIN)
        sol.pack(side="left", padx=20, pady=12)

        if self._logo:
            lbl_logo = tk.Label(sol, image=self._logo, bg=BASLIK_ZEMIN)
            lbl_logo.pack(side="left", padx=(0, 12))

        metin = tk.Frame(sol, bg=BASLIK_ZEMIN)
        metin.pack(side="left", pady=4)
        tk.Label(metin, text="R+ AI Influencer", bg=BASLIK_ZEMIN,
                 fg="#FFFFFF", font=FONT_BASLIK).pack(anchor="w")
        tk.Label(metin, text="retro+  ·  Premium sanal influencer stüdyosu",
                 bg=BASLIK_ZEMIN, fg=BASLIK_SOLUK, font=FONT_ALT).pack(anchor="w")

        # Sağ rozet
        rozet = tk.Frame(bar, bg=BASLIK_ZEMIN)
        rozet.pack(side="right", padx=20)
        tk.Label(rozet, text="R+", bg=TEAL_VURGU, fg="#FFFFFF",
                 font=("Segoe UI", 16, "bold"), width=5, height=1).pack()

        # Gradient şerit
        serit = tk.Frame(self, bg=TEAL_VURGU, height=3)
        serit.pack(fill="x")

    def _sekmeler(self):
        self.notebook = ttk.Notebook(self, style="Notebook.TNotebook")
        self.notebook.pack(fill="both", expand=True, padx=14, pady=(10, 0))

        self.sekme_kisilik = sekme_kisilik.SekmeKisilik(self.notebook)
        self.sekme_uretim = sekme_uretim.SekmeUretim(self.notebook)
        self.sekme_takvim = sekme_takvim.SekmeTakvim(self.notebook)
        self.sekme_api = sekme_api.SekmeApi(self.notebook,
                                            ig_foto=self._ig,
                                            tt_foto=self._tt)

        self.notebook.add(self.sekme_kisilik, text="  Karakter  ")
        self.notebook.add(self.sekme_uretim, text="  Üretim & Onay  ")
        self.notebook.add(self.sekme_takvim, text="  Takvim  ")
        self.notebook.add(self.sekme_api, text="  API & Bağlantılar  ")

    def _durum_cubugu(self):
        bar = tk.Frame(self, bg=BASLIK_ZEMIN, height=30)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Label(bar, text="  R+ v1.0  ·  retro+ premium  ·  MIT License",
                 bg=BASLIK_ZEMIN, fg=BASLIK_SOLUK, anchor="w",
                 font=("Segoe UI", 9)).pack(fill="x", padx=16, pady=5)

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
