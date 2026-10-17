# -*- coding: utf-8 -*-
"""API Yönetimi sekmesi: çoklu API, key yapıştır → tanıma, test, aktif seçimi."""

import threading
import tkinter as tk
from tkinter import messagebox, ttk

from core import api_yonetici, depolama
from gui.palet import (AMBER, AMBER_ZEMIN, KART, METIN_KOYU, TEAL,
                       TEAL_KOYU, TEAL_VURGU, YESIL_ACIK, ZEMIN)


class SekmeApi(ttk.Frame):
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
        canvas.bind("<Configure>", lambda e: canvas.itemconfigure(
            "icerik", width=e.width))

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # --- Başlık ---
        self._kart_baslik("Görsel Üretim API'si Bağla")

        tk.Label(self.icerik,
                 text="Kendi API anahtarınızı yapıştırın — sistem otomatik tanır.\n"
                      "Veya listeden seçip anahtarı girin. API yoksa ücretsiz "
                      "Pollinations.ai kullanılır.",
                 bg=KART, fg=METIN_KOYU, font=("Segoe UI", 10),
                 justify="left", anchor="w").pack(fill="x", padx=16, pady=(4, 8))

        # --- API Seçimi + Key Yapıştırma ---
        f_sec = tk.Frame(self.icerik, bg=KART)
        f_sec.pack(fill="x", padx=16, pady=4)
        tk.Label(f_sec, text="API Seçin:", bg=KART, fg=METIN_KOYU, width=14,
                 anchor="w", font=("Segoe UI", 10, "bold")).pack(side="left")

        liste = [f"{adi}  ({aid})" for aid, adi, _, _ in api_yonetici.API_TANIMLAR]
        self.api_cb = ttk.Combobox(f_sec, values=liste, state="readonly", width=38)
        self.api_cb.current(0)
        self.api_cb.pack(side="left", padx=(0, 8))
        self.api_cb.bind("<<ComboboxSelected>>", self._api_secildi)

        # Key girişi
        f_key = tk.Frame(self.icerik, bg=KART)
        f_key.pack(fill="x", padx=16, pady=4)
        tk.Label(f_key, text="API Anahtarı:", bg=KART, fg=METIN_KOYU, width=14,
                 anchor="w", font=("Segoe UI", 10, "bold")).pack(side="left")
        self.key_entry = ttk.Entry(f_key, width=60)
        self.key_entry.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.key_entry.bind("<KeyRelease>", self._key_yapistirildi)

        # Tanıma rozeti
        self.tanima_frame = tk.Frame(self.icerik, bg=AMBER_ZEMIN)
        self.tanima_frame.pack(fill="x", padx=16, pady=4)
        self.tanima_label = tk.Label(
            self.tanima_frame,
            text="💡 Anahtarı yapıştırın — API otomatik tanınacak",
            bg=AMBER_ZEMIN, fg=AMBER, font=("Segoe UI", 10, "bold"),
            anchor="w", padx=8, pady=6)
        self.tanima_label.pack(fill="x")

        # Butonlar
        f_btn = tk.Frame(self.icerik, bg=KART)
        f_btn.pack(fill="x", padx=16, pady=8)
        ttk.Button(f_btn, text="Kaydet ve Aktif Yap", style="Yesil.TButton",
                   command=self._kaydet).pack(side="left", padx=(0, 6))
        ttk.Button(f_btn, text="Bağlantı Testi", style="Kart.TButton",
                   command=self._test).pack(side="left", padx=(0, 6))
        ttk.Button(f_btn, text="Sil", style="Kart.TButton",
                   command=self._sil).pack(side="left")

        # --- Kayıtlı API'ler tablosu ---
        self._kart_baslik("Kayıtlı API Anahtarları")
        self.tree = ttk.Treeview(
            self.icerik, columns=("ad", "key", "aktif"), show="headings", height=6)
        self.tree.heading("ad", text="API")
        self.tree.heading("key", text="Anahtar (maskeli)")
        self.tree.heading("aktif", text="Durum")
        self.tree.column("ad", width=280)
        self.tree.column("key", width=200)
        self.tree.column("aktif", width=100)
        self.tree.pack(fill="x", padx=16, pady=4)

        # Aktif API bilgisi
        self.aktif_frame = tk.Frame(self.icerik, bg=YESIL_ACIK)
        self.aktif_frame.pack(fill="x", padx=16, pady=(4, 8))
        self.aktif_label = tk.Label(
            self.aktif_frame, text="Aktif API: — (ücretsiz Pollinations)",
            bg=YESIL_ACIK, fg=TEAL_KOYU, font=("Segoe UI", 10, "bold"),
            anchor="w", padx=8, pady=6)
        self.aktif_label.pack(fill="x")

        # --- Sosyal medya bağlantıları (logolu) ---
        self._kart_baslik("Sosyal Medya Hesap Bağlantıları")
        self._platform_kart("Instagram Graph API", self.ig_foto, "#E1306C", "IG")
        self._alan("ig_token", "Access Token", "EAA...")
        self._alan("ig_user_id", "IG User ID", "17841400...")
        self._onay("ig_aktif", "Instagram paylaşımı aktif")
        ttk.Button(self.icerik, text="Instagram Bağlantı Testi",
                   style="Yesil.TButton",
                   command=self._ig_test).pack(anchor="w", padx=16, pady=4)
        self._ipucu("Meta for Developers > App > Instagram Graph API\n"
                    "Permissions: instagram_content_publish\n"
                    "Professional hesap + Facebook Page şart.")

        self._platform_kart("TikTok Content Posting API", self.tt_foto, "#000000", "TT")
        self._alan("tt_token", "User Access Token", "")
        self._alan("tt_client_key", "Client Key", "")
        self._alan("tt_client_secret", "Client Secret", "")
        f2 = tk.Frame(self.icerik, bg=KART)
        f2.pack(fill="x", padx=16, pady=4)
        tk.Label(f2, text="Mod:", bg=KART, fg=METIN_KOYU, width=14,
                 anchor="w", font=("Segoe UI", 10)).pack(side="left")
        self.tt_mod_cb = ttk.Combobox(
            f2, values=["taslak", "self_only", "direct"], state="readonly", width=12)
        self.tt_mod_cb.pack(side="left")
        self._onay("tt_aktif", "TikTok paylaşımı aktif")
        ttk.Button(self.icerik, text="TikTok Bağlantı Testi",
                   style="Yesil.TButton",
                   command=self._tt_test).pack(anchor="w", padx=16, pady=4)
        self._ipucu("developers.tiktok.com > App > Content Posting API\n"
                    "Onaysız istemci: taslak (MEDIA_UPLOAD) veya SELF_ONLY")

        # --- Host ---
        self._kart_baslik("Public URL Host  ·  Instagram için gerekli")
        f_h = tk.Frame(self.icerik, bg=KART)
        f_h.pack(fill="x", padx=16, pady=4)
        tk.Label(f_h, text="Yöntem:", bg=KART, fg=METIN_KOYU, width=14,
                 anchor="w", font=("Segoe UI", 10)).pack(side="left")
        self.host_cb = ttk.Combobox(
            f_h, values=["catbox", "tmpfiles", "manuel"], state="readonly", width=12)
        self.host_cb.pack(side="left")
        self._ipucu("catbox: ücretsiz, kalıcı (önerilen)  |  "
                    "tmpfiles: geçici  |  manuel: kendi host'unuz")

        # Pollinations
        self._kart_baslik("Pollinations.ai (Ücretsiz — API anahtarsız)")
        self._alan("pollinations_key", "API Key (opsiyonel)", "Boş bırakabilirsiniz")

        # Kaydet alt
        tk.Frame(self.icerik, bg=KART, height=8).pack(fill="x")
        btn_kaydet = tk.Frame(self.icerik, bg=TEAL, height=52)
        btn_kaydet.pack(fill="x")
        btn_kaydet.pack_propagate(False)
        ttk.Button(btn_kaydet, text="Tüm Ayarları Kaydet", style="Yesil.TButton",
                   command=self._kaydet_tumu).pack(pady=10)

    def _kart_baslik(self, metin):
        f = tk.Frame(self.icerik, bg=TEAL, height=38)
        f.pack(fill="x")
        f.pack_propagate(False)
        tk.Label(f, text="  " + metin, bg=TEAL, fg="#FFFFFF",
                 font=("Segoe UI", 11, "bold"), anchor="w").pack(side="left", fill="y")

    def _platform_kart(self, metin, foto, renk, rozet):
        f = tk.Frame(self.icerik, bg=TEAL, height=42)
        f.pack(fill="x")
        f.pack_propagate(False)
        if foto:
            tk.Label(f, image=foto, bg=TEAL).pack(side="left", padx=(14, 6), pady=8)
        else:
            tk.Label(f, text=rozet, bg=renk, fg="#FFFFFF",
                     font=("Segoe UI", 10, "bold"), width=3, height=1,
                     relief="flat").pack(side="left", padx=(14, 6), pady=8)
        tk.Label(f, text=metin, bg=TEAL, fg="#FFFFFF",
                 font=("Segoe UI", 11, "bold"), anchor="w").pack(side="left", fill="y")

    def _alan(self, anahtar, etiket, ipucu, frame=None):
        hedef = frame if frame is not None else self.icerik
        f = tk.Frame(hedef, bg=KART)
        f.pack(fill="x", padx=16, pady=3)
        tk.Label(f, text=etiket, bg=KART, fg=METIN_KOYU, width=16,
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

    # --- API tanıma ---
    def _key_yapistirildi(self, event=None):
        key = self.key_entry.get().strip()
        if not key:
            self.tanima_label.config(
                text="💡 Anahtarı yapıştırın — API otomatik tanınacak")
            return
        api_id, api_adi = api_yonetici.key_tanima(key)
        if api_id:
            self.tanima_label.config(
                text=f"✓ Tanındı: {api_adi}  (ID: {api_id})")
            # Combobox'ı da güncelle
            for i, (aid, adi, _, _) in enumerate(api_yonetici.API_TANIMLAR):
                if aid == api_id:
                    self.api_cb.current(i)
                    break
        else:
            self.tanima_label.config(text="⚠ Tanınamadı — listeden seçin")

    def _api_secildi(self, event=None):
        secim = self.api_cb.get()
        if "(" in secim and ")" in secim:
            api_id = secim.split("(")[-1].rstrip(")").strip()
            # Kayıtlı key varsa doldur
            key = depolama.ayar_al(f"api_{api_id}_key", "")
            if key:
                self.key_entry.delete(0, "end")
                self.key_entry.insert(0, key)
            self.tanima_label.config(text=f"Seçildi: {secim}")

    def _kaydet(self):
        key = self.key_entry.get().strip()
        if not key:
            messagebox.showwarning("Eksik", "API anahtarı girin")
            return
        secim = self.api_cb.get()
        api_id = secim.split("(")[-1].rstrip(")").strip() if "(" in secim else "custom"

        # Key'den tanıyıp doğrula
        taninan_id, taninan_adi = api_yonetici.key_tanima(key)
        if taninan_id and taninan_id != api_id:
            # Tanıma ile seçim çelişiyorsa tanımaya güven
            cevap = messagebox.askyesno(
                "Tanıma Farkı",
                f"Anahtar '{taninan_adi}' olarak tanındı.\n"
                f"Seçiminiz: {secim}\n\nTanımaya göre kaydedilsin mi?")
            if cevap:
                api_id = taninan_id

        api_yonetici.api_kaydet(api_id, key)
        self._tablo_yenile()
        self._aktif_goster()
        messagebox.showinfo("Tamam", f"API kaydedildi ve aktif yapıldı: {api_id}")

    def _test(self):
        key = self.key_entry.get().strip()
        if not key:
            messagebox.showwarning("Eksik", "Önce anahtar girin")
            return
        secim = self.api_cb.get()
        api_id = secim.split("(")[-1].rstrip(")").strip() if "(" in secim else "custom"
        threading.Thread(target=self._test_worker, args=(api_id, key),
                         daemon=True).start()

    def _test_worker(self, api_id, key):
        ok, mesaj = api_yonetici.baglanti_testi(api_id, key)
        self.after(0, lambda: messagebox.showinfo(
            "API Testi", f"{'✓' if ok else '✗'} {mesaj}"))

    def _sil(self):
        secim = self.api_cb.get()
        api_id = secim.split("(")[-1].rstrip(")").strip() if "(" in secim else None
        if api_id:
            api_yonetici.api_sil(api_id)
            self.key_entry.delete(0, "end")
            self._tablo_yenile()
            self._aktif_goster()

    def _tablo_yenile(self):
        for i in self.tree.get_children():
            self.tree.delete(i)
        for kayit in api_yonetici.kayitli_api_listesi():
            self.tree.insert("", "end", values=(
                kayit["ad"], kayit["key_maskeli"],
                "★ AKTİF" if kayit["aktif"] else "Kayıtlı"))

    def _aktif_goster(self):
        api = api_yonetici.aktif_api()
        if api and api.get("key"):
            self.aktif_label.config(
                text=f"Aktif API: {api['ad']}  (ID: {api['id']})")
        else:
            self.aktif_label.config(
                text="Aktif API: — (ücretsiz Pollinations.ai kullanılıyor)")

    def _yukle(self):
        self._tablo_yenile()
        self._aktif_goster()
        # Sosyal medya
        for anahtar in ["ig_token", "ig_user_id", "tt_token",
                        "tt_client_key", "tt_client_secret", "pollinations_key"]:
            deger = depolama.ayar_al(anahtar, "")
            e = getattr(self, f"entry_{anahtar}", None)
            if e:
                e.delete(0, "end")
                e.insert(0, deger or "")
        for anahtar in ["ig_aktif", "tt_aktif"]:
            var = getattr(self, f"var_{anahtar}", None)
            if var:
                var.set(depolama.ayar_al(anahtar) == "1")
        self.host_cb.set(depolama.ayar_al("host_yontem", "catbox"))
        self.tt_mod_cb.set(depolama.ayar_al("tt_mod", "taslak"))

    def _kaydet_tumu(self):
        for anahtar in ["ig_token", "ig_user_id", "tt_token",
                        "tt_client_key", "tt_client_secret", "pollinations_key"]:
            e = getattr(self, f"entry_{anahtar}", None)
            if e:
                depolama.ayar_koy(anahtar, e.get().strip())
        for anahtar in ["ig_aktif", "tt_aktif"]:
            var = getattr(self, f"var_{anahtar}", None)
            if var:
                depolama.ayar_koy(anahtar, "1" if var.get() else "0")
        depolama.ayar_koy("host_yontem", self.host_cb.get())
        depolama.ayar_koy("tt_mod", self.tt_mod_cb.get())
        messagebox.showinfo("Tamam", "Tüm ayarlar kaydedildi")

    def _ig_test(self):
        self._kaydet_tumu()
        threading.Thread(target=self._ig_test_worker, daemon=True).start()

    def _ig_test_worker(self):
        from core.paylasim import instagram
        ok, mesaj = instagram.baglanti_testi()
        self.after(0, lambda: messagebox.showinfo(
            "Instagram Testi", f"{'✓ Başarılı' if ok else '✗ Hata'}: {mesaj}"))

    def _tt_test(self):
        self._kaydet_tumu()
        threading.Thread(target=self._tt_test_worker, daemon=True).start()

    def _tt_test_worker(self):
        from core.paylasim import tiktok
        ok, mesaj = tiktok.baglanti_testi()
        self.after(0, lambda: messagebox.showinfo(
            "TikTok Testi", f"{'✓ Başarılı' if ok else '✗ Hata'}: {mesaj}"))
