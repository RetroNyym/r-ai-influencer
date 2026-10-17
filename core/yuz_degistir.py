# -*- coding: utf-8 -*-
"""AI ile gerçekçi yüz kimliği dönüştürme — insightface inswapper + ArcFace harmanlama.

Bir yüzü (kullanıcının kendi fotoğrafı) *farklı ama gerçekçi* bir surete çevirir.
Sektör standardı olan InSwapper-128 + buffalo_l ArcFace embedding'leri kullanılır:

1. Kimlik uzayı: Her yüz 512 boyutlu ArcFace embedding ile temsil edilir.
2. Kimlik harmanlama: z_yeni = (1-oran)*z_kullanici + oran*z_hedef → iki kişi
   arasında gerçekçi, yeni bir ara kimlik (gerçek insan gibi görünür).
3. InSwapper: Bu blended kimliği hedef poza/expression/arka plana yapıştırır.
4. Sonuç: AI ile yapılmış olduğu belli olmayan, doğal bir farklı kişi.

Modlar:
- "kullanici": Kullanıcının kendi fotoğrafında yüzü blended kimlikle değiştirir
  (poz/arka plan kullanıcıya ait, yüz farklı bir kişi olur) — ana kullanım.
- "hedef": Hedef fotoğrafın pozu korunur, kimlik blended kimliğe kaydırılır.

Model lisansı: InSwapper-128 / buffalo_l akademik-araştırma amaçlıdır.
Ticari kullanım için InsightFace'ten lisans gerekir.
"""

from pathlib import Path
import random

import cv2
import numpy as np

MODELLER = Path.home() / ".insightface" / "models"
INSP_URL = ("https://huggingface.co/ezioruan/inswapper_128.onnx/resolve/main/"
            "inswapper_128.onnx")

_APP = None
_SWAPPER = None
_HAZIR = False


def model_durumu():
    """Model dosyalarının varlığını döndürür (indirme tetiklemez)."""
    insw = MODELLER / "inswapper_128.onnx"
    buffalo = MODELLER / "buffalo_l"
    return {
        "inswapper": insw.is_file() and insw.stat().st_size > 100_000_000,
        "buffalo_l": buffalo.is_dir(),
    }


def _inswapper_indir():
    insw = MODELLER / "inswapper_128.onnx"
    if insw.is_file() and insw.stat().st_size > 100_000_000:
        return insw
    MODELLER.mkdir(parents=True, exist_ok=True)
    import requests
    with requests.get(INSP_URL, stream=True, timeout=300) as r:
        r.raise_for_status()
        tmp = insw.with_suffix(".tmp")
        with open(tmp, "wb") as f:
            for ch in r.iter_content(1 << 20):
                f.write(ch)
        tmp.rename(insw)
    return insw


def _motor():
    """App (buffalo_l) + swapper'ı tembel yükler. (1. çağrı ~10-40sn sürebilir)"""
    global _APP, _SWAPPER, _HAZIR
    if _HAZIR:
        return _APP, _SWAPPER
    from insightface.app import FaceAnalysis
    from insightface.model_zoo import model_zoo
    from insightface.app.common import Face  # noqa: F401  (yukleme testi)

    insw = _inswapper_indir()
    _APP = FaceAnalysis(name="buffalo_l", providers=["CPUExecutionProvider"])
    _APP.prepare(ctx_id=-1, det_size=(640, 640))
    _SWAPPER = model_zoo.get_model(str(insw), providers=["CPUExecutionProvider"])
    _HAZIR = True
    return _APP, _SWAPPER


def en_iyi_yuz(app, img):
    """En yüksek güven skorlu yüzü döndürür; yoksa None."""
    yuzler = app.get(img)
    if not yuzler:
        return None
    return max(yuzler, key=lambda f: getattr(f, "det_score", 0))


def _harmanla(z_k, z_h, oran):
    """İki ArcFace embedding'i harmanlar ve yeniden normalize eder."""
    z = (1 - oran) * z_k.astype(np.float32) + oran * z_h.astype(np.float32)
    return z / (np.linalg.norm(z) + 1e-6)


def kimlik_al(gorsel_yol):
    """Bir fotoğraftan (yol veya ndarray) en iyi yüzün embedding'ini alır."""
    app, _ = _motor()
    img = cv2.imread(str(gorsel_yol)) if not isinstance(gorsel_yol, np.ndarray) else gorsel_yol
    if img is None:
        raise ValueError(f"Görsel okunamadı: {gorsel_yol}")
    f = en_iyi_yuz(app, img)
    if f is None:
        raise ValueError("Yüz bulunamadı. Daha net bir portre deneyin.")
    return f


