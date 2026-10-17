# -*- coding: utf-8 -*-
"""R+ AI Influencer — Ultra premium DARK ana pencere.

Düzen: üst bar (logo + arama + bildirim + karakter çipi) / sol sidebar
(navigasyon) / içerik alanı (sayfa değiştirme) / alt durum barı.
"""

import tkinter as tk
from pathlib import Path
from tkinter import ttk

from gui import sekme_api, sekme_arac, sekme_cizgofilm, sekme_kisilik, \
    sekme_panom, sekme_takvim, sekme_uretim, sekme_video, sekme_yayin
from gui.palet import (AMBER, AMBER_KOYU, AMBER_ZEMIN, BASLIK_SOLUK,
                       BASLIK_ZEMIN, CIZGI, HATA, KART, KART_GOLGE,
                       METIN_KOYU, METIN_SOLUK, SIDEBAR, TEAL, TEAL_KOYU,
                       TEAL_ORTA, TEAL_PARLAK, TEAL_VURGU, VARLIK, YESIL,
                       YESIL_ACIK, YESIL_KOYU, YESIL_METIN, ZEMIN,
                       ZEMIN_KOYU, vesikalik_foto)

IKON = "Segoe MDL2 Assets"

FONT_BASLIK = ("Segoe UI", 15, "bold")
FONT_ALT = ("Segoe UI", 9)
FONT_KART_BASLIK = ("Segoe UI", 12, "bold")
FONT_NORMAL = ("Segoe UI", 10)
FONT_KUCUK = ("Segoe UI", 9)
FONT_BUTON = ("Segoe UI", 10, "bold")

# Sidebar navigasyonu: (anahtar, MDL2 glif, etiket)
NAV = [
    ("panom",     "", "Genel Bakış"),
    ("kisilik",   "", "Karakterler"),
    ("uretim",    "", "Üretim"),
    ("video",     "", "Video Stüdyo"),
    ("cizgofilm", "", "Çizgi Film"),
    ("yayin",     "", "Yayın & Analiz"),
    ("takvim",    "", "Takvim"),
    ("api",       "", "Entegrasyonlar"),
    ("arac",      "", "Araçlar"),
]

