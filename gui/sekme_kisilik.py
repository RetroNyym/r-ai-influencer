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

        # Karakter bilgi paneli
        bilgi_f = tk.Frame(liste_f, bg=KART, width=220)
        bilgi_f.pack(side="right", fill="y", padx=(10, 0))
        bilgi_f.pack_propagate(False)

        tk.Label(bilgi_f, text="Karakter Bilgisi", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", pady=(0, 4))

        self.bilgi_label = tk.Label(
            bilgi_f, text="Karakter seçin", bg=KART, fg=METIN_KOYU,
            font=("Segoe UI", 9), justify="left", anchor="nw")
        self.bilgi_label.pack(fill="both", expand=True, anchor="w")

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
        kisilik.kanon_sec(pid, yol)
        messagebox.showinfo("Tamam", "Canon güncellendi")
        self._listeyi_yenile()
        # Alt bardaki vesikalığı da tazele
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
        # Bilgi
        kanon = persona.get("kanon_gorsel")
        self.bilgi_label.config(
            text=f"Ad: {persona['ad']}\nYaş: {persona.get('yas', '?')}\n"
                 f"Niş: {persona.get('nis', '?')}\n"
                 f"Seed: {persona.get('seed', '?')}\n"
                 f"Kaynak: {persona.get('kaynak', 'ai')}\n"
                 f"Canon: {'Var' if kanon else 'Yok'}")
        self._bar_bildir(persona)

    def _bar_bildir(self, persona):
        if not self.on_karakter:
            return
        kanon = persona.get("kanon_gorsel")
        baslik = f"{persona['ad']}  ·  {persona.get('nis', '')}"
        alt = (f"Seed {persona.get('seed', '?')} · "
               f"{'Canon hazır' if kanon else 'Canon yüz yok'}")
        self.after(0, lambda: self.on_karakter(kanon, baslik, alt))