def suret_degistir(kullanici_yol, hedef_yol, oran=0.55, mod="kullanici"):
    """Kullanıcının yüzünü, hedef kimlikle harmanlayarak farklı bir surete çevirir.

    kullanici_yol : dönüşüme uğrayacak fotoğraf (kullanıcının kendi yüzü).
    hedef_yol     : kimlik yönünü belirleyen hedef fotoğraf (farklı bir kişi).
    oran          : 0.0 (kullanıcıya sadık) .. 1.0 (hedefe sadık). ~0.5-0.7 fark yaratır.
    mod           : "kullanici" (kullanıcının pozu korunur) veya "hedef".
    """
    app, swapper = _motor()

    k_img = cv2.imread(str(kullanici_yol)) if not isinstance(kullanici_yol, np.ndarray) else kullanici_yol
    h_img = cv2.imread(str(hedef_yol)) if not isinstance(hedef_yol, np.ndarray) else hedef_yol
    if k_img is None:
        raise ValueError(f"Kullanıcı görseli okunamadı: {kullanici_yol}")
    if h_img is None:
        raise ValueError(f"Hedef görsel okunamadı: {hedef_yol}")

    f_k = en_iyi_yuz(app, k_img)
    f_h = en_iyi_yuz(app, h_img)
    if f_k is None:
        raise ValueError("Kullanıcı fotoğrafında yüz bulunamadı.")
    if f_h is None:
        raise ValueError("Hedef fotoğrafında yüz bulunamadı.")

    z_yeni = _harmanla(f_k.embedding, f_h.embedding, oran)

    from insightface.app.common import Face

    if mod == "hedef":
        temel, tespit = h_img, f_h
    else:  # "kullanici"
        temel, tespit = k_img, f_k

    kaynak = Face(dict(tespit))
    kaynak["embedding"] = z_yeni
    # NOT: inswapper.get(img, target_face, source_face) — hedef önce, kaynak sonra.
    sonuc = swapper.get(temel.copy(), tespit, kaynak)
    return sonuc


def persona_cikar(kullanici_yol, hedef_yollar, oran=0.55, cikti_klasor="test_cikti/suretler",
                  mod="kullanici", seed=None):
    """Kullanıcı fotoğrafından, her hedef için bir suret üretir (toplu)."""
    cikti_klasor = Path(cikti_klasor)
    cikti_klasor.mkdir(parents=True, exist_ok=True)
    if seed is None:
        seed = random.randint(1, 2**31 - 1)
    sonuclar = []
    for i, h in enumerate(hedef_yollar):
        try:
            sonuc = suret_degistir(kullanici_yol, h, oran=oran, mod=mod)
            yol = cikti_klasor / f"suret_{i+1}_{seed}.jpg"
            cv2.imwrite(str(yol), sonuc, [cv2.IMWRITE_JPEG_QUALITY, 95])
            sonuclar.append({"gorsel_yol": str(yol), "hedef": str(h),
                             "meta": {"oran": oran, "mod": mod, "seed": seed}})
        except Exception as e:
            sonuclar.append({"hedef": str(h), "hata": str(e)})
    return sonuclar


def kanon_suretler(kullanici_yol, persona, cikti_klasor, sayi=8, seed=None,
                   oran_aralik=(0.45, 0.85)):
    """Kullanıcının yüzünü, persona'nın görünümüne harmanlayarak farklı
    ama gerçekçi suretler üretir (ana 'kendi yüzünden' yöntemi).

    Hedef kimlikler Pollinations ile üretilir (kişi başı ~2-4 farklı hedef),
    sonra her hedefe farklı bir harmanlama oranı uygulanır. Sonuç: AI ile
    yapılmış olduğu belli olmayan, gerçekten farklı kişiler.
    """
    from core import uretim  # Pollinations hedef üretimi

    cikti_klasor = Path(cikti_klasor)
    cikti_klasor.mkdir(parents=True, exist_ok=True)
    if seed is None:
        seed = random.randint(1, 2**31 - 1)

    anchor = (persona or {}).get("anchor_prompt", "") if isinstance(persona, dict) else ""
    if not anchor:
        anchor = ("photorealistic portrait of a young woman, natural skin, "
                  "candid expression")

    # Hedef kimlikleri üret (farklı seed'ler → farklı kişiler)
    hedef_sayi = max(2, min(4, sayi))
    hedef_yollar = []
    for t in range(hedef_sayi):
        prompt = (f"{anchor}, different distinct person, headshot, "
                  "shot on Sony A7 III, 85mm f/1.4, natural skin pores, "
                  "film grain, candid, no anime, no CGI")
        try:
            data = uretim.gorsel_uret(prompt, seed=seed + 1000 + t,
                                      genislik=768, yukseklik=1024)
            hp = cikti_klasor / f"hedef_{t+1}_{seed}.jpg"
            hp.write_bytes(data)
            hedef_yollar.append(str(hp))
        except Exception:
            continue
    if not hedef_yollar:
        raise RuntimeError("Hedef kimlik üretilemedi (Pollinations erişimi yok).")

    # Oranları dağıt (farklı derecede dönüşüm)
    oranlar = []
    for i in range(sayi):
        oranlar.append(oran_aralik[0] +
                       (oran_aralik[1] - oran_aralik[0]) * (i / max(1, sayi - 1)))

    sonuclar = []
    for i in range(sayi):
        hedef = hedef_yollar[i % len(hedef_yollar)]
        oran = round(oranlar[i], 3)
        try:
            sonuc = suret_degistir(kullanici_yol, hedef, oran=oran, mod="kullanici")
            yol = cikti_klasor / f"suret_{i+1}_{seed}.jpg"
            cv2.imwrite(str(yol), sonuc, [cv2.IMWRITE_JPEG_QUALITY, 95])
            sonuclar.append({"gorsel_yol": str(yol),
                             "meta": {"oran": oran, "hedef": hedef,
                                      "mod": "kullanici", "seed": seed + i}})
        except Exception as e:
            sonuclar.append({"hata": str(e), "meta": {"oran": oran}})
    return [s for s in sonuclar if "gorsel_yol" in s]
