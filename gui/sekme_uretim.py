# -*- coding: utf-8 -*-
"""Üretim & Onay sekmesi — vesikalık görsel önizleme + premium kartlar."""

import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from core import depolama, kisilik

ZEMIN = "#EDF4F3"
KART = "#FFFFFF"
CIZGI = "#C8D8D5"
METIN_KOYU = "#0F2A2C"
METIN_SOLUK = "#5A7A78"
TEAL_KOYU = "#0A3D47"
TEAL_VURGU = "#20B89A"
TEAL_PARLAK = "#3DDBB5"
YESIL_ACIK = "#DFF5EE"
VESIKALIK_BOYUT = (180, 240)  # 3:4 vesikalık oranı


class SekmeUretim(ttk.Frame):
    def __init__(self, parent):
        super().__init__(parent, style="Govde.TFrame")
        self._foto_onizleme = None
        self._kur()
        self._yukle()

    def _kur(self):
        paned = tk.PanedWindow(self, orient="horizontal", bg=ZEMIN,
                               sashwidth=6, sashrelief="flat", bd=0)
        paned.pack(fill="both", expand=True, padx=6, pady=6)

        # --- Sol: üretim kontrolü ---
        sol = tk.Frame(paned, bg=KART, highlightthickness=1,
                       highlightbackground=CIZGI)
        paned.add(sol, width=340)

        tk.Label(sol, text="İçerik Üret", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=18, pady=(18, 6))
        tk.Label(sol, text="Seçili karakter için sahne üretin",
                 bg=KART, fg=METIN_SOLUK, font=("Segoe UI", 9)).pack(anchor="w", padx=18)

        # Persona kartı (vesikalık ile)
        self.persona_kart = tk.Frame(sol, bg=KART)
        self.persona_kart.pack(fill="x", padx=18, pady=(12, 4))

        f1 = tk.Frame(self.persona_kart, bg=KART)
        f1.pack(fill="x")
        tk.Label(f1, text="Karakter:", bg=KART, fg=METIN_KOYU, width=10,
                 anchor="w", font=("Segoe UI", 10)).pack(side="left")
        self.persona_cb = ttk.Combobox(f1, state="readonly", width=22)
        self.persona_cb.pack(side="left", fill="x", expand=True)
        self.persona_cb.bind("<<ComboboxSelected>>", self._persona_degisti)

        # Seçili persona vesikalığı
        self.persona_vesikalik_frame = tk.Frame(sol, bg=KART, height=200)
        self.persona_vesikalik_frame.pack(fill="x", padx=18, pady=6)
        self.persona_vesikalik_frame.pack_propagate(False)
        self.persona_vesikalik_label = tk.Label(
            self.persona_vesikalik_frame,
            text="Karakter seçin",
            bg=KART, fg=METIN_SOLUK, font=("Segoe UI", 9))
        self.persona_vesikalik_label.pack(expand=True)

        f2 = tk.Frame(sol, bg=KART)
        f2.pack(fill="x", padx=18, pady=4)
        tk.Label(f2, text="Sahne sayısı:", bg=KART, fg=METIN_KOYU, width=10,
                 anchor="w", font=("Segoe UI", 10)).pack(side="left")
        self.sahne_spin = ttk.Spinbox(f2, from_=1, to=10, width=5)
        self.sahne_spin.set(3)
        self.sahne_spin.pack(side="left")

        self.ilerleme = ttk.Progressbar(sol, mode="determinate", length=300)
        self.ilerleme.pack(fill="x", padx=18, pady=(14, 6))
        self.ilerleme_deger = tk.StringVar(value="Hazır")
        tk.Label(sol, textvariable=self.ilerleme_deger, bg=KART,
                 fg=METIN_SOLUK, font=("Segoe UI", 9),
                 anchor="w").pack(fill="x", padx=18)

        ttk.Button(sol, text="Üretimi Başlat", style="Yesil.TButton",
                   command=self._baslat).pack(fill="x", padx=18, pady=(10, 4))
        ttk.Button(sol, text="Listeyi Yenile", style="Kart.TButton",
                   command=self._yukle).pack(fill="x", padx=18, pady=2)

        # --- Orta: liste ---
        orta = tk.Frame(paned, bg=KART, highlightthickness=1,
                        highlightbackground=CIZGI)
        paned.add(orta, width=360)

        ust = tk.Frame(orta, bg=KART)
        ust.pack(fill="x", padx=10, pady=(12, 4))
        tk.Label(ust, text="Onay Kuyruğu", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 12, "bold")).pack(side="left")

        self.filtre = tk.StringVar(value="onay_bekliyor")
        filtre_f = tk.Frame(orta, bg=KART)
        filtre_f.pack(fill="x", padx=10, pady=2)
        for text, val in [("Bekleyen", "onay_bekliyor"), ("Onaylı", "onayli"),
                          ("Paylaşılan", "paylasildi"), ("Tümü", "")]:
            ttk.Radiobutton(filtre_f, text=text, value=val, variable=self.filtre,
                            command=self._yukle).pack(side="left", padx=4)

        self.tree = ttk.Treeview(orta, columns=("id", "sahne", "durum"),
                                 show="headings", height=14)
        self.tree.heading("id", text="ID")
        self.tree.heading("sahne", text="Sahne")
        self.tree.heading("durum", text="Durum")
        self.tree.column("id", width=45)
        self.tree.column("sahne", width=220)
        self.tree.column("durum", width=80)
        self.tree.pack(fill="both", expand=True, padx=10, pady=4)
        self.tree.bind("<<TreeviewSelect>>", self._onizleme)

        # --- Sağ: vesikalık önizleme ---
        sag = tk.Frame(paned, bg=KART, highlightthickness=1,
                       highlightbackground=CIZGI)
        paned.add(sag, width=340)

        tk.Label(sag, text="Vesikalık Önizleme", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 12, "bold")).pack(anchor="w", padx=16, pady=(14, 4))

        # Vesikalık kart
        self.vesikalik_kart = tk.Frame(sag, bg=ZEMIN, highlightthickness=2,
                                       highlightbackground=TEAL_VURGU, height=280)
        self.vesikalik_kart.pack(fill="x", padx=16, pady=6)
        self.vesikalik_kart.pack_propagate(False)
        self.vesikalik_label = tk.Label(
            self.vesikalik_kart, text="Post seçin",
            bg=ZEMIN, fg=METIN_SOLUK, font=("Segoe UI", 10))
        self.vesikalik_label.pack(expand=True)

        # Caption
        tk.Label(sag, text="Caption", bg=KART, fg=TEAL_KOYU,
                 font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=16, pady=(8, 2))
        self.caption_text = tk.Text(sag, height=5, width=38, wrap="word",
                                    font=("Segoe UI", 9), bg=ZEMIN,
                                    fg=METIN_KOYU, relief="solid",
                                    borderwidth=1, bd=0)
        self.caption_text.pack(fill="x", padx=16, pady=2)
        self.caption_text.config(state="disabled")

        # Butonlar
        btn_f = tk.Frame(sag, bg=KART)
        btn_f.pack(fill="x", padx=16, pady=(10, 6))
        ttk.Button(btn_f, text="Onayla", style="Yesil.TButton",
                   command=lambda: self._durum_degistir("onayli")).pack(
            side="left", padx=(0, 4))
        ttk.Button(btn_f, text="Reddet", style="Tehlike.TButton",
                   command=lambda: self._durum_degistir("reddedildi")).pack(
            side="left", padx=(0, 4))

        btn_f2 = tk.Frame(sag, bg=KART)
        btn_f2.pack(fill="x", padx=16, pady=2)
        ttk.Button(btn_f2, text="Caption Panoya Kopyala", style="Kart.TButton",
                   command=self._panoya_kopyala).pack(fill="x", pady=2)
        ttk.Button(btn_f2, text="Klasörde Aç", style="Kart.TButton",
                   command=self._klasorde_ac).pack(fill="x", pady=2)

        # Caption kaydet
        ttk.Button(sag, text="Caption'ı Kaydet", style="Teal.TButton",
                   command=self._caption_kaydet).pack(fill="x", padx=16, pady=(6, 4))

        self._persona_yukle()

    def _persona_yukle(self):
        kisiler = kisilik.persona_listele()
        degerler = [f"{p['id']} — {p['ad']}" for p in kisiler]
        self.persona_cb["values"] = degerler
        if degerler:
            self.persona_cb.current(0)
            self._persona_vesikalik_goster()

    def _persona_degisti(self, event=None):
        self._persona_vesikalik_goster()

    def _persona_vesikalik_goster(self):
        """Seçili persona'nın kanon görselini vesikalık olarak gösterir."""
        secim = self.persona_cb.get()
        if not secim:
            return
        pid = int(secim.split("—")[0].strip())
        persona = kisilik.persona_al(pid)
        if not persona:
            return
        kanon = persona.get("kanon_gorsel")
        if kanon:
            self._vesikalik_yukle(self.persona_vesikalik_label, kanon,
                                  self.persona_vesikalik_frame)
        else:
            self.persona_vesikalik_label.config(
                image="", text=f"{persona['ad']}\nSeed: {persona.get('seed')}\n"
                               "Canon yüz yok — üretin")
            self.persona_vesikalik_label.image = None

    def _vesikalik_yukle(self, label_widget, gorsel_yol, frame_widget):
        """Görseli vesikalık oranında yükleyip label'a gösterir."""
        try:
            from PIL import Image, ImageTk, ImageDraw
            img = Image.open(gorsel_yol)
            # Vesikalık oranına kırp (3:4)
            w, h = img.size
            hedef_oran = VESIKALIK_BOYUT[0] / VESIKALIK_BOYUT[1]
            mevcut = w / h
            if mevcut > hedef_oran:
                yeni_w = int(h * hedef_oran)
                x = (w - yeni_w) // 2
                img = img.crop((x, 0, x + yeni_w, h))
            else:
                yeni_h = int(w / hedef_oran)
                y = (h - yeni_h) // 2
                img = img.crop((0, y, w, y + yeni_h))

            img = img.resize(VESIKALIK_BOYUT, Image.LANCZOS)

            # Vesikalık çerçeve: ince bordür + köşe işaretleri
            cerceve = Image.new("RGB", (VESIKALIK_BOYUT[0] + 12,
                                        VESIKALIK_BOYUT[1] + 12), (32, 184, 154))
            cerceve.paste(img, (6, 6))

            foto = ImageTk.PhotoImage(cerceve)
            label_widget.config(image=foto, text="")
            label_widget.image = foto
        except Exception as e:
            label_widget.config(image="", text=f"Hata: {e}")
            label_widget.image = None

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
                             values=(p["id"], (p["sahne"] or "")[:60], p["durum"]))

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
        if not post:
            return
        # Vesikalık göster
        if post.get("gorsel_yol"):
            self._vesikalik_yukle(self.vesikalik_label, post["gorsel_yol"],
                                  self.vesikalik_kart)
        # Caption yükle
        self.caption_text.config(state="normal")
        self.caption_text.delete("1.0", "end")
        self.caption_text.insert("1.0", post.get("caption", ""))
        self.caption_text.config(state="disabled")

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

    def _caption_kaydet(self):
        pid = self._secili_id()
        if not pid:
            return
        yeni = self.caption_text.get("1.0", "end").strip()
        with depolama.baglanti() as c:
            c.execute("UPDATE posts SET caption=? WHERE id=?", (yeni, pid))
            c.commit()
        messagebox.showinfo("Tamam", "Caption kaydedildi")
