# -*- coding: utf-8 -*-
"""Üretim & Onay sekmesi: toplu üretim, onay kuyruğu, önizleme."""

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from core import depolama, kisilik

ZEMIN = "#F0F6F5"
KART = "#FFFFFF"
YESIL_ACIK = "#E0F5F0"
TEAL_KOYU = "#0D4F5C"
TEAL_VURGU = "#2BB8A0"


class SekmeUretim(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Govde.TFrame")
        self._kur()

    def _kur(self):
        paned = tk.PanedWindow(self, orient="horizontal", bg=ZEMIN,
                               sashwidth=6, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        # --- Sol: üretim kontrolü ---
        sol = ttk.Frame(paned, style="Kart.TFrame")
        paned.add(sol, width=320)

        ttk.Label(sol, text="İçerik Üret", style="Vurgu.TLabel",
                  font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(16, 8))

        # Persona seçimi
        f1 = ttk.Frame(sol, style="Kart.TFrame")
        f1.pack(fill="x", padx=16, pady=4)
        ttk.Label(f1, text="Karakter:", style="Kart.TLabel", width=10,
                  anchor="w").pack(side="left")
        self.persona_cb = ttk.Combobox(f1, state="readonly", width=20)
        self.persona_cb.pack(side="left", fill="x", expand=True)

        # Sahne sayısı
        f2 = ttk.Frame(sol, style="Kart.TFrame")
        f2.pack(fill="x", padx=16, pady=4)
        ttk.Label(f2, text="Sahne sayısı:", style="Kart.TLabel", width=10,
                  anchor="w").pack(side="left")
        self.sahne_spin = ttk.Spinbox(f2, from_=1, to=10, width=5)
        self.sahne_spin.set(3)
        self.sahne_spin.pack(side="left")

        self.ilerleme = ttk.Progressbar(sol, mode="determinate", length=280)
        self.ilerleme.pack(fill="x", padx=16, pady=12)
        self.ilerleme_deger = tk.StringVar(value="Hazır")
        ttk.Label(sol, textvariable=self.ilerleme_deger,
                  style="Kart.TLabel").pack(anchor="w", padx=16)

        ttk.Button(sol, text="Üretimi Başlat", style="Yesil.TButton",
                   command=self._baslat).pack(fill="x", padx=16, pady=(8, 4))
        ttk.Button(sol, text="Listeyi Yenile", style="Kart.TButton",
                   command=self._yukle).pack(fill="x", padx=16, pady=2)

        ttk.Separator(sol).pack(fill="x", padx=16, pady=8)
        ttk.Label(sol,
                  text="Ücretsiz API: Pollinations.ai\n"
                       "Her sahne ~5sn sürer (rate limit).",
                  style="Kart.TLabel", justify="left").pack(anchor="w", padx=16)

        # --- Sağ: onay kuyruğu ---
        sag = ttk.Frame(paned, style="Kart.TFrame")
        paned.add(sag, width=700)

        ust = ttk.Frame(sag, style="Kart.TFrame")
        ust.pack(fill="x", padx=12, pady=(12, 4))
        ttk.Label(ust, text="Onay Kuyruğu", style="Vurgu.TLabel",
                  font=("Segoe UI", 12, "bold")).pack(side="left")

        # Filtre
        self.filtre = tk.StringVar(value="onay_bekliyor")
        for text, val in [("Bekleyen", "onay_bekliyor"), ("Onaylı", "onayli"),
                          ("Paylaşılan", "paylasildi"), ("Tümü", "")]:
            ttk.Radiobutton(ust, text=text, value=val, variable=self.filtre,
                            command=self._yukle).pack(side="left", padx=4)

        self.tree = ttk.Treeview(sag, columns=("id", "sahne", "durum"),
                                 show="headings", height=12)
        self.tree.heading("id", text="ID")
        self.tree.heading("sahne", text="Sahne")
        self.tree.heading("durum", text="Durum")
        self.tree.column("id", width=50)
        self.tree.column("sahne", width=450)
        self.tree.column("durum", width=100)
        self.tree.pack(fill="both", expand=True, padx=12, pady=4)
        self.tree.bind("<<TreeviewSelect>>", self._onizleme)

        # Onay butonları
        btnler = ttk.Frame(sag, style="Kart.TFrame")
        btnler.pack(fill="x", padx=12, pady=(4, 12))
        ttk.Button(btnler, text="Onayla", style="Yesil.TButton",
                   command=lambda: self._durum_degistir("onayli")).pack(side="left", padx=2)
        ttk.Button(btnler, text="Reddet", style="Kart.TButton",
                   command=lambda: self._durum_degistir("reddedildi")).pack(side="left", padx=2)
        ttk.Button(btnler, text="Panoya Caption Kopyala", style="Kart.TButton",
                   command=self._panoya_kopyala).pack(side="left", padx=2)
        ttk.Button(btnler, text="Klasörde Aç", style="Kart.TButton",
                   command=self._klasorde_ac).pack(side="left", padx=2)

        # Önizleme
        self.onizleme_frame = ttk.Frame(sag, style="Kart.TFrame")
        self.onizleme_frame.pack(fill="x", padx=12, pady=(0, 12))
        self.onizleme_label = ttk.Label(self.onizleme_frame,
                                        text="Seçili postu önizlemek için tıklayın",
                                        style="Kart.TLabel")
        self.onizleme_label.pack(anchor="w")

        self._persona_yukle()
        self._yukle()

    def _persona_yukle(self):
        kisiler = kisilik.persona_listele()
        degerler = [f"{p['id']} — {p['ad']}" for p in kisiler]
        self.persona_cb["values"] = degerler
        if degerler:
            self.persona_cb.current(0)

    def _baslat(self):
        secim = self.persona_cb.get()
        if not secim:
            messagebox.showwarning("Seçim", "Karakter seçin")
            return
        pid = int(secim.split("—")[0].strip())
        try:
            sayi = int(self.sahne_spin.get())
        except ValueError:
            sayi = 3

        self.ilerleme["maximum"] = sayi
        self.ilerleme["value"] = 0
        threading.Thread(target=self._uretim_worker, args=(pid, sayi),
                         daemon=True).start()

    def _uretim_worker(self, pid, sayi):
        from core import uretim
        try:
            def cb(i, toplam, mesaj):
                self.after(0, lambda: self._ilerleme_guncelle(i, toplam, mesaj))
            posts = uretim.toplu_uret(pid, sayi, ilerleme_cb=cb)
            self.after(0, lambda: self._uretim_bitti(posts))
        except Exception as e:
            self.after(0, lambda: self._uretim_hata(str(e)))

    def _ilerleme_guncelle(self, i, toplam, mesaj):
        self.ilerleme["maximum"] = toplam
        self.ilerleme["value"] = i
        self.ilerleme_deger.set(mesaj)

    def _uretim_bitti(self, posts):
        self.ilerleme_deger.set(f"Tamamlandı: {len(posts)} post")
        self._yukle()

    def _uretim_hata(self, hata):
        self.ilerleme_deger.set(f"Hata: {hata}")
        messagebox.showerror("Üretim Hatası", hata)

    def _yukle(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        durum = self.filtre.get()
        for p in depolama.post_listele(durum or None):
            self.tree.insert("", "end", iid=str(p["id"]),
                             values=(p["id"], (p["sahne"] or "")[:80], p["durum"]))

    def _secili_id(self):
        sec = self.tree.selection()
        return int(sec[0]) if sec else None

    def _durum_degistir(self, durum):
        pid = self._secili_id()
        if not pid:
            return
        depolama.post_durum(pid, durum)
        self._yukle()

    def _onizleme(self, event):
        pid = self._secili_id()
        if not pid:
            return
        post = depolama.post_al(pid)
        if not post or not post.get("gorsel_yol"):
            return
        try:
            from PIL import Image, ImageTk
            img = Image.open(post["gorsel_yol"])
            img.thumbnail((200, 260))
            self._foto = ImageTk.PhotoImage(img)
            self.onizleme_label.configure(image=self._foto, text="")
        except Exception:
            self.onizleme_label.configure(
                text=f"Görsel: {post['gorsel_yol']}\nCaption: {post.get('caption', '')[:120]}")

    def _panoya_kopyala(self):
        pid = self._secili_id()
        if not pid:
            return
        post = depolama.post_al(pid)
        metin = f"{post.get('caption', '')}\n\n{post.get('hashtags', '')}"
        self.clipboard_clear()
        self.clipboard_append(metin)
        messagebox.showinfo("Tamam", "Caption panoya kopyalandı")

    def _klasorde_ac(self):
        pid = self._secili_id()
        if not pid:
            return
        post = depolama.post_al(pid)
        import os
        if post and post.get("gorsel_yol"):
            os.startfile(os.path.dirname(post["gorsel_yol"]))
