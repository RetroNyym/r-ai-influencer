# -*- coding: utf-8 -*-
"""Araçlar sekmesi: trend fikirleri, marka kiti, fotoroman, toplu kuyruk."""

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from core import depolama, fotoroman, kisilik, marka, toplu, trend
from gui.palet import CIZGI, KART, METIN_KOYU, METIN_SOLUK, TEAL_KOYU, ZEMIN


class SekmeArac(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Govde.TFrame")
        self._kur()
        self._kuyruk_yenile()

    def _kur(self):
        paned = tk.PanedWindow(self, orient="horizontal", bg=ZEMIN,
                               sashwidth=6, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        # --- Sol: trend + fotoroman ---
        sol = tk.Frame(paned, bg=KART, highlightthickness=1,
                       highlightbackground=CIZGI)
        paned.add(sol, width=460)

        # Trend
        tk.Label(sol, text="Trend Konu Fikirleri", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(12, 2))
        f1 = tk.Frame(sol, bg=KART)
        f1.pack(fill="x", padx=14, pady=2)
        tk.Label(f1, text="Niş:", bg=KART, fg=METIN_KOYU, width=6,
                 anchor="w").pack(side="left")
        self.nis_girdi = ttk.Entry(f1, width=24)
        self.nis_girdi.insert(0, "lifestyle")
        self.nis_girdi.pack(side="left", padx=(0, 6))
        ttk.Button(f1, text="Fikir Üret", style="Yesil.TButton",
                   command=self._trend).pack(side="left")
        self.trend_liste = tk.Listbox(sol, height=8, font=("Segoe UI", 9),
                                      bg=ZEMIN, fg=METIN_KOYU, relief="flat")
        self.trend_liste.pack(fill="x", padx=14, pady=4)

        ttk.Separator(sol).pack(fill="x", padx=14, pady=6)

        # Fotoroman
        tk.Label(sol, text="Fotoroman (4-6 kare hikâye)", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(4, 2))
        f2 = tk.Frame(sol, bg=KART)
        f2.pack(fill="x", padx=14, pady=2)
        tk.Label(f2, text="Persona:", bg=KART, fg=METIN_KOYU, width=6,
                 anchor="w").pack(side="left")
        self.persona_cb = ttk.Combobox(f2, state="readonly", width=22)
        self.persona_cb.pack(side="left")
        f3 = tk.Frame(sol, bg=KART)
        f3.pack(fill="x", padx=14, pady=2)
        tk.Label(f3, text="Konu:", bg=KART, fg=METIN_KOYU, width=6,
                 anchor="w").pack(side="left")
        self.konu_girdi = ttk.Entry(f3, width=36)
        self.konu_girdi.insert(0, "kahve molasi")
        self.konu_girdi.pack(side="left")
        f4 = tk.Frame(sol, bg=KART)
        f4.pack(fill="x", padx=14, pady=4)
        tk.Label(f4, text="Kare:", bg=KART, fg=METIN_KOYU, width=6,
                 anchor="w").pack(side="left")
        self.kare_spin = ttk.Spinbox(f4, from_=4, to=6, width=4)
        self.kare_spin.set(5)
        self.kare_spin.pack(side="left", padx=(0, 8))
        ttk.Button(f4, text="Fotoroman Üret", style="Yesil.TButton",
                   command=self._fotoroman).pack(side="left")
        self.foto_durum = tk.Label(sol, text="", bg=KART, fg=METIN_SOLUK,
                                   font=("Segoe UI", 9), anchor="w")
        self.foto_durum.pack(fill="x", padx=14)

        # --- Orta: marka kiti ---
        orta = tk.Frame(paned, bg=KART, highlightthickness=1,
                        highlightbackground=CIZGI)
        paned.add(orta, width=320)
        tk.Label(orta, text="Marka Kiti", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(12, 2))
        tk.Label(orta, text="1:1 profil görseli + biyografi + kapak önerisi",
                 bg=KART, fg=METIN_SOLUK, font=("Segoe UI", 9),
                 wraplength=280, justify="left").pack(anchor="w", padx=14)
        ttk.Button(orta, text="Marka Kiti Üret", style="Yesil.TButton",
                   command=self._marka).pack(fill="x", padx=14, pady=10)
        self.marka_text = tk.Text(orta, height=18, font=("Segoe UI", 9),
                                  bg=ZEMIN, fg=METIN_KOYU, relief="flat")
        self.marka_text.pack(fill="both", expand=True, padx=14, pady=4)

        # --- Sağ: toplu kuyruk ---
        sag = tk.Frame(paned, bg=KART, highlightthickness=1,
                       highlightbackground=CIZGI)
        paned.add(sag, width=360)
        tk.Label(sag, text="Toplu Üretim Kuyruğu", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(12, 2))

        f5 = tk.Frame(sag, bg=KART)
        f5.pack(fill="x", padx=14, pady=4)
        tk.Label(f5, text="Sahne:", bg=KART, fg=METIN_KOYU, width=6,
                 anchor="w").pack(side="left")
        self.toplu_sahne = ttk.Entry(f5, width=30)
        self.toplu_sahne.insert(0, "sokak kahvesi")
        self.toplu_sahne.pack(side="left")
        f6 = tk.Frame(sag, bg=KART)
        f6.pack(fill="x", padx=14, pady=2)
        tk.Label(f6, text="Adet:", bg=KART, fg=METIN_KOYU, width=6,
                 anchor="w").pack(side="left")
        self.toplu_sayi = ttk.Spinbox(f6, from_=1, to=20, width=4)
        self.toplu_sayi.set(3)
        self.toplu_sayi.pack(side="left", padx=(0, 8))
        ttk.Button(f6, text="Kuyruğa Ekle", style="Teal.TButton",
                   command=self._toplu_ekle).pack(side="left")

        btn7 = tk.Frame(sag, bg=KART)
        btn7.pack(fill="x", padx=14, pady=6)
        ttk.Button(btn7, text="Çalıştır", style="Yesil.TButton",
                   command=self._toplu_calistir).pack(side="left", padx=(0, 4))
        ttk.Button(btn7, text="Duraklat", style="Kart.TButton",
                   command=self._toplu_duraklat).pack(side="left", padx=(0, 4))
        ttk.Button(btn7, text="Temizle", style="Kart.TButton",
                   command=self._toplu_temizle).pack(side="left")

        self.toplu_durum_lbl = tk.Label(sag, text="Durum: bekliyor",
                                        bg=KART, fg=METIN_SOLUK,
                                        font=("Segoe UI", 9), anchor="w")
        self.toplu_durum_lbl.pack(fill="x", padx=14)

        self.kuyruk_tree = ttk.Treeview(
            sag, columns=("id", "tip", "durum"), show="headings", height=12)
        for c, t, w in [("id", "ID", 40), ("tip", "Tip", 80), ("durum", "Durum", 100)]:
            self.kuyruk_tree.heading(c, text=t)
            self.kuyruk_tree.column(c, width=w)
        self.kuyruk_tree.pack(fill="both", expand=True, padx=14, pady=4)

        self._personalar()

    def _personalar(self):
        ps = kisilik.persona_listele()
        self.persona_cb["values"] = [f"{p['id']} — {p['ad']}" for p in ps]
        if ps:
            self.persona_cb.current(0)

    def _secili_persona(self):
        s = self.persona_cb.get()
        if not s:
            return None
        return int(s.split("—")[0].strip())

    # --- Trend ---
    def _trend(self):
        nis = self.nis_girdi.get().strip() or "lifestyle"
        self.trend_liste.delete(0, "end")
        self.trend_liste.insert("end", "Üretiliyor...")
        threading.Thread(target=self._trend_worker, args=(nis,),
                         daemon=True).start()

    def _trend_worker(self, nis):
        try:
            fikirler = trend.trend_fikirleri(nis, sayi=10)
            def goster():
                self.trend_liste.delete(0, "end")
                for f in fikirler:
                    self.trend_liste.insert(
                        "end", f"[{f.get('platform', '?')}] {f['baslik'][:70]}")
            self.after(0, goster)
        except Exception as e:
            self.after(0, lambda: self.trend_liste.insert("end", f"Hata: {e}"))

    # --- Fotoroman ---
    def _fotoroman(self):
        pid = self._secili_persona()
        konu = self.konu_girdi.get().strip()
        if not pid or not konu:
            messagebox.showwarning("Eksik", "Persona ve konu seçin")
            return
        try:
            kare = int(self.kare_spin.get())
        except ValueError:
            kare = 5
        self.foto_durum.config(text="Üretiliyor...")
        threading.Thread(target=self._fotoroman_worker, args=(pid, konu, kare),
                         daemon=True).start()

    def _fotoroman_worker(self, pid, konu, kare):
        try:
            def cb(i, n, msg):
                self.after(0, lambda: self.foto_durum.config(text=msg))
            posts = fotoroman.fotoroman_uret(pid, konu, kare, ilerleme_cb=cb)
            self.after(0, lambda: self.foto_durum.config(
                text=f"Tamam: {len(posts)} kare → Onay kuyruğunda"))
        except Exception as e:
            self.after(0, lambda: self.foto_durum.config(text=f"Hata: {e}"))

    # --- Marka ---
    def _marka(self):
        pid = self._secili_persona()
        if not pid:
            messagebox.showwarning("Seçim", "Persona seçin")
            return
        self.marka_text.delete("1.0", "end")
        self.marka_text.insert("end", "Üretiliyor (Pollinations)...")
        threading.Thread(target=self._marka_worker, args=(pid,),
                         daemon=True).start()

    def _marka_worker(self, pid):
        try:
            r = marka.marka_kiti_uret(pid)
            def goster():
                self.marka_text.delete("1.0", "end")
                self.marka_text.insert("end",
                    f"Biyografi:\n{r['biyografi']}\n\n"
                    f"Kapak:\n{r['kapak']}\n\nKlasör: {r['klasor']}")
            self.after(0, goster)
        except Exception as e:
            self.after(0, lambda: self.marka_text.insert("end", f"\nHata: {e}"))

    # --- Toplu ---
    def _toplu_ekle(self):
        pid = self._secili_persona()
        sahne = self.toplu_sahne.get().strip()
        if not pid or not sahne:
            messagebox.showwarning("Eksik", "Persona ve sahne girin")
            return
        try:
            sayi = int(self.toplu_sayi.get())
        except ValueError:
            sayi = 1
        toplu.kuyruga_post_ekle(pid, sahne, sayi)
        self._kuyruk_yenile()

    def _toplu_calistir(self):
        if not toplu.calistir(ilerleme_cb=lambda *a: self.after(0, self._kuyruk_yenile)):
            messagebox.showinfo("Bilgi", "Kuyruk zaten çalışıyor")
        self.after(500, self._kuyruk_yenile)
        self._kuyruk_durum()

    def _toplu_duraklat(self):
        toplu.duraklat()
        self._kuyruk_durum()

    def _toplu_temizle(self):
        toplu.kuyruga_temizle()
        self._kuyruk_yenile()

    def _kuyruk_yenile(self):
        for i in self.kuyruk_tree.get_children():
            self.kuyruk_tree.delete(i)
        for k in toplu.kuyruga_listele():
            self.kuyruk_tree.insert("", "end", iid=str(k["id"]),
                                    values=(k["id"], k["tip"], k["durum"]))
        self._kuyruk_durum()

    def _kuyruk_durum(self):
        d = toplu.durum()
        etkin = "ÇALIŞIYOR" if d["calisiyor"] else "Bekliyor"
        self.toplu_durum_lbl.config(
            text=f"Durum: {etkin} · bekleyen {d['bekliyor']} · {d.get('son_mesaj', '')}")
        if d["calisiyor"]:
            self.after(1500, self._kuyruk_yenile)
