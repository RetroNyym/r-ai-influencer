# -*- coding: utf-8 -*-
"""Public URL üretici: Catbox / tmpfiles / manuel host seçenekleri."""

import time
from pathlib import Path

import requests

TIMEOUT = 60


def public_url_yap(gorsel_yol, yontem="catbox"):
    """Yerel görsel için public URL üretir.

    Yontemler:
    - catbox:猫箱 (ücretsiz, kalıcı, 200MB)
    - tmpfiles: tmpfiles.org (geçici, ~1 saat)
    - manel: kullanıcı kendi host'unu girer
    """
    yol = Path(gorsel_yol)
    if not yol.is_file():
        raise FileNotFoundError(f"Dosya yok: {gorsel_yol}")

    if yontem == "catbox":
        return _catbox(yol)
    elif yontem == "tmpfiles":
        return _tmpfiles(yol)
    elif yontem == "manuel":
        return depolama_ayar_url()
    else:
        raise ValueError(f"Bilinmeyen yontem: {yontem}")


def _catbox(yol):
    with open(yol, "rb") as f:
        r = requests.post(
            "https://catbox.moe/user/api.php",
            data={"reqtype": "fileupload"},
            files={"fileToUpload": (yol.name, f, "image/jpeg")},
            timeout=TIMEOUT)
    r.raise_for_status()
    url = r.text.strip()
    if not url.startswith("http"):
        raise RuntimeError(f"Catbox hatasi: {url}")
    return url


def _tmpfiles(yol):
    with open(yol, "rb") as f:
        r = requests.post(
            "https://tmpfiles.org/api/v1/upload",
            files={"file": (yol.name, f, "image/jpeg")},
            timeout=TIMEOUT)
    r.raise_for_status()
    veri = r.json()
    url = veri.get("data", {}).get("url", "")
    # tmpfiles linkini direct indirme linkine çevir
    if "/dl/" not in url and url:
        url = url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
    if not url:
        raise RuntimeError("tmpfiles hatasi")
    return url


def depolama_ayar_url():
    """Manuel host: kullanıcı ayarlardan URL şablonu girer.
    Ör: https://mysite.com/img/{dosya}
    """
    from core import depolama
    sablon = depolama.ayar_al("manuel_host_sablon")
    if not sablon:
        raise RuntimeError("Manuel host sablonu ayarlanmamis (Ayarlar sekmesi)")
    # Kullanıcı dosyayı manuel yükledi; sablonda {dosya} yer tutucusu olmalı
    # Basitçe: sablonu döndür (kullanıcı kendi akışını bilir)
    return sablon