ARAMA_YER_TUTUCU = "Karakter, içerik veya özellik ara...  (Enter)"


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
        self.geometry("1360x860")
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
        self._ust_bar()      # önce üst bar (sekme kurulumu vesikalığı çağırır)
        self._govde_kur()    # sidebar + içerik alanı
        self._alt_bar()
        self._sekmeleri_kur()

        self.sayfa_degistir("panom")
        self.protocol("WM_DELETE_WINDOW", self._kapat)

    # ------------------------------------------------------------------
    def _foto_on_yukle(self):
        self._logo = varlik_foto("retro-logo.png", (36, 36))
        self._ig = varlik_foto("ig.png", (22, 22))
        self._tt = varlik_foto("tt.png", (22, 22))

    # ------------------------------------------------------------------
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
                    foreground=HATA, font=FONT_KUCUK)
        s.configure("Basari.TLabel", background=KART,
                    foreground=TEAL_VURGU, font=("Segoe UI", 10, "bold"))

        # Butonlar
        s.configure("Yesil.TButton", background=TEAL_VURGU,
                    foreground="#FFFFFF", font=FONT_BUTON, padding=(16, 8),
                    borderwidth=0)
        s.map("Yesil.TButton",
              background=[("active", TEAL_PARLAK), ("pressed", TEAL_ORTA),
                          ("disabled", "#2A4A44")],
              foreground=[("disabled", METIN_SOLUK)])

        s.configure("Kart.TButton", background=KART_GOLGE,
                    foreground=METIN_KOYU, font=FONT_NORMAL, padding=(12, 6),
                    borderwidth=1, relief="solid", bordercolor=CIZGI)
        s.map("Kart.TButton",
              background=[("active", "#22304F"), ("pressed", "#1B2740")],
              bordercolor=[("focus", TEAL_VURGU)])

        s.configure("Teal.TButton", background=TEAL, foreground="#FFFFFF",
                    font=FONT_NORMAL, padding=(12, 6), borderwidth=0)
        s.map("Teal.TButton",
              background=[("active", TEAL_ORTA), ("pressed", "#0C6157")])

        s.configure("Tehlike.TButton", background="#E85D5D",
                    foreground="#FFFFFF", font=FONT_NORMAL, padding=(12, 6),
                    borderwidth=0)
        s.map("Tehlike.TButton", background=[("active", "#D14343")])

        # Giriş öğeleri (dark)
        s.configure("TEntry",
                    fieldbackground="#0E1729", foreground=METIN_KOYU,
                    bordercolor=CIZGI, lightcolor=CIZGI, borderwidth=1,
                    insertcolor=METIN_KOYU, padding=6)
        s.map("TEntry",
              bordercolor=[("focus", TEAL_VURGU)],
              lightcolor=[("focus", TEAL_VURGU)])

        s.configure("TCombobox",
                    fieldbackground="#0E1729", background=KART,
                    foreground=METIN_KOYU, arrowcolor=METIN_SOLUK,
                    bordercolor=CIZGI, borderwidth=1, padding=4)
        s.map("TCombobox",
              fieldbackground=[("readonly", "#0E1729"),
                               ("disabled", ZEMIN_KOYU)],
              background=[("readonly", KART), ("active", KART_GOLGE)],
              foreground=[("readonly", METIN_KOYU)],
              bordercolor=[("focus", TEAL_VURGU)])
        self.option_add("*TCombobox*Listbox.background", "#0E1729")
        self.option_add("*TCombobox*Listbox.foreground", METIN_KOYU)
        self.option_add("*TCombobox*Listbox.selectBackground", TEAL)
        self.option_add("*TCombobox*Listbox.selectForeground", "#FFFFFF")

        s.configure("TSpinbox",
                    fieldbackground="#0E1729", foreground=METIN_KOYU,
                    arrowcolor=METIN_SOLUK, bordercolor=CIZGI,
                    insertcolor=METIN_KOYU, padding=4)
        s.map("TSpinbox", bordercolor=[("focus", TEAL_VURGU)])

        s.configure("TCheckbutton", background=KART, foreground=METIN_KOYU,
                    font=FONT_NORMAL)
        s.map("TCheckbutton",
              background=[("active", KART)],
              foreground=[("active", METIN_KOYU)])

        s.configure("TRadiobutton", background=KART, foreground=METIN_KOYU,
                    font=FONT_NORMAL)
        s.map("TRadiobutton", background=[("active", KART)])

        s.configure("TSeparator", background=CIZGI)
        s.configure("TProgressbar", troughcolor=ZEMIN_KOYU,
                    background=TEAL_VURGU, thickness=12)

        # Tablolar
        s.configure("Treeview", background=KART, fieldbackground=KART,
                    foreground=METIN_KOYU, rowheight=30,
                    font=("Segoe UI", 10), borderwidth=0)
        s.configure("Treeview.Heading", background=KART_GOLGE,
                    foreground=METIN_SOLUK, font=("Segoe UI", 9, "bold"),
                    borderwidth=0)
        s.map("Treeview",
              background=[("selected", TEAL)],
              foreground=[("selected", "#FFFFFF")])
        s.map("Treeview.Heading",
              background=[("active", "#22304F")])

        # Kaydırma çubukları
        s.configure("Vertical.TScrollbar",
                    background=CIZGI, troughcolor=ZEMIN_KOYU,
                    bordercolor=ZEMIN_KOYU, arrowcolor=METIN_SOLUK,
                    borderwidth=0)
        s.map("Vertical.TScrollbar",
              background=[("active", TEAL), ("pressed", TEAL_ORTA)])
        s.configure("Horizontal.TScrollbar",
                    background=CIZGI, troughcolor=ZEMIN_KOYU,
                    bordercolor=ZEMIN_KOYU, arrowcolor=METIN_SOLUK,
                    borderwidth=0)
        s.map("Horizontal.TScrollbar",
              background=[("active", TEAL)])

        s.configure("Horizontal.TScale", background=ZEMIN,
                    troughcolor=CIZGI)

        # Genel seçim/imleç renkleri (tk.Listbox / tk.Text için)
        self.option_add("*Listbox.selectBackground", TEAL)
        self.option_add("*Listbox.selectForeground", "#FFFFFF")
        self.option_add("*Text.selectBackground", TEAL)
        self.option_add("*Text.selectForeground", "#FFFFFF")
        self.option_add("*Text.insertBackground", METIN_KOYU)

    # ------------------------------------------------------------------
    def _ust_bar(self):
        bar = tk.Frame(self, bg=SIDEBAR, height=64)
        bar.pack(fill="x", side="top")
        bar.pack_propagate(False)

        # Sol: logo + başlık
        sol = tk.Frame(bar, bg=SIDEBAR)
        sol.pack(side="left", padx=(18, 0))
        if self._logo:
            tk.Label(sol, image=self._logo, bg=SIDEBAR).pack(
                side="left", padx=(0, 10))
        tk.Label(sol, text="R+ CREATOR STUDIO", bg=SIDEBAR, fg="#FFFFFF",
                 font=("Segoe UI", 14, "bold")).pack(side="left")

        # Orta: arama
        ara_f = tk.Frame(bar, bg=SIDEBAR)
        ara_f.pack(side="left", expand=True, fill="x", padx=(36, 24))
        kutu = tk.Frame(ara_f, bg="#0E1729", highlightthickness=1,
                        highlightbackground=CIZGI)
        kutu.pack(fill="x")
        tk.Label(kutu, text="", bg="#0E1729", fg=METIN_SOLUK,
                 font=(IKON, 12)).pack(side="left", padx=(10, 6))
        self.arama = tk.Entry(kutu, bg="#0E1729", fg=METIN_SOLUK,
                              insertbackground=METIN_SOLUK, relief="flat",
                              font=("Segoe UI", 10), bd=0)
        self.arama.pack(side="left", fill="x", expand=True, ipady=7)
        self.arama.insert(0, ARAMA_YER_TUTUCU)
        self.arama.bind("<FocusIn>", self._arama_odak_gir)
        self.arama.bind("<FocusOut>", self._arama_odak_cik)
        self.arama.bind("<Return>", self._arama_calistir)
        tk.Label(kutu, text="Ctrl + K", bg="#0E1729", fg=METIN_SOLUK,
                 font=("Segoe UI", 8)).pack(side="right", padx=10)
        self.bind_all("<Control-k>", lambda e: self.arama.focus_set())

        # Sağ: bildirim + karakter çipi
        sag = tk.Frame(bar, bg=SIDEBAR)
        sag.pack(side="right", padx=(0, 18))

        bildirim = tk.Frame(sag, bg=SIDEBAR, width=30, height=30)
        bildirim.pack(side="left", padx=(0, 16))
        bildirim.pack_propagate(False)
        tk.Label(bildirim, text="", bg=SIDEBAR, fg=METIN_SOLUK,
                 font=(IKON, 13)).place(relx=0.5, rely=0.5, anchor="center")
        tk.Label(bildirim, text="", bg=TEAL_VURGU, width=1, height=1).place(
            relx=0.78, rely=0.22)

        cip = tk.Frame(sag, bg=SIDEBAR)
        cip.pack(side="left")
        self.cip_foto = tk.Label(cip, text="👤", bg=SIDEBAR, fg=METIN_SOLUK,
                                 font=("Segoe UI", 15), width=4, height=3,
                                 highlightthickness=1,
                                 highlightbackground=CIZGI)
        self.cip_foto.pack(side="left", padx=(0, 10))
        bilgi = tk.Frame(cip, bg=SIDEBAR)
        bilgi.pack(side="left")
        self.cip_ad = tk.Label(bilgi, text="R+ Creator", bg=SIDEBAR,
                               fg="#FFFFFF", font=("Segoe UI", 10, "bold"),
                               anchor="w")
        self.cip_ad.pack(anchor="w")
        self.cip_alt = tk.Label(bilgi, text="retro+ studio", bg=SIDEBAR,
                                fg=BASLIK_SOLUK, font=("Segoe UI", 8),
                                anchor="w")
        self.cip_alt.pack(anchor="w")
        tk.Label(cip, text="▾", bg=SIDEBAR, fg=METIN_SOLUK,
                 font=("Segoe UI", 10)).pack(side="left", padx=(6, 0))

        # İnce turkuaz ayraç
        tk.Frame(self, bg=TEAL_VURGU, height=2).pack(fill="x")

    def _arama_odak_gir(self, event=None):
        if self.arama.get() == ARAMA_YER_TUTUCU:
            self.arama.delete(0, "end")
            self.arama.config(fg=METIN_KOYU)

    def _arama_odak_cik(self, event=None):
        if not self.arama.get().strip():
            self.arama.insert(0, ARAMA_YER_TUTUCU)
            self.arama.config(fg=METIN_SOLUK)

    def _arama_calistir(self, event=None):
        metin = self.arama.get().strip().lower()
        if not metin or metin == ARAMA_YER_TUTUCU.lower():
            return
        for anahtar, _, etiket in NAV:
            if metin in etiket.lower() or etiket.lower() in metin:
                self.sayfa_degistir(anahtar)
                self.arama.config(fg=METIN_KOYU)
                return
        # Eşleşme yoksa kırmızı kısa uyarı
        self.arama.config(fg=HATA)
        self.after(700, lambda: self.arama.config(fg=METIN_KOYU))

    # ------------------------------------------------------------------
    def _govde_kur(self):
        govde = tk.Frame(self, bg=ZEMIN)
        govde.pack(fill="both", expand=True)

        # --- Sidebar ---
        yan = tk.Frame(govde, bg=SIDEBAR, width=230)
        yan.pack(side="left", fill="y")
        yan.pack_propagate(False)
        tk.Frame(yan, bg=SIDEBAR, highlightthickness=1,
                 highlightbackground=CIZGI, bd=0).pack(fill="x")

        tk.Label(yan, text="MENÜ", bg=SIDEBAR, fg=METIN_SOLUK,
                 font=("Segoe UI", 8, "bold"), anchor="w").pack(
            fill="x", padx=20, pady=(18, 6))

        self._nav_cerceve = {}
        for anahtar, glif, etiket in NAV:
            self._nav_oge(yan, anahtar, glif, etiket)

        # Alt: marka bloğu
        marka = tk.Frame(yan, bg=SIDEBAR)
        marka.pack(side="bottom", fill="x", padx=20, pady=(0, 18))
        tk.Label(marka, text="R+", bg=SIDEBAR, fg=TEAL_VURGU,
                 font=("Segoe UI", 26, "bold"), anchor="w").pack(anchor="w")
        tk.Label(marka, text="Create Real Connections\nwith AI", bg=SIDEBAR,
                 fg=BASLIK_SOLUK, font=("Segoe UI", 9),
                 justify="left").pack(anchor="w")

        # --- İçerik alanı (sayfalar buraya pack edilir) ---
        self.icerik = tk.Frame(govde, bg=ZEMIN)
        self.icerik.pack(side="left", fill="both", expand=True)
        self._sayfalar = {}
        self._aktif_sayfa = None

    def _nav_oge(self, parent, anahtar, glif, etiket):
        satir = tk.Frame(parent, bg=SIDEBAR, height=40, cursor="hand2")
        satir.pack(fill="x", padx=10, pady=2)
        satir.pack_propagate(False)
        aksan = tk.Frame(satir, bg=SIDEBAR, width=3)
        aksan.pack(side="left", fill="y")
        ikon_lbl = tk.Label(satir, text=glif, bg=SIDEBAR, fg=METIN_SOLUK,
                            font=(IKON, 13), width=2)
        ikon_lbl.pack(side="left", padx=(10, 8))
        metin_lbl = tk.Label(satir, text=etiket, bg=SIDEBAR, fg=METIN_SOLUK,
                             font=("Segoe UI", 10), anchor="w")
        metin_lbl.pack(side="left", fill="x")

        kayit = {"satir": satir, "aksan": aksan,
                 "ikon": ikon_lbl, "metin": metin_lbl, "aktif": False}

        def tikla(event=None):
            self.sayfa_degistir(anahtar)

        def gir(event=None):
            if not kayit["aktif"]:
                satir.config(bg="#16223A")
                ikon_lbl.config(bg="#16223A")
                metin_lbl.config(bg="#16223A")

        def cik(event=None):
            if not kayit["aktif"]:
                satir.config(bg=SIDEBAR)
                ikon_lbl.config(bg=SIDEBAR)
                metin_lbl.config(bg=SIDEBAR)

        for w in (satir, ikon_lbl, metin_lbl):
            w.bind("<Button-1>", tikla)
            w.bind("<Enter>", gir)
            w.bind("<Leave>", cik)
        self._nav_cerceve[anahtar] = kayit

    def _nav_vurgula(self, anahtar):
        for k, kayit in self._nav_cerceve.items():
            secili = (k == anahtar)
            kayit["aktif"] = secili
            zemin = YESIL_ACIK if secili else SIDEBAR
            renk = TEAL_PARLAK if secili else METIN_SOLUK
            kayit["satir"].config(bg=zemin)
            kayit["ikon"].config(bg=zemin, fg=renk)
            kayit["metin"].config(bg=zemin, fg=renk)
            kayit["aksan"].config(bg=TEAL_VURGU if secili else SIDEBAR)

    # ------------------------------------------------------------------
    def _sekmeleri_kur(self):
        p = self.icerik
        self.sekme_panom = sekme_panom.SekmePanom(
            p, git=self.sayfa_degistir)
        self.sekme_kisilik = sekme_kisilik.SekmeKisilik(
            p, on_karakter=self.vesikalik_guncelle)
        self.sekme_uretim = sekme_uretim.SekmeUretim(
            p, on_karakter=self.vesikalik_guncelle)
        self.sekme_video = sekme_video.SekmeVideo(p)
        self.sekme_cizgofilm = sekme_cizgofilm.SekmeCizgiFilm(
            p, on_karakter=self.vesikalik_guncelle)
        self.sekme_yayin = sekme_yayin.SekmeYayin(p)
        self.sekme_takvim = sekme_takvim.SekmeTakvim(p)
        self.sekme_api = sekme_api.SekmeApi(p, ig_foto=self._ig,
                                            tt_foto=self._tt)
        self.sekme_arac = sekme_arac.SekmeArac(p)

        self._sayfalar = {
            "panom": self.sekme_panom,
            "kisilik": self.sekme_kisilik,
            "uretim": self.sekme_uretim,
            "video": self.sekme_video,
            "cizgofilm": self.sekme_cizgofilm,
            "yayin": self.sekme_yayin,
            "takvim": self.sekme_takvim,
            "api": self.sekme_api,
            "arac": self.sekme_arac,
        }

    def sayfa_degistir(self, anahtar):
        """Sidebar'dan/aramadan çağrılan sayfa geçişi + tazeleme."""
        if anahtar not in self._sayfalar:
            return
        if self._aktif_sayfa != anahtar:
            for frame in self._sayfalar.values():
                frame.pack_forget()
            self._sayfalar[anahtar].pack(fill="both", expand=True)
            self._aktif_sayfa = anahtar
            self._nav_vurgula(anahtar)

        # Sayfaya özel tazeleme (eski <<NotebookTabChanged>> davranışı)
        try:
            if anahtar == "panom":
                self.sekme_panom.yenile()
            elif anahtar == "uretim":
                self.sekme_uretim._yukle()
            elif anahtar == "video":
                self.sekme_video._yukle()
            elif anahtar == "cizgofilm":
                self.sekme_cizgofilm._karakterleri_yukle()
            elif anahtar == "yayin":
                self.sekme_yayin._yukle()
            elif anahtar == "takvim":
                self.sekme_takvim._yukle()
            elif anahtar == "api":
                self.sekme_api._yukle()
        except Exception:
            pass

    # Geriye dönük uyumluluk (eski test scriptleri)
    def _sekme_degisti(self, event=None):
        if self._aktif_sayfa:
            self.sayfa_degistir(self._aktif_sayfa)

    # ------------------------------------------------------------------
    def vesikalik_guncelle(self, gorsel_yol, baslik="", alt=""):
        """Üst bardaki karakter çipini günceller (her sekmede görünür)."""
        self.cip_ad.config(text=baslik or "R+ Creator")
        self.cip_alt.config(text=alt or "retro+ studio")
        try:
            if gorsel_yol:
                foto = vesikalik_foto(gorsel_yol, boyut=(30, 40))
                self.cip_foto.config(image=foto, text="",
                                     width=0, height=0)
                self.cip_foto.image = foto
            else:
                self.cip_foto.config(image="", text="👤",
                                     width=4, height=3)
                self.cip_foto.image = None
        except Exception:
            self.cip_foto.config(image="", text="👤", width=4, height=3)
            self.cip_foto.image = None

    # ------------------------------------------------------------------
    def _alt_bar(self):
        bar = tk.Frame(self, bg=SIDEBAR, height=32)
        bar.pack(fill="x", side="bottom")
        bar.pack_propagate(False)
        tk.Frame(bar, bg=CIZGI, height=1).pack(fill="x")

        sol = tk.Frame(bar, bg=SIDEBAR)
        sol.pack(side="left", padx=16)
        tk.Label(sol, text="●", bg=SIDEBAR, fg=TEAL_VURGU,
                 font=("Segoe UI", 8)).pack(side="left")
        tk.Label(sol, text="  Tüm sistemler hazır", bg=SIDEBAR,
                 fg=METIN_SOLUK, font=("Segoe UI", 9)).pack(side="left")
        tk.Frame(sol, bg=CIZGI, width=1).pack(side="left", fill="y",
                                              padx=12, pady=6)
        tk.Label(sol, text="●", bg=SIDEBAR, fg=AMBER,
                 font=("Segoe UI", 8)).pack(side="left")
        tk.Label(sol, text="  Yerel üretim açık", bg=SIDEBAR,
                 fg=METIN_SOLUK, font=("Segoe UI", 9)).pack(side="left")

        tk.Label(bar, text="  v1.0.0  ·  R+ AI Influencer  ", bg=SIDEBAR,
                 fg=METIN_SOLUK, font=("Segoe UI", 9)).pack(side="right")

    # ------------------------------------------------------------------
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
