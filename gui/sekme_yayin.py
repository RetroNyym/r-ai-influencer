# -*- coding: utf-8 -*-
"""Yayın & Analiz sekmesi: caption skoru, yayın paketi, performans günlüğü."""

import tkinter as tk
from tkinter import messagebox, ttk

from core import depolama, skorlama, yayin_paketi
from gui.palet import CIZGI, KART, METIN_KOYU, METIN_SOLUK, TEAL_KOYU, ZEMIN


class SekmeYayin(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Govde.TFrame")
        self._kur()
        self._yukle()

    def _kur(self):
        paned = tk.PanedWindow(self, orient="horizontal", bg=ZEMIN,
                               sashwidth=6, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        # Sol: post listesi
        sol = tk.Frame(paned, bg=KART, highlightthickness=1,
                       highlightbackground=CIZGI)
        paned.add(sol, width=300)
        tk.Label(sol, text="Paylaşım Kuyruğu", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(12, 4))
        self.tree = ttk.Treeview(sol, columns=("id", "sahne", "durum"),
                                 show="headings", height=14)
        for c, t, w in [("id", "ID", 40), ("sahne", "Sahne", 170), ("durum", "Durum", 70)]:
            self.tree.heading(c, text=t)
            self.tree.column(c, width=w)
        self.tree.pack(fill="both", expand=True, padx=12, pady=4)
        self.tree.bind("<<TreeviewSelect>>", self._secim)
        ttk.Button(sol, text="Yenile", style="Kart.TButton",
                   command=self._yukle).pack(fill="x", padx=12, pady=4)

        # Orta: skor + paket
        orta = tk.Frame(paned, bg=KART, highlightthickness=1,
                        highlightbackground=CIZGI)
        paned.add(orta, width=420)
        tk.Label(orta, text="Caption Skoru & Yayın Paketi", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(12, 4))

        self.skor_etiket = tk.Label(orta, text="Post seçin", bg=KART,
                                    fg=METIN_KOYU, font=("Segoe UI", 22, "bold"))
        self.skor_etiket.pack(pady=(4, 0))
        self.skor_detay = tk.Label(orta, text="", bg=KART, fg=METIN_SOLUK,
                                   font=("Segoe UI", 9), justify="left", anchor="w")
        self.skor_detay.pack(fill="x", padx=16, anchor="w")

        btn_f = tk.Frame(orta, bg=KART)
        btn_f.pack(fill="x", padx=16, pady=10)
        ttk.Button(btn_f, text="Puanla", style="Kart.TButton",
                   command=self._puanla).pack(side="left", padx=(0, 6))
        ttk.Button(btn_f, text="Yayın Paketi Üret", style="Yesil.TButton",
                   command=self._paket).pack(side="left")
        ttk.Button(btn_f, text="Paket Klasörünü Aç", style="Kart.TButton",
                   command=self._paket_klasor).pack(side="left", padx=(6, 0))

        tk.Label(orta, text="Çıktı (MD)", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16)
        self.md_text = tk.Text(orta, height=18, wrap="word", font=("Consolas", 9),
                               bg=ZEMIN, fg=METIN_KOYU, relief="flat")
        self.md_text.pack(fill="both", expand=True, padx=16, pady=4)

        # Sağ: performans
        sag = tk.Frame(paned, bg=KART, highlightthickness=1,
                       highlightbackground=CIZGI)
        paned.add(sag, width=340)
        tk.Label(sag, text="Performans Günlüğü", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=14, pady=(12, 4))

        f = tk.Frame(sag, bg=KART)
        f.pack(fill="x", padx=14, pady=4)
        tk.Label(f, text="Platform:", bg=KART, fg=METIN_KOYU, width=8,
                 anchor="w").pack(side="left")
        self.plat_cb = ttk.Combobox(f, values=["instagram", "tiktok"],
                                    state="readonly", width=14)
        self.plat_cb.current(0)
        self.plat_cb.pack(side="left")

        self.alanlar = {}
        for ad, etiket in [("goruntulenme", "Görüntülenme"),
                           ("begeni", "Beğeni"), ("yorum", "Yorum"),
                           ("paylasim", "Paylaşım")]:
            ff = tk.Frame(sag, bg=KART)
            ff.pack(fill="x", padx=14, pady=2)
            tk.Label(ff, text=etiket + ":", bg=KART, fg=METIN_KOYU, width=10,
                     anchor="w").pack(side="left")
            e = ttk.Entry(ff, width=12)
            e.pack(side="left")
            self.alanlar[ad] = e

        ttk.Button(sag, text="Performans Ekle", style="Yesil.TButton",
                   command=self._perf_ekle).pack(fill="x", padx=14, pady=8)

        self.istat_text = tk.Text(sag, height=14, font=("Segoe UI", 9),
                                  bg=ZEMIN, fg=METIN_KOYU, relief="flat")
        self.istat_text.pack(fill="both", expand=True, padx=14, pady=4)
        self._istat_yenile()

    def _yukle(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for p in depolama.post_listele():
            if p["durum"] in ("onayli", "paylasildi", "onay_bekliyor"):
                self.tree.insert("", "end", iid=str(p["id"]),
                                 values=(p["id"], (p["sahne"] or "")[:40], p["durum"]))

    def _secili_id(self):
        sec = self.tree.selection()
        return int(sec[0]) if sec else None

    def _secim(self, event=None):
        self._puanla()

    def _puanla(self):
        pid = self._secili_id()
        if not pid:
            return
        post = depolama.post_al(pid)
        metin = f"{post.get('caption', '')}\n{post.get('hashtags', '')}".strip()
        s = skorlama.caption_skoru(metin)
        self.skor_etiket.config(text=f"{s['puan']}/100")
        renk = "#20B89A" if s["puan"] >= 75 else ("#F0A830" if s["puan"] >= 50 else "#FF6B6B")
        self.skor_etiket.config(fg=renk)
        sat = [f"{s.get('degerlendirme', '')}"]
        for tip, m in s["maddeler"]:
            ikon = {"iyi": "✓", "orta": "~", "zayıf": "✗", "hata": "!"}.get(tip, "-")
            sat.append(f"{ikon} {m}")
        if s["oneriler"]:
            sat.append("—")
            sat += [f"→ {o}" for o in s["oneriler"]]
        self.skor_detay.config(text="\n".join(sat))

    def _paket(self):
        pid = self._secili_id()
        if not pid:
            messagebox.showwarning("Seçim", "Post seçin")
            return
        try:
            r = yayin_paketi.yayin_paketi_uret(pid, self.plat_cb.get())
            md_yol = r["klasor"] + "/YAYIN-PAKETI.md"
            with open(md_yol, "r", encoding="utf-8") as f:
                icerik = f.read()
            self.md_text.delete("1.0", "end")
            self.md_text.insert("1.0", icerik)
            messagebox.showinfo("Tamam", f"Yayın paketi hazır:\n{r['klasor']}")
        except Exception as e:
            messagebox.showerror("Hata", str(e))

    def _paket_klasor(self):
        pid = self._secili_id()
        if not pid:
            return
        import os
        klasor = depolama.URETILEN_KLASOR / "paket" / f"post_{pid}"
        klasor.mkdir(parents=True, exist_ok=True)
        os.startfile(str(klasor))

    def _perf_ekle(self):
        pid = self._secili_id()
        if not pid:
            messagebox.showwarning("Seçim", "Post seçin")
            return
        try:
            degerler = {k: int(e.get() or 0) for k, e in self.alanlar.items()}
        except ValueError:
            messagebox.showwarning("Hata", "Sayısal değer girin")
            return
        depolama.performans_ekle(pid, self.plat_cb.get(), **degerler)
        for e in self.alanlar.values():
            e.delete(0, "end")
        self._istat_yenile()
        messagebox.showinfo("Tamam", "Performans kaydedildi")

    def _istat_yenile(self):
        self.istat_text.delete("1.0", "end")
        try:
            ist = depolama.performans_istatistik()
        except Exception as e:
            self.istat_text.insert("end", f"Hata: {e}")
            return
        t = ist["toplam"]
        self.istat_text.insert("end",
            f"Toplam kayıt: {t['n']}\n"
            f"Görüntülenme: {t['g']:,}\nBeğeni: {t['b']:,}\n"
            f"Yorum: {t['y']:,}\nPaylaşım: {t['p']:,}\n\nEn iyi paylaşımlar:\n")
        for e in ist["en_iyi"]:
            cap = (e.get("caption") or "")[:40]
            self.istat_text.insert(
                "end", f"  {e.get('platform', '?')}: {e.get('goruntulenme', 0):,} — {cap}\n")
