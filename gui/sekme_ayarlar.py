# -*- coding: utf-8 -*-
"""Ayarlar sekmesi: IG/TikTok token, host seçimi, Pollinations key."""

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from core import depolama
from gui.palet import (CIZGI, KART, METIN_KOYU, TEAL, TEAL_KOYU,
                       TEAL_VURGU, YESIL_ACIK, ZEMIN)


class SekmeAyarlar(ttk.Frame):
    def __init__(self, parent, ig_foto=None, tt_foto=None):
        super().__init__(parent, style="Govde.TFrame")
        self.ig_foto = ig_foto
        self.tt_foto = tt_foto
        self._kur()
        self._yukle()

    def _kur(self):
        canvas = tk.Canvas(self, bg=ZEMIN, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        self.icerik = tk.Frame(canvas, bg=KART)

        self.icerik.bind("<Configure>",
                         lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=self.icerik, anchor="nw", tags="icerik")
        canvas.configure(yscrollcommand=scrollbar.set)
        # Canvas genişliği değişince frame genişliğini de güncelle
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(
            "icerik", width=e.width))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Pollinations ---
        self._kart_baslik("Pollinations.ai  ·  Ücretsiz Üretim")
        self._alan("pollinations_key", "API Key (opsiyonel)",
                   "Boş bırakılabilir — anahtarsız çalışır")
        self._ipucu("Görsel: image.pollinations.ai  |  Metin: text.pollinations.ai\n"
                    "Rate limit: ~5sn/istek. Daha hızlı için ücretli key alınabilir.")

        # --- Host ---
        self._kart_baslik("Public URL Host  ·  Instagram için gerekli")
        f = tk.Frame(self.icerik, bg=KART)
        f.pack(fill="x", padx=16, pady=4)
        tk.Label(f, text="Yöntem:", bg=KART, fg=METIN_KOYU, width=16,
                 anchor="w", font=("Segoe UI", 10)).pack(side="left")
        self.host_cb = ttk.Combobox(
            f, values=["catbox", "tmpfiles", "manuel"], state="readonly", width=12)
        self.host_cb.pack(side="left")
        self.host_cb.bind("<<ComboboxSelected>>", self._host_degisti)

        self.manel_frame = tk.Frame(self.icerik, bg=KART)
        self._alan("manuel_host_sablon", "Manuel host şablonu",
                   "https://ornek.com/img/{dosya}", frame=self.manel_frame)
        self._ipucu("catbox: ücretsiz, kalıcı (önerilen)\n"
                    "tmpfiles: geçici (~1 saat)\n"
                    "manuel: kendi host'unuzu kullanın")

        # --- Instagram (logolu) ---
        self._platform_kart("Instagram Graph API", self.ig_foto,
                            "#E1306C", "IG")
        self._alan("ig_token", "Access Token", "EAA...")
        self._alan("ig_user_id", "IG User ID", "17841400...")
        self._onay("ig_aktif", "Instagram paylaşımı aktif")
        ttk.Button(self.icerik, text="Instagram Bağlantı Testi",
                   style="Yesil.TButton",
                   command=self._ig_test).pack(anchor="w", padx=16, pady=4)
        self._ipucu("Meta for Developers > App > Instagram Graph API\n"
                    "Permissions: instagram_content_publish\n"
                    "Professional hesap + Facebook Page şart.\n"
                    "Uzun ömürlü Page token kullanın.")

        # --- TikTok (logolu) ---
        self._platform_kart("TikTok Content Posting API", self.tt_foto,
                            "#000000", "TT")
        self._alan("tt_token", "User Access Token", "")
        self._alan("tt_client_key", "Client Key", "")
        self._alan("tt_client_secret", "Client Secret", "")
        f2 = tk.Frame(self.icerik, bg=KART)
        f2.pack(fill="x", padx=16, pady=4)
        tk.Label(f2, text="Mod:", bg=KART, fg=METIN_KOYU, width=16,
                 anchor="w", font=("Segoe UI", 10)).pack(side="left")
        self.tt_mod_cb = ttk.Combobox(
            f2, values=["taslak", "self_only", "direct"],
            state="readonly", width=12)
        self.tt_mod_cb.pack(side="left")
        self._onay("tt_aktif", "TikTok paylaşımı aktif")
        ttk.Button(self.icerik, text="TikTok Bağlantı Testi",
                   style="Yesil.TButton",
                   command=self._tt_test).pack(anchor="w", padx=16, pady=4)
        self._ipucu("developers.tiktok.com > App > Content Posting API\n"
                    "Onaysız istemci: taslak (MEDIA_UPLOAD) veya SELF_ONLY\n"
                    "Audit sonrası: direct + herkese açık\n"
                    "Token: Login Kit ile alınan user access token")

        # --- Kaydet ---
        tk.Frame(self.icerik, bg=KART, height=8).pack(fill="x")
        btn_kaydet = tk.Frame(self.icerik, bg=TEAL, height=56)
        btn_kaydet.pack(fill="x")
        btn_kaydet.pack_propagate(False)
        ttk.Button(btn_kaydet, text="Ayarları Kaydet", style="Yesil.TButton",
                   command=self._kaydet).pack(pady=12)

    def _kart_baslik(self, metin):
        f = tk.Frame(self.icerik, bg=TEAL, height=38)
        f.pack(fill="x")
        f.pack_propagate(False)
        tk.Label(f, text="  " + metin, bg=TEAL, fg="#FFFFFF",
                 font=("Segoe UI", 11, "bold"), anchor="w").pack(
            side="left", fill="y")

    def _platform_kart(self, metin, foto, renk, rozet):
        """Sosyal medya logosu + başlık kartı."""
        f = tk.Frame(self.icerik, bg=TEAL, height=42)
        f.pack(fill="x")
        f.pack_propagate(False)

        if foto:
            lbl = tk.Label(f, image=foto, bg=TEAL)
            lbl.pack(side="left", padx=(14, 6), pady=8)
        else:
            # Logo yoksa renkli rozet
            tk.Label(f, text=rozet, bg=renk, fg="#FFFFFF",
                     font=("Segoe UI", 10, "bold"), width=3, height=1,
                     relief="flat").pack(side="left", padx=(14, 6), pady=8)

        tk.Label(f, text=metin, bg=TEAL, fg="#FFFFFF",
                 font=("Segoe UI", 11, "bold"), anchor="w").pack(
            side="left", fill="y")

    def _alan(self, anahtar, etiket, ipucu, frame=None):
        hedef = frame if frame is not None else self.icerik
        if frame is not None:
            frame.pack(fill="x", padx=16, pady=2)
        f = tk.Frame(hedef, bg=KART)
        f.pack(fill="x", padx=16, pady=3)
        tk.Label(f, text=etiket, bg=KART, fg=METIN_KOYU, width=22,
                 anchor="w", font=("Segoe UI", 10)).pack(side="left")
        e = ttk.Entry(f)
        e.pack(side="left", fill="x", expand=True)
        setattr(self, f"entry_{anahtar}", e)

    def _onay(self, anahtar, etiket):
        var = tk.BooleanVar(value=False)
        tk.Checkbutton(self.icerik, text=etiket, variable=var, bg=KART,
                       fg=METIN_KOYU, selectcolor=KART,
                       activebackground=KART, font=("Segoe UI", 10)).pack(
            anchor="w", padx=16, pady=2)
        setattr(self, f"var_{anahtar}", var)

    def _ipucu(self, metin):
        f = tk.Frame(self.icerik, bg=YESIL_ACIK)
        f.pack(fill="x", padx=16, pady=(2, 10))
        tk.Label(f, text=metin, bg=YESIL_ACIK, fg=TEAL_KOYU,
                 justify="left", font=("Segoe UI", 9),
                 anchor="w").pack(fill="x", padx=8, pady=6)

    def _host_degisti(self, event):
        if self.host_cb.get() == "manuel":
            self.manel_frame.pack(fill="x")
        else:
            self.manel_frame.pack_forget()

    def _yukle(self):
        for anahtar in ["pollinations_key", "ig_token", "ig_user_id",
                        "tt_token", "tt_client_key", "tt_client_secret",
                        "manuel_host_sablon"]:
            deger = depolama.ayar_al(anahtar, "")
            e = getattr(self, f"entry_{anahtar}", None)
            if e:
                e.delete(0, "end")
                e.insert(0, deger or "")

        for anahtar in ["ig_aktif", "tt_aktif"]:
            var = getattr(self, f"var_{anahtar}", None)
            if var:
                var.set(depolama.ayar_al(anahtar) == "1")

        host_yontem = depolama.ayar_al("host_yontem", "catbox")
        self.host_cb.set(host_yontem)
        if host_yontem == "manuel":
            self.manel_frame.pack(fill="x")

        tt_mod = depolama.ayar_al("tt_mod", "taslak")
        self.tt_mod_cb.set(tt_mod)

    def _kaydet(self):
        for anahtar in ["pollinations_key", "ig_token", "ig_user_id",
                        "tt_token", "tt_client_key", "tt_client_secret",
                        "manuel_host_sablon"]:
            e = getattr(self, f"entry_{anahtar}", None)
            if e:
                depolama.ayar_koy(anahtar, e.get().strip())

        for anahtar in ["ig_aktif", "tt_aktif"]:
            var = getattr(self, f"var_{anahtar}", None)
            if var:
                depolama.ayar_koy(anahtar, "1" if var.get() else "0")

        depolama.ayar_koy("host_yontem", self.host_cb.get())
        depolama.ayar_koy("tt_mod", self.tt_mod_cb.get())
        messagebox.showinfo("Tamam", "Ayarlar kaydedildi")

    def _ig_test(self):
        self._kaydet()
        threading.Thread(target=self._ig_test_worker, daemon=True).start()

    def _ig_test_worker(self):
        from core.paylasim import instagram
        ok, mesaj = instagram.baglanti_testi()
        self.after(0, lambda: messagebox.showinfo(
            "Instagram Testi", f"{'✓ Başarılı' if ok else '✗ Hata'}: {mesaj}"))

    def _tt_test(self):
        self._kaydet()
        threading.Thread(target=self._tt_test_worker, daemon=True).start()

    def _tt_test_worker(self):
        from core.paylasim import tiktok
        ok, mesaj = tiktok.baglanti_testi()
        self.after(0, lambda: messagebox.showinfo(
            "TikTok Testi", f"{'✓ Başarılı' if ok else '✗ Hata'}: {mesaj}"))
