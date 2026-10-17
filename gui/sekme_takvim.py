# -*- coding: utf-8 -*-
"""Takvim sekmesi: gün/saat planlama, zamanlayıcı başlat/durdur."""

import tkinter as tk
from tkinter import messagebox, ttk

from core import depolama, zamanlayici
from gui.palet import CIZGI, KART, TEAL_KOYU, TEAL_VURGU, ZEMIN

GUNLER = ["Pazartesi", "Salı", "Çarşamba", "Perşembe",
          "Cuma", "Cumartesi", "Pazar"]


class SekmeTakvim(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Govde.TFrame")
        self._kur()
        self._yukle()

    def _kur(self):
        sol = tk.Frame(self, bg=KART, highlightthickness=1,
                       highlightbackground=CIZGI)
        sol.pack(side="left", fill="y", padx=8, pady=8)

        ttk.Label(sol, text="Paylaşım Takvimi", style="Vurgu.TLabel",
                  font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(16, 8))

        # Gün seçimi
        f1 = ttk.Frame(sol, style="Kart.TFrame")
        f1.pack(fill="x", padx=16, pady=4)
        ttk.Label(f1, text="Gün:", style="Kart.TLabel", width=8,
                  anchor="w").pack(side="left")
        self.gun_cb = ttk.Combobox(f1, values=GUNLER, state="readonly", width=14)
        self.gun_cb.current(0)
        self.gun_cb.pack(side="left")

        # Saat
        f2 = ttk.Frame(sol, style="Kart.TFrame")
        f2.pack(fill="x", padx=16, pady=4)
        ttk.Label(f2, text="Saat:", style="Kart.TLabel", width=8,
                  anchor="w").pack(side="left")
        self.saat_cb = ttk.Combobox(
            f2, values=[f"{h:02d}:00" for h in range(24)] +
                       [f"{h:02d}:30" for h in range(24)],
            state="readonly", width=6)
        self.saat_cb.set("19:00")
        self.saat_cb.pack(side="left")

        ttk.Button(sol, text="Ekle", style="Yesil.TButton",
                   command=self._ekle).pack(fill="x", padx=16, pady=8)

        ttk.Separator(sol).pack(fill="x", padx=16, pady=4)
        ttk.Label(sol, text="Zamanlayıcı", style="Vurgu.TLabel",
                  font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=16, pady=(8, 4))

        self.zaman_durum = tk.StringVar(value="Durduruldu")
        ttk.Label(sol, textvariable=self.zaman_durum,
                  style="Kart.TLabel").pack(anchor="w", padx=16)

        btn_z = ttk.Frame(sol, style="Kart.TFrame")
        btn_z.pack(fill="x", padx=16, pady=8)
        ttk.Button(btn_z, text="Başlat", style="Yesil.TButton",
                   command=self._zaman_baslat).pack(side="left", padx=(0, 6))
        ttk.Button(btn_z, text="Durdur", style="Kart.TButton",
                   command=self._zaman_durdur).pack(side="left")

        ttk.Label(sol,
                  text="Not: Zamanlayıcı çalışırken uygulama\n"
                       "açık olmalıdır. Onaylı postlar saati\n"
                       "gelince otomatik paylaşılır.",
                  style="Kart.TLabel", justify="left").pack(anchor="w", padx=16, pady=8)

        # --- Sağ: liste + log ---
        sag = tk.Frame(self, bg=KART, highlightthickness=1,
                       highlightbackground=CIZGI)
        sag.pack(side="left", fill="both", expand=True, padx=8, pady=8)

        ttk.Label(sag, text="Zamanlanmış Saatler", style="Vurgu.TLabel",
                  font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(12, 4))

        self.tree = ttk.Treeview(sag, columns=("gun", "saat", "aktif"),
                                 show="headings", height=8)
        self.tree.heading("gun", text="Gün")
        self.tree.heading("saat", text="Saat")
        self.tree.heading("aktif", text="Aktif")
        self.tree.column("gun", width=140)
        self.tree.column("saat", width=80)
        self.tree.column("aktif", width=60)
        self.tree.pack(fill="x", padx=12, pady=4)

        ttk.Button(sag, text="Seçileni Sil", style="Kart.TButton",
                   command=self._sil).pack(anchor="w", padx=12, pady=4)

        ttk.Separator(sag).pack(fill="x", padx=12, pady=8)
        ttk.Label(sag, text="Paylaşım Geçmişi", style="Vurgu.TLabel",
                  font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=12, pady=(4, 4))

        self.log_tree = ttk.Treeview(
            sag, columns=("platform", "basarili", "mesaj", "zaman"),
            show="headings", height=8)
        self.log_tree.heading("platform", text="Platform")
        self.log_tree.heading("basarili", text="Durum")
        self.log_tree.heading("mesaj", text="Mesaj")
        self.log_tree.heading("zaman", text="Zaman")
        self.log_tree.column("platform", width=90)
        self.log_tree.column("basarili", width=60)
        self.log_tree.column("mesaj", width=300)
        self.log_tree.column("zaman", width=130)
        self.log_tree.pack(fill="both", expand=True, padx=12, pady=(4, 12))

    def _ekle(self):
        gun = self.gun_cb.current()
        saat = self.saat_cb.get()
        depolama.schedule_ekle(gun, saat)
        self._yukle()

    def _sil(self):
        sec = self.tree.selection()
        if not sec:
            return
        sid = int(sec[0])
        depolama.schedule_sil(sid)
        self._yukle()

    def _yukle(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for s in depolama.schedule_listele():
            gun_adi = GUNLER[s["gun"]] if 0 <= s["gun"] < 7 else str(s["gun"])
            self.tree.insert("", "end", iid=str(s["id"]),
                             values=(gun_adi, s["saat"], "Evet" if s["aktif"] else "Hayır"))

        for i in self.log_tree.get_children():
            self.log_tree.delete(i)
        import time
        for lg in depolama.log_listele(30):
            self.log_tree.insert("", "end", values=(
                lg["platform"], "✓" if lg["basarili"] else "✗",
                (lg["mesaj"] or "")[:60],
                time.strftime("%d.%m %H:%M", time.localtime(lg["zamani"]))))

    def _zaman_baslat(self):
        zamanlayici.baslat()
        self.zaman_durum.set("Çalışıyor ✓")
        messagebox.showinfo("Zamanlayıcı", "Zamanlayıcı başlatıldı")

    def _zaman_durdur(self):
        zamanlayici.durdur()
        self.zaman_durum.set("Durduruldu")
