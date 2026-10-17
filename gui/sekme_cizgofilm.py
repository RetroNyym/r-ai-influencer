# -*- coding: utf-8 -*-
"""Çizgi Film / Animasyon sekmesi: senaryo tabanlı kısa shorts üretimi.

Kullanıcı sadece bir KONU yazar; program senaryoyu, görselleri,
seslendirmeyi ve dikey short videonun kendisi hazırlar.
"""

import json
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from core import animasyon, kisilik
from gui.palet import (CIZGI, KART, METIN_KOYU, METIN_SOLUK, TEAL_KOYU,
                       TEAL_VURGU, ZEMIN)

STILLER = [("Pixar 3D", "pixar"), ("Anime", "anime"),
           ("2D Cartoon", "cartoon"), ("Watercolor", "watercolor"),
           ("Comic", "comic")]


class SekmeCizgiFilm(ttk.Frame):
    def __init__(self, parent, on_karakter=None):
        super().__init__(parent, style="Govde.TFrame")
        self.on_karakter = on_karakter
        self._sonuc = None
        self._pid_map = {}
        self._kur()
        self._karakterleri_yukle()

    def _kur(self):
        paned = tk.PanedWindow(self, orient="horizontal", bg=ZEMIN,
                               sashwidth=6, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        # --- Sol: konu + ayarlar ---
        sol = tk.Frame(paned, bg=KART, highlightthickness=1,
                       highlightbackground=CIZGI)
        paned.add(sol, width=400)

        tk.Label(sol, text="Çizgi Film Shorts", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=18, pady=(18, 4))
        tk.Label(sol,
                 text="Sadece bir konu yazın. Program senaryoyu,\n"
                      "görselleri ve seslendirmeyi kendisi hazırlar;\n"
                      "9:16 dikey kısa bir short çıkarır. Kimlik kilidi\n"
                      "varsa her bölümde aynı kişi görünür.",
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

        # Bölüm sayısı
        f3 = ttk.Frame(sol, style="Kart.TFrame")
        f3.pack(fill="x", padx=16, pady=2)
        ttk.Label(f3, text="Bölüm", style="Kart.TLabel", width=10,
                  anchor="w").pack(side="left")
        self.bolum_sb = ttk.Spinbox(f3, from_=3, to=6, width=6)
        self.bolum_sb.set(4)
        self.bolum_sb.pack(side="left")

        # Konu
        ttk.Label(sol, text="Konu", style="Kart.TLabel",
                  font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(10, 2))
        self.konu = tk.Text(sol, height=3, width=44, font=("Segoe UI", 10))
        self.konu.pack(fill="x", padx=16)
        self.konu.insert("1.0", "kahve demlemenin püf noktaları")

        # Seçenekler
        self.ses_var = tk.BooleanVar(value=True)
        self.alt_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(sol, text="Seslendir (Türkçe)",
                        variable=self.ses_var).pack(anchor="w", padx=16, pady=2)
        ttk.Checkbutton(sol, text="Altyazı göster",
                        variable=self.alt_var).pack(anchor="w", padx=16)

        btnler = ttk.Frame(sol, style="Kart.TFrame")
        btnler.pack(fill="x", padx=16, pady=(6, 2))
        ttk.Button(btnler, text="Senaryo Önizle", style="Kart.TButton",
                   command=self._onizle).pack(side="left", expand=True, fill="x", padx=(0, 4))
        ttk.Button(btnler, text="Short Üret", style="Yesil.TButton",
                   command=self._uret).pack(side="left", expand=True, fill="x")

        self.durum = ttk.Label(sol, text="", style="Kart.TLabel",
                               wraplength=360, justify="left")
        self.durum.pack(anchor="w", padx=16, pady=(4, 10))

        # --- Sağ: senaryo + önizleme ---
        sag = tk.Frame(paned, bg=KART, highlightthickness=1,
                       highlightbackground=CIZGI)
        paned.add(sag, width=620)

        tk.Label(sag, text="Senaryo", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(12, 2))

        self.senaryo_txt = tk.Text(sag, height=8, width=60, font=("Segoe UI", 9),
                                   state="disabled", bg="#F7FAFA")
        self.senaryo_txt.pack(fill="x", padx=12, pady=4)

        tk.Label(sag, text="Kareler", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=12, pady=(8, 2))
        self.kare_frame = tk.Frame(sag, bg=KART)
        self.kare_frame.pack(fill="x", padx=12, pady=4)

        self.video_label = tk.Label(sag, text="Video burada oluşacak",
                                    bg=KART, fg=METIN_SOLUK,
                                    font=("Segoe UI", 11), justify="left")
        self.video_label.pack(fill="both", expand=True, padx=12, pady=8)

    # ------------------------------------------------------------------
    def _karakterleri_yukle(self):
        personalar = kisilik.persona_listele()
        self._pid_map = {p["ad"]: p["id"] for p in personalar}
        self.karakter_cb["values"] = list(self._pid_map.keys())
        if personalar:
            self.karakter_cb.current(0)

    def _secim(self):
        secili = self.karakter_cb.get()
        if not secili or secili not in self._pid_map:
            messagebox.showwarning("Seçim", "Bir karakter seçin")
            return None
        pid = self._pid_map[secili]
        konu = self.konu.get("1.0", "end").strip()
        if not konu:
            messagebox.showwarning("Eksik", "Bir konu yazın")
            return None
        try:
            sayi = int(self.bolum_sb.get())
        except ValueError:
            sayi = 4
        stil = STILLER[self.stil_cb.current()][1]
        return pid, konu, sayi, stil

    def _onizle(self):
        secim = self._secim()
        if not secim:
            return
        pid, konu, sayi, _ = secim
        self.durum.config(text="Senaryo yazılıyor...")
        threading.Thread(target=self._onizle_worker,
                         args=(pid, konu, sayi), daemon=True).start()

    def _onizle_worker(self, pid, konu, sayi):
        try:
            persona = kisilik.persona_al(pid)
            senaryo = animasyon.senaryo_uret(
                konu, sayi=sayi, karakter=persona.get("ad", "Karakter"))
            self.after(0, lambda: self._senaryo_goster(senaryo))
            self.after(0, lambda: self.durum.config(text="Senaryo hazır"))
        except Exception as e:
            self.after(0, lambda: self.durum.config(
                text=f"Senaryo hatası: {e}", fg="#C62828"))

    def _senaryo_goster(self, senaryo):
        self.senaryo_txt.config(state="normal")
        self.senaryo_txt.delete("1.0", "end")
        for b in senaryo:
            self.senaryo_txt.insert(
                "end", f"{b['no']}. {b['replik_tr']}\n"
                       f"   ↳ {b['sahne_en']}\n\n")
        self.senaryo_txt.config(state="disabled")

    def _uret(self):
        secim = self._secim()
        if not secim:
            return
        pid, konu, sayi, stil = secim
        self.durum.config(text="Üretiliyor... (senaryo + görseller + ses + video)")
        threading.Thread(target=self._worker,
                         args=(pid, konu, sayi, stil), daemon=True).start()

    def _worker(self, pid, konu, sayi, stil):
        try:
            sonuc = animasyon.short_yap(
                pid, konu, sayi=sayi, stil=stil,
                ses_acik=self.ses_var.get(), altyazi=self.alt_var.get(),
                ilerleme_cb=lambda a, b, m: self.after(
                    0, lambda: self.durum.config(text=m)))
            self.after(0, lambda: self._bitti(sonuc))
        except Exception as e:
            self.after(0, lambda: self._hata(str(e)))

    def _bitti(self, sonuc):
        self._sonuc = sonuc
        self._senaryo_goster(sonuc.get("senaryo", []))
        kareler = sonuc.get("kareler", [])
        v = sonuc.get("video", {})
        self.durum.config(
            text=f"Tamamlandı: {len(kareler)} bölüm · "
                 f"{v.get('sureSn', '?')}sn · {v.get('boyut_mb', '?')}MB")

        for w in self.kare_frame.winfo_children():
            w.destroy()
        try:
            from PIL import Image, ImageTk
            for kp in kareler:
                img = Image.open(kp)
                img.thumbnail((80, 142), Image.LANCZOS)
                foto = ImageTk.PhotoImage(img)
                lbl = tk.Label(self.kare_frame, image=foto, bg=KART)
                lbl.image = foto
                lbl.pack(side="left", padx=2)
        except Exception:
            pass

        yol = v.get("cikti", "")
        if yol:
            self.video_label.config(
                text=f"Short hazır:\n{yol}\n\n"
                     f"Senaryo JSON: {Path(sonuc.get('klasor',''))/'senaryo.json'}\n"
                     f"(Dosya yöneticisinden oynatabilirsiniz.)",
                fg=TEAL_VURGU)

    def _hata(self, hata):
        self.durum.config(text=f"Hata: {hata}", fg="#C62828")
