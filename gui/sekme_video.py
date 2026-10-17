# -*- coding: utf-8 -*-
"""Video sekmesi: onaylı postlardan seslendirme + ffmpeg slayt video."""

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core import depolama, seslendirme, video as video_mod
from gui.palet import CIZGI, KART, METIN_KOYU, METIN_SOLUK, TEAL_KOYU, ZEMIN

SESLER = [("Türkçe — Ahmet", "tr-TR-AhmetNeural"),
          ("Türkçe — Emel", "tr-TR-EmelNeural"),
          ("English — Guy", "en-US-GuyNeural"),
          ("English — Aria", "en-US-AriaNeural"),
          ("Deutsch — Conrad", "de-DE-ConradNeural")]

ORANLAR = [("9:16 Shorts/Reels/TikTok", "9:16"),
           ("16:9 YouTube", "16:9"),
           ("1:1 IG Feed", "1:1")]


class SekmeVideo(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Govde.TFrame")
        self._sonuc = None
        self._kur()
        self._yukle()

    def _kur(self):
        paned = tk.PanedWindow(self, orient="horizontal", bg=ZEMIN,
                               sashwidth=6, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=8, pady=8)

        # Sol: post seçimi
        sol = tk.Frame(paned, bg=KART, highlightthickness=1,
                       highlightbackground=CIZGI)
        paned.add(sol, width=360)

        tk.Label(sol, text="Video Kur", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=16, pady=(16, 4))
        tk.Label(sol, text="Onaylı bir post seçin; seslendirilir ve MP4'e kurulur",
                 bg=KART, fg=METIN_SOLUK, font=("Segoe UI", 9),
                 wraplength=320, justify="left").pack(anchor="w", padx=16)

        self.tree = ttk.Treeview(sol, columns=("id", "sahne"),
                                 show="headings", height=10)
        self.tree.heading("id", text="ID")
        self.tree.heading("sahne", text="Sahne")
        self.tree.column("id", width=45)
        self.tree.column("sahne", width=240)
        self.tree.pack(fill="both", expand=True, padx=16, pady=8)

        ttk.Button(sol, text="Listeyi Yenile", style="Kart.TButton",
                   command=self._yukle).pack(fill="x", padx=16, pady=2)

        # Orta: ayarlar
        orta = tk.Frame(paned, bg=KART, highlightthickness=1,
                        highlightbackground=CIZGI)
        paned.add(orta, width=320)

        tk.Label(orta, text="Ayarlar", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(14, 4))

        f1 = tk.Frame(orta, bg=KART)
        f1.pack(fill="x", padx=16, pady=4)
        tk.Label(f1, text="Ses:", bg=KART, fg=METIN_KOYU, width=8,
                 anchor="w").pack(side="left")
        self.ses_cb = ttk.Combobox(f1, values=[s[0] for s in SESLER],
                                   state="readonly", width=22)
        self.ses_cb.current(0)
        self.ses_cb.pack(side="left")

        f2 = tk.Frame(orta, bg=KART)
        f2.pack(fill="x", padx=16, pady=4)
        tk.Label(f2, text="Oran:", bg=KART, fg=METIN_KOYU, width=8,
                 anchor="w").pack(side="left")
        self.oran_cb = ttk.Combobox(f2, values=[o[0] for o in ORANLAR],
                                    state="readonly", width=28)
        self.oran_cb.current(0)
        self.oran_cb.pack(side="left")

        f3 = tk.Frame(orta, bg=KART)
        f3.pack(fill="x", padx=16, pady=4)
        tk.Label(f3, text="Motor:", bg=KART, fg=METIN_KOYU, width=8,
                 anchor="w").pack(side="left")
        self.motor_cb = ttk.Combobox(
            f3, values=["Otomatik (edge→gtts)", "Edge (ücretsiz)", "gTTS"],
            state="readonly", width=22)
        self.motor_cb.current(0)
        self.motor_cb.pack(side="left")

        self.altyazi_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(orta, text="Altyazı göm (SRT yanar)",
                        variable=self.altyazi_var).pack(anchor="w", padx=16, pady=4)

        ttk.Button(orta, text="Ses Örneği Üret", style="Kart.TButton",
                   command=self._ses_ornek).pack(fill="x", padx=16, pady=4)
        ttk.Button(orta, text="Videoyu Kur", style="Yesil.TButton",
                   command=self._kur_video).pack(fill="x", padx=16, pady=(10, 4))
        ttk.Button(orta, text="Klasörde Aç", style="Kart.TButton",
                   command=self._klasorde_ac).pack(fill="x", padx=16, pady=2)

        self.durum = tk.StringVar(value="Hazır")
        tk.Label(orta, textvariable=self.durum, bg=KART, fg=METIN_SOLUK,
                 font=("Segoe UI", 9), wraplength=280, justify="left",
                 anchor="w").pack(fill="x", padx=16, pady=8)
        self.ilerleme = ttk.Progressbar(orta, mode="determinate")
        self.ilerleme.pack(fill="x", padx=16, pady=2)

        # Sağ: sonuçlar
        sag = tk.Frame(paned, bg=KART, highlightthickness=1,
                       highlightbackground=CIZGI)
        paned.add(sag, width=320)

        tk.Label(sag, text="Üretilen Videolar", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(14, 4))
        self.sonuc_liste = tk.Listbox(sag, font=("Segoe UI", 9), bg=ZEMIN,
                                      fg=METIN_KOYU, relief="flat")
        self.sonuc_liste.pack(fill="both", expand=True, padx=16, pady=8)
        self._sonuclari_tara()

    def _motor_secimi(self):
        i = self.motor_cb.current()
        return ["otomatik", "edge", "gtts"][i]

    def _ses_adi(self):
        return SESLER[self.ses_cb.current()][1]

    def _oran(self):
        return ORANLAR[self.oran_cb.current()][1]

    def _yukle(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for p in depolama.post_listele("onayli"):
            self.tree.insert("", "end", iid=str(p["id"]),
                             values=(p["id"], (p["sahne"] or "")[:50]))

    def _secili_id(self):
        sec = self.tree.selection()
        return int(sec[0]) if sec else None

    def _ses_ornek(self):
        from pathlib import Path
        cikti = Path(depolama.URETILEN_KLASOR) / "ornek_ses.mp3"
        self.durum.set("Ses örneği üretiliyor...")
        threading.Thread(target=self._ornek_worker, args=(str(cikti),),
                         daemon=True).start()

    def _ornek_worker(self, cikti):
        try:
            r = seslendirme.ornek_uret(cikti, ses=self._ses_adi(),
                                       motor_secimi=self._motor_secimi())
            self.after(0, lambda: self.durum.set(
                f"Örnek hazır ({r['motor']}, {r['sureSn']} sn): {r['dosya']}"))
        except Exception as e:
            self.after(0, lambda: self.durum.set(f"Ses hatası: {e}"))

    def _kur_video(self):
        pid = self._secili_id()
        if not pid:
            messagebox.showwarning("Seçim", "Onaylı bir post seçin")
            return
        if not video_mod.ffmpeg_var_mi():
            messagebox.showerror("ffmpeg", "ffmpeg bulunamadı")
            return
        self.ilerleme["maximum"] = 3
        self.ilerleme["value"] = 0
        self.durum.set("Video hazırlanıyor...")
        threading.Thread(target=self._video_worker, args=(pid,),
                         daemon=True).start()

    def _video_worker(self, pid):
        try:
            post = depolama.post_al(pid)
            klasor = depolama.URETILEN_KLASOR / "video" / f"post_{pid}"
            klasor.mkdir(parents=True, exist_ok=True)

            def cb(i, n, msg=""):
                self.after(0, lambda: self.durum.set(msg or f"{i}/{n}"))

            metin = (post.get("caption") or "").strip() or "Yeni içerik."
            self.after(0, lambda: self.durum.set("Seslendiriliyor..."))
            zamanlama = seslendirme.seslendir(
                [metin], klasor / "ses", ses=self._ses_adi(),
                dil=self._ses_adi()[:2], motor_secimi=self._motor_secimi(),
                ilerleme_cb=lambda i, n: self.after(
                    0, lambda: self.ilerleme.configure(value=i)))
            self.after(0, lambda: self.ilerleme.configure(value=2))
            ses_yol = klasor / "ses" / "parts" / "000.mp3"

            srt_yol = None
            if self.altyazi_var.get():
                srt_yol = klasor / "altyazi.srt"
                video_mod.srt_yaz([{"baslangicSn": 0.0,
                                    "sureSn": zamanlama["toplamSn"],
                                    "metin": metin.replace("\n", " ")}], srt_yol)

            self.after(0, lambda: self.durum.set("Render (ffmpeg)..."))
            sonuc = video_mod.video_kur(
                [(post["gorsel_yol"], zamanlama["toplamSn"])],
                klasor / "video.mp4",
                ses_yol=str(ses_yol) if ses_yol.is_file() else None,
                srt_yol=str(srt_yol) if srt_yol else None,
                oran=self._oran())
            self.after(0, lambda: self._bitti(sonuc))
        except Exception as e:
            self.after(0, lambda: self._hata(str(e)))

    def _bitti(self, sonuc):
        self.ilerleme.configure(value=3)
        self.durum.set(f"Tamam: {sonuc['cikti']} ({sonuc['sureSn']} sn, "
                       f"{sonuc['boyut_mb']} MB)")
        self._sonuclari_tara()

    def _hata(self, hata):
        self.durum.set(f"Hata: {hata}")

    def _sonuclari_tara(self):
        self.sonuc_liste.delete(0, "end")
        kok = depolama.URETILEN_KLASOR / "video"
        if not kok.is_dir():
            return
        for d in sorted(kok.iterdir(), reverse=True)[:30]:
            mp4 = d / "video.mp4"
            if mp4.is_file():
                self.sonuc_liste.insert("end", f"{d.name}  ({mp4.stat().st_size // 1024} KB)")

    def _klasorde_ac(self):
        kok = depolama.URETILEN_KLASOR / "video"
        kok.mkdir(parents=True, exist_ok=True)
        import os
        os.startfile(str(kok))
